# src/scraper_refactored.py

"""
Refactored scraper with clean separation of concerns.
Uses business logic and UI automation layers.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright._impl._errors import TargetClosedError
from src.error_handler import retry_with_backoff, ErrorContext, RetryableError, FatalError
from src.business_logic import (
    PersonalInfoManager, JobDataProcessor, ResumeDataBuilder, 
    ApplicationManager, LLMResponseProcessor
)
from src.ui_automation import (
    LinkedInLoginHandler, JobSearchHandler, JobDetailHandler, EasyApplyHandler
)
from src.resume_builder import build_resume
from src.llm_summary import generate_resume_summary
import src.config as config
from src.config import MAX_JOBS
from typing import Optional, List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class JobScrapingOrchestrator:
    """Orchestrates the entire job scraping and application process."""
    
    def __init__(self, personal_info_path: str = "personal_info.yaml"):
        # Initialize business logic components
        self.personal_info_manager = PersonalInfoManager(personal_info_path)
        self.job_processor = JobDataProcessor()
        self.resume_builder = ResumeDataBuilder(self.personal_info_manager)
        self.application_manager = ApplicationManager()
        self.llm_processor = LLMResponseProcessor()
        
        # UI automation components will be initialized per session
        self.login_handler = None
        self.search_handler = None
        self.job_detail_handler = None
        self.easy_apply_handler = None
    
    def initialize_ui_handlers(self, page):
        """Initialize UI automation handlers for a page."""
        self.login_handler = LinkedInLoginHandler(page)
        self.search_handler = JobSearchHandler(page)
        self.job_detail_handler = JobDetailHandler(page)
        self.easy_apply_handler = EasyApplyHandler(page)
    
    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def scrape_jobs_from_search(
        self,
        search_url: str,
        email: str,
        password: str,
        max_jobs: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Main orchestration method for job scraping and application.
        
        Args:
            search_url: LinkedIn job search URL
            email: LinkedIn login email
            password: LinkedIn login password
            max_jobs: Maximum number of jobs to process
            
        Returns:
            List of processed job data dictionaries
        """
        if max_jobs is None:
            max_jobs = MAX_JOBS
        
        with ErrorContext("Job scraping orchestration") as context:
            context.add_context("search_url", search_url)
            context.add_context("max_jobs", max_jobs)
            
            try:
                # Start Playwright session
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=not config.DEBUG)
                    context_browser = browser.new_context()
                    page = context_browser.new_page()
                    
                    # Initialize UI handlers
                    self.initialize_ui_handlers(page)
                    
                    # Execute the main workflow
                    jobs_data = self._execute_workflow(
                        page, search_url, email, password, max_jobs
                    )
                    
                    context.add_context("jobs_processed", len(jobs_data))
                    context.add_context("success", True)
                    return jobs_data
                    
            except Exception as e:
                context.add_context("error", str(e))
                raise e
    
    def _execute_workflow(
        self, 
        page, 
        search_url: str, 
        email: str, 
        password: str, 
        max_jobs: int
    ) -> List[Dict[str, Any]]:
        """Execute the main job scraping workflow."""
        
        # Step 1: Login to LinkedIn
        print("[INFO] Starting LinkedIn login...")
        if not self.login_handler.login(email, password):
            print("[ERROR] ❌ Login failed")
            return []
        
        # Step 2: Navigate to job search
        print(f"[INFO] Navigating to job search: {search_url}")
        if not self.search_handler.navigate_to_search(search_url):
            print("[ERROR] ❌ Failed to navigate to job search")
            return []
        
        # Step 3: Collect job links
        print("[INFO] Collecting job links...")
        job_links = self.search_handler.collect_job_links(max_jobs)
        if not job_links:
            print("[WARN] No job links found")
            return []
        
        print(f"[INFO] Found {len(job_links)} job links")
        
        # Step 4: Process each job
        jobs_data = []
        for idx, job_url in enumerate(job_links, start=1):
            print(f"\n[INFO] [{idx}/{len(job_links)}] Processing job: {job_url}")
            
            try:
                job_data = self._process_single_job(page, job_url, idx)
                if job_data:
                    jobs_data.append(job_data)
            except Exception as e:
                logger.error(f"Failed to process job {idx}: {e}")
                continue
        
        return jobs_data
    
    def _process_single_job(self, page, job_url: str, job_index: int) -> Optional[Dict[str, Any]]:
        """Process a single job through the complete pipeline."""
        
        with ErrorContext(f"Processing job {job_index}", page) as context:
            context.add_context("job_url", job_url)
            context.add_context("job_index", job_index)
            
            try:
                # Open job page
                job_page = page.context.new_page()
                job_page.goto(job_url, timeout=config.TIMEOUTS["job_page"])
                
                # Extract job details
                job_details = self.job_detail_handler.extract_job_details()
                context.add_context("job_title", job_details.get("title", "Unknown"))
                context.add_context("company", job_details.get("company", "Unknown"))
                
                # Process job data
                processed_job = self.job_processor.process_job_data(job_details)
                
                # Generate LLM summary
                llm_response = self._generate_llm_summary(processed_job)
                
                # Build resume data
                resume_data = self.resume_builder.build_resume_data(processed_job, llm_response)
                
                # Generate PDF resume
                pdf_path = self._generate_resume_pdf(resume_data)
                if not pdf_path:
                    raise FatalError("Failed to generate resume PDF")
                
                # Handle Easy Apply if enabled
                apply_status = "skipped"
                if config.AUTO_APPLY:
                    apply_status = self._handle_easy_apply(job_page, pdf_path, job_url)
                
                # Build final job data
                final_job_data = {
                    **resume_data,
                    "url": job_url,
                    "pdf_path": pdf_path,
                    "apply_status": apply_status,
                    "job_index": job_index
                }
                
                context.add_context("success", True)
                return final_job_data
                
            except Exception as e:
                context.add_context("error", str(e))
                logger.error(f"Job processing failed: {e}")
                return None
            finally:
                try:
                    job_page.close()
                except:
                    pass
    
    def _generate_llm_summary(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LLM summary for job."""
        try:
            raw_summary = generate_resume_summary(
                job_data["title"],
                job_data["company"], 
                job_data["description"]
            )
            return self.llm_processor.process_llm_response(raw_summary)
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            # Return fallback summary
            return {
                "summary": f"Experienced software developer with strong technical skills in {', '.join(job_data.get('keyword_list', [])[:5])}.",
                "keywords": ", ".join(job_data.get('keyword_list', [])[:7])
            }
    
    def _generate_resume_pdf(self, resume_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF resume from data."""
        try:
            return build_resume(resume_data)
        except Exception as e:
            logger.error(f"Resume PDF generation failed: {e}")
            return None
    
    def _handle_easy_apply(self, job_page, pdf_path: str, job_url: str) -> str:
        """Handle Easy Apply automation."""
        try:
            if self.easy_apply_handler.start_easy_apply():
                success = self.easy_apply_handler.process_easy_apply_modal(
                    pdf_path, self.personal_info_manager
                )
                if success:
                    self.application_manager.remove_applied_job(job_url)
                    return "applied"
                else:
                    return "failed"
            else:
                return "skipped"
        except Exception as e:
            logger.error(f"Easy Apply failed: {e}")
            return "failed"

# Convenience function for backward compatibility
@retry_with_backoff(max_attempts=3, base_delay=2.0)
def scrape_jobs_from_search(
    search_url: str,
    email: str,
    password: str,
    max_jobs: Optional[int] = None,
    personal_info_path: str = "personal_info.yaml"
) -> List[Dict[str, Any]]:
    """
    Convenience function for backward compatibility.
    Creates orchestrator and runs job scraping.
    """
    orchestrator = JobScrapingOrchestrator(personal_info_path)
    return orchestrator.scrape_jobs_from_search(search_url, email, password, max_jobs)

# Export main classes and functions
__all__ = [
    'JobScrapingOrchestrator',
    'scrape_jobs_from_search'
]



