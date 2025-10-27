# src/business_logic.py

"""
Business logic layer for resume generation automation.
Separates business logic from UI automation concerns.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.shared_utils import FileHandler, DataValidator, TextProcessor, DataMerger
from src.error_handler import ErrorContext, RetryableError, FatalError
import src.config as config

logger = logging.getLogger(__name__)

class PersonalInfoManager:
    """Manages personal information data and operations."""
    
    def __init__(self, personal_info_path: str = "personal_info.yaml"):
        self.personal_info_path = personal_info_path
        self._data = None
    
    def load_personal_info(self) -> Dict[str, Any]:
        """
        Load personal information from YAML file.
        
        Returns:
            Personal information dictionary
            
        Raises:
            FatalError: If personal info cannot be loaded or is invalid
        """
        with ErrorContext("Loading personal information") as context:
            try:
                self._data = FileHandler.load_yaml(self.personal_info_path)
                context.add_context("file_path", self.personal_info_path)
                
                # Validate the data
                validation_errors = DataValidator.validate_personal_info(self._data)
                if validation_errors:
                    error_msg = f"Personal info validation failed: {'; '.join(validation_errors)}"
                    context.add_context("validation_errors", validation_errors)
                    raise FatalError(error_msg)
                
                context.add_context("success", True)
                return self._data
                
            except Exception as e:
                context.add_context("error", str(e))
                raise FatalError(f"Failed to load personal information: {e}")
    
    def get_personal_info(self) -> Dict[str, Any]:
        """Get cached personal information or load if not available."""
        if self._data is None:
            self._data = self.load_personal_info()
        return self._data
    
    def save_answer_to_yaml(self, question: str, answer: str) -> bool:
        """
        Save question-answer pair to personal info YAML.
        
        Args:
            question: Question text
            answer: Answer text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = self.get_personal_info()
            
            if "questions" not in data:
                data["questions"] = {}
            
            data["questions"][question] = answer
            
            return FileHandler.save_yaml(data, self.personal_info_path)
            
        except Exception as e:
            logger.error(f"Error saving answer to YAML: {e}")
            return False

