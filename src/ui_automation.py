# src/ui_automation.py

"""
UI automation layer for LinkedIn interactions.
Separates UI automation concerns from business logic.
"""

import time
import random
import logging
from typing import List, Optional, Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, TargetClosedError

from src.error_handler import (
    ErrorContext, SelectorFallback, LinkedInUIChangeHandler,
    RetryableError, FatalError, LinkedInUIError
)
from src.shared_utils import DelayManager, TextProcessor
import src.config as config

logger = logging.getLogger(__name__)

class LinkedInLoginHandler:
    """Handles LinkedIn login automation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selector_fallback = SelectorFallback(page)
        self.ui_handler = LinkedInUIChangeHandler(page)
    
    def login(self, email: str, password: str) -> bool:
        """
        Perform LinkedIn login with error handling.
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            
        Returns:
            True if login successful, False otherwise
        """
        with ErrorContext("LinkedIn login", self.page) as context:
            context.add_context("email", email)
            
            try:
                # Navigate to login page
                self.page.goto("https://www.linkedin.com/login", timeout=config.TIMEOUTS["login"])
                
                # Check for UI changes (with login context)
                ui_changes = self.ui_handler.detect_ui_changes(context="login")
                if ui_changes["login_page_changed"]:
                    logger.warning("⚠️ LinkedIn login page UI changes detected")
                    if not self.ui_handler.adapt_to_changes(ui_changes):
                        raise LinkedInUIError("LinkedIn login page UI has changed and cannot be adapted")
                
                # Fill credentials
                username_success = self.selector_fallback.safe_fill(
                    [config.LINKEDIN_SELECTORS["login"]["username"]], 
                    email, 
                    "username input"
                )
                if not username_success:
                    raise LinkedInUIError("Could not find username input field")
                
                password_success = self.selector_fallback.safe_fill(
                    [config.LINKEDIN_SELECTORS["login"]["password"]], 
                    password, 
                    "password input"
                )
                if not password_success:
                    raise LinkedInUIError("Could not find password input field")
                
                # Submit login
                submit_success = self.selector_fallback.safe_click(
                    [config.LINKEDIN_SELECTORS["login"]["submit"]], 
                    "login submit"
                )
                if not submit_success:
                    raise LinkedInUIError("Could not find or click login submit button")
                
                # Wait for login processing
                DelayManager.human_like_delay(2.0, 4.0)
                
                # Verify login success
                return self._verify_login_success()
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e
    
    def _verify_login_success(self) -> bool:
        """Verify that login was successful."""
        try:
            # Check URL redirect
            current_url = self.page.url
            if "/login" not in current_url and ("linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url):
                logger.info("✅ Login successful (URL redirect detected)")
                return True
            
            # Check page title
            page_title = self.page.title()
            if "Feed" in page_title or "LinkedIn" in page_title and "Sign In" not in page_title:
                logger.info("✅ Login successful (page title indicates success)")
                return True
            
            # Check for success selectors
            login_success_selectors = config.LINKEDIN_SELECTORS["login_success"]
            for selector in login_success_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=config.TIMEOUTS["login_success"])
                    logger.info(f"✅ Login successful (detected via: {selector})")
                    return True
                except PlaywrightTimeout:
                    continue
            
            # Check for error conditions
            error_indicators = {
                'captcha': 'div.challenge',
                'invalid_credentials': '[data-test-id="sign-in-error"]',
                'form_error': '.form__input--error'
            }
            
            for error_type, selector in error_indicators.items():
                if self.page.locator(selector).count() > 0:
                    error_messages = {
                        'captcha': "Login blocked by security challenge/CAPTCHA",
                        'invalid_credentials': "Invalid credentials",
                        'form_error': "Login form error detected"
                    }
                    logger.error(f"❌ {error_messages[error_type]}")
                    raise FatalError(f"Login failed: {error_type}")
            
            if "/login" in self.page.url:
                raise FatalError("Login failed: Still on login page")
            else:
                raise RetryableError("Login detection failed - may be temporary")
                
        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            raise e

class JobSearchHandler:
    """Handles job search page automation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selector_fallback = SelectorFallback(page)
        self.ui_handler = LinkedInUIChangeHandler(page)
    
    def navigate_to_search(self, search_url: str) -> bool:
        """
        Navigate to job search page.
        
        Args:
            search_url: LinkedIn job search URL
            
        Returns:
            True if navigation successful, False otherwise
        """
        with ErrorContext("Navigating to job search", self.page) as context:
            context.add_context("search_url", search_url)
            
            try:
                self.page.goto(search_url, timeout=config.TIMEOUTS["search_page"])
                
                # Check for UI changes (with job_search context)
                ui_changes = self.ui_handler.detect_ui_changes(context="job_search")
                if ui_changes["job_search_changed"]:
                    logger.warning("⚠️ LinkedIn job search page UI changes detected")
                    if not self.ui_handler.adapt_to_changes(ui_changes):
                        raise LinkedInUIError("LinkedIn job search page UI has changed and cannot be adapted")
                
                context.add_context("success", True)
                return True
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e
    
    def collect_job_links(self, max_jobs: Optional[int] = None) -> List[str]:
        """
        Collect job links from search results.
        
        Args:
            max_jobs: Maximum number of jobs to collect
            
        Returns:
            List of job URLs
        """
        with ErrorContext("Collecting job links", self.page) as context:
            context.add_context("max_jobs", max_jobs)
            
            try:
                from src.utils import collect_job_links_with_pagination
                
                job_links = collect_job_links_with_pagination(
                    self.page, 
                    self.page.url, 
                    max_jobs=max_jobs
                )
                
                context.add_context("links_collected", len(job_links))
                context.add_context("success", True)
                return job_links
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e

class JobDetailHandler:
    """Handles individual job page automation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selector_fallback = SelectorFallback(page)
    
    def extract_job_details(self) -> Dict[str, Any]:
        """
        Extract job details from current page.
        
        Returns:
            Dictionary containing job details
        """
        with ErrorContext("Extracting job details", self.page) as context:
            try:
                # Check if job is available
                if self.page.locator(config.LINKEDIN_SELECTORS["job_detail"]["unavailable"]).count():
                    raise FatalError("Job is unavailable or expired")
                
                # Extract job information
                job_data = {
                    "title": self._extract_text(config.LINKEDIN_SELECTORS["job_detail"]["title"]),
                    "company": self._extract_text(config.LINKEDIN_SELECTORS["job_detail"]["company"]),
                    "location": self._extract_text(config.LINKEDIN_SELECTORS["job_detail"]["location"]),
                    "description": self._extract_text(config.LINKEDIN_SELECTORS["job_detail"]["description"])
                }
                
                # Clean and validate data
                for key, value in job_data.items():
                    job_data[key] = TextProcessor.clean_text(value)
                
                context.add_context("job_title", job_data.get("title", "Unknown"))
                context.add_context("company", job_data.get("company", "Unknown"))
                context.add_context("success", True)
                return job_data
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e
    
    def _extract_text(self, selector: str) -> str:
        """Extract text from element using selector."""
        try:
            element = self.page.locator(selector)
            if element.count() > 0:
                return element.inner_text()
            return ""
        except Exception:
            return ""

class EasyApplyHandler:
    """Handles LinkedIn Easy Apply automation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selector_fallback = SelectorFallback(page)
        self.ui_handler = LinkedInUIChangeHandler(page)
    
    def start_easy_apply(self) -> bool:
        """
        Start the Easy Apply process.
        
        Returns:
            True if Easy Apply button found and clicked, False otherwise
        """
        with ErrorContext("Starting Easy Apply", self.page) as context:
            try:
                # Check if already applied
                if self._check_already_applied():
                    logger.info("Job already applied to")
                    return False
                
                # Check if job is still accepting applications
                if self._check_job_closed():
                    logger.info("Job no longer accepting applications")
                    return False
                
                # Click Easy Apply button
                easy_apply_success = self.selector_fallback.safe_click(
                    [config.LINKEDIN_SELECTORS["easy_apply"]["button"]], 
                    "Easy Apply button"
                )
                
                if not easy_apply_success:
                    raise LinkedInUIError("Easy Apply button not found or not clickable")
                
                # Wait for modal
                self._wait_for_modal()
                
                context.add_context("success", True)
                return True
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e
    
    def _check_already_applied(self) -> bool:
        """Check if job was already applied to."""
        applied_banner = self.page.locator(config.LINKEDIN_SELECTORS["application_status"]["applied_banner"])
        if applied_banner.count() > 0:
            text = applied_banner.inner_text().strip()
            return config.LINKEDIN_SELECTORS["application_status"]["applied_text"] in text
        return False
    
    def _check_job_closed(self) -> bool:
        """Check if job is no longer accepting applications."""
        page_text = self.page.inner_text("body").lower()
        return "no longer accepting applications" in page_text
    
    def _wait_for_modal(self) -> None:
        """Wait for Easy Apply modal to appear."""
        try:
            modal_selector = config.LINKEDIN_SELECTORS["easy_apply"]["modal"]
            self.page.wait_for_selector(modal_selector, state="visible", timeout=config.TIMEOUTS["modal_wait"])
        except Exception as e:
            raise RetryableError(f"Easy Apply modal not detected: {e}")
    
    def process_easy_apply_modal(self, resume_path: str, personal_info_manager) -> bool:
        """
        Process the Easy Apply modal steps.
        
        Args:
            resume_path: Path to resume file
            personal_info_manager: Personal info manager for answers
            
        Returns:
            True if application submitted successfully, False otherwise
        """
        with ErrorContext("Processing Easy Apply modal", self.page) as context:
            context.add_context("resume_path", resume_path)
            
            try:
                # Import the step-through function
                from src.easy_apply import step_through_easy_apply
                
                # Process the modal steps
                success = step_through_easy_apply(self.page)
                
                context.add_context("success", success)
                return success
                
            except Exception as e:
                context.add_context("error", str(e))
                raise e

# Export main classes
__all__ = [
    'LinkedInLoginHandler',
    'JobSearchHandler',
    'JobDetailHandler', 
    'EasyApplyHandler'
]