class JobDataProcessor:
    """Processes job data and extracts relevant information."""
    
    def __init__(self):
        self.keyword_extractor = None
        self.keyword_weighter = None
    
    def process_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process job data to extract keywords and prepare for resume generation.
        
        Args:
            job_data: Raw job data dictionary
            
        Returns:
            Processed job data with extracted information
        """
        with ErrorContext("Processing job data") as context:
            context.add_context("job_title", job_data.get("title", "Unknown"))
            context.add_context("company", job_data.get("company", "Unknown"))
            
            try:
                # Validate job data
                validation_errors = DataValidator.validate_job_data(job_data)
                if validation_errors:
                    raise FatalError(f"Job data validation failed: {'; '.join(validation_errors)}")
                
                # Extract keywords
                from src.keyword_extractor import extract_keywords
                from src.keyword_weighting import weigh_keywords
                
                description = job_data.get("description", "")
                keywords = extract_keywords(description)
                weighted_keywords = weigh_keywords(description, keywords)
                
                # Prepare processed data
                processed_data = job_data.copy()
                processed_data.update({
                    "extracted_keywords": keywords,
                    "weighted_keywords": weighted_keywords,
                    "keyword_list": [kw for kw, _ in weighted_keywords]
                })
                
                context.add_context("keywords_extracted", len(keywords))
                context.add_context("success", True)
                return processed_data
                
            except Exception as e:
                context.add_context("error", str(e))
                raise FatalError(f"Job data processing failed: {e}")

class ResumeDataBuilder:
    """Builds resume data structures for PDF generation."""
    
    def __init__(self, personal_info_manager: PersonalInfoManager):
        self.personal_info_manager = personal_info_manager
    
    def build_resume_data(self, job_data: Dict[str, Any], llm_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete resume data structure for PDF generation.
        
        Args:
            job_data: Processed job data
            llm_summary: LLM-generated summary and keywords
            
        Returns:
            Complete resume data dictionary
        """
        with ErrorContext("Building resume data") as context:
            context.add_context("job_title", job_data.get("title", "Unknown"))
            context.add_context("company", job_data.get("company", "Unknown"))
            
            try:
                personal_info = self.personal_info_manager.get_personal_info()
                
                # Build base resume data
                resume_data = {
                    "name": f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}",
                    "email": personal_info.get("email", ""),
                    "phone": personal_info.get("phone", ""),
                    "linkedin": personal_info.get("linkedin", ""),
                    "github": personal_info.get("github", ""),
                    "address": personal_info.get("address", ""),
                    "summary": llm_summary.get("summary", ""),
                    "skills": llm_summary.get("keywords", "").split(", ") if llm_summary.get("keywords") else [],
                    "experiences": self._build_experiences(personal_info.get("job_history", [])),
                    "education": personal_info.get("education", []),
                    "references": personal_info.get("references", []),
                    "matched_keywords": job_data.get("keyword_list", []),
                    "title": job_data.get("title", "N/A"),
                    "company": job_data.get("company", "N/A"),
                    "location": job_data.get("location", "N/A"),
                    "description": job_data.get("description", "")
                }
                
                context.add_context("success", True)
                return resume_data
                
            except Exception as e:
                context.add_context("error", str(e))
                raise FatalError(f"Resume data building failed: {e}")
    
    def _build_experiences(self, job_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build experiences list from job history.
        
        Args:
            job_history: List of job history entries
            
        Returns:
            Formatted experiences list
        """
        experiences = []
        
        for job in job_history:
            experience = {
                "role": job.get("title", ""),
                "company": job.get("company", ""),
                "years": self._calculate_years(job.get("start_date", ""), job.get("end_date", "")),
                "responsibilities": job.get("responsibilities", [])
            }
            experiences.append(experience)
        
        return experiences
    
    def _calculate_years(self, start_date: str, end_date: str) -> str:
        """Calculate years of experience from date strings."""
        # Simple implementation - could be enhanced with proper date parsing
        if end_date and end_date.lower() != "present":
            return f"{start_date} - {end_date}"
        else:
            return f"{start_date} - Present"

class ApplicationManager:
    """Manages job application data and tracking."""
    
    def __init__(self, job_urls_path: str = "job_urls.json"):
        self.job_urls_path = job_urls_path
    
    def load_existing_job_links(self) -> List[str]:
        """Load existing job links from JSON file."""
        return FileHandler.load_json(self.job_urls_path)
    
    def save_job_links(self, job_links: List[str]) -> bool:
        """Save job links to JSON file."""
        return FileHandler.save_json(job_links, self.job_urls_path)
    
    def remove_applied_job(self, job_url: str) -> bool:
        """
        Remove a job URL from the job URLs list after application.
        
        Args:
            job_url: URL of the job to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job_links = self.load_existing_job_links()
            if job_url in job_links:
                job_links.remove(job_url)
                return self.save_job_links(job_links)
            return True
        except Exception as e:
            logger.error(f"Error removing applied job {job_url}: {e}")
            return False

class LLMResponseProcessor:
    """Processes and validates LLM responses."""
    
    @staticmethod
    def process_llm_response(raw_response: str) -> Dict[str, Any]:
        """
        Process and validate LLM response.
        
        Args:
            raw_response: Raw LLM response string
            
        Returns:
            Processed response dictionary
            
        Raises:
            FatalError: If response cannot be processed
        """
        with ErrorContext("Processing LLM response") as context:
            try:
                # Clean the response
                cleaned_response = TextProcessor.clean_text(raw_response)
                
                # Parse JSON
                try:
                    parsed_response = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    raise FatalError(f"LLM returned invalid JSON: {e}")
                
                # Validate required fields
                required_fields = ["summary", "keywords"]
                for field in required_fields:
                    if field not in parsed_response:
                        raise FatalError(f"LLM response missing required field: {field}")
                
                context.add_context("success", True)
                return parsed_response
                
            except Exception as e:
                context.add_context("error", str(e))
                raise FatalError(f"LLM response processing failed: {e}")

# Export main classes
__all__ = [
    'PersonalInfoManager',
    'JobDataProcessor', 
    'ResumeDataBuilder',
    'ApplicationManager',
    'LLMResponseProcessor'
]



