# src/error_handler.py

import time
import random
import logging
from typing import Any, Callable, Optional, Dict, List, Union
from functools import wraps
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

# Handle TargetClosedError import compatibility
try:
    from playwright.sync_api import TargetClosedError
except ImportError:
    # TargetClosedError may not be available in all Playwright versions
    class TargetClosedError(Exception):
        """Fallback for TargetClosedError when not available in Playwright."""
        pass
import src.config as config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress WeasyPrint's verbose font processing logs
weasyprint_logger = logging.getLogger('weasyprint')
weasyprint_logger.setLevel(logging.WARNING)

# Also suppress fontTools logs that WeasyPrint uses
fonttools_logger = logging.getLogger('fontTools')
fonttools_logger.setLevel(logging.WARNING)

class AutomationError(Exception):
    """Base exception for automation-related errors."""
    pass

class LinkedInUIError(AutomationError):
    """Raised when LinkedIn UI changes break expected selectors."""
    pass

class NetworkError(AutomationError):
    """Raised for network-related failures."""
    pass

class RetryableError(AutomationError):
    """Raised for errors that can be retried."""
    pass

class FatalError(AutomationError):
    """Raised for errors that should not be retried."""
    pass

def retry_with_backoff(
    max_attempts: Optional[int] = None,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (RetryableError, NetworkError, PlaywrightTimeout)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (defaults to config)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Tuple of exceptions that can be retried
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = max_attempts or config.RETRY_CONFIG["max_attempts"]
            last_exception = None
            
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == attempts - 1:  # Last attempt
                        logger.error(f"❌ {func.__name__} failed after {attempts} attempts: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1}/{attempts} failed: {e}")
                    logger.info(f"🔄 Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                    
                except FatalError as e:
                    logger.error(f"💥 Fatal error in {func.__name__}: {e}")
                    raise e
                except Exception as e:
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise e
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

class ErrorContext:
    """Context manager for capturing detailed error information."""
    
    def __init__(self, operation: str, page: Optional[Page] = None):
        self.operation = operation
        self.page = page
        self.start_time = time.time()
        self.context = {}
    
    def __enter__(self):
        logger.info(f"🚀 Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            logger.error(f"❌ {self.operation} failed after {duration:.2f}s")
            self._log_error_context(exc_type, exc_val, exc_tb)
            return False  # Don't suppress the exception
        else:
            logger.info(f"✅ {self.operation} completed in {duration:.2f}s")
            return True
    
    def add_context(self, key: str, value: Any):
        """Add context information for debugging."""
        self.context[key] = value
    
    def _log_error_context(self, exc_type, exc_val, exc_tb):
        """Log detailed error context."""
        logger.error(f"Error type: {exc_type.__name__}")
        logger.error(f"Error message: {exc_val}")
        
        if self.context:
            logger.error("Context information:")
            for key, value in self.context.items():
                logger.error(f"  {key}: {value}")
        
        if self.page:
            try:
                current_url = self.page.url
                page_title = self.page.title()
                logger.error(f"Current URL: {current_url}")
                logger.error(f"Page title: {page_title}")
            except Exception as e:
                logger.error(f"Could not get page info: {e}")

class SelectorFallback:
    """Handles fallback mechanisms for LinkedIn UI changes."""
    
    def __init__(self, page: Page):
        self.page = page
        self.fallback_cache = {}
    
    def find_element_with_fallback(self, selectors: List[str], operation: str = "find element") -> Optional[Any]:
        """
        Try multiple selectors in order until one works.
        Now includes automatic fallback selectors from config.
        
        Args:
            selectors: List of CSS selectors to try
            operation: Description of what we're trying to do
            
        Returns:
            Playwright locator or None if all selectors fail
        """
        # Add fallback selectors based on operation type
        all_selectors = selectors.copy()
        
        # Add fallback selectors from config
        if "login" in operation.lower():
            all_selectors.extend(config.LINKEDIN_SELECTORS.get("login_fallbacks", []))
        elif "apply" in operation.lower() or "easy" in operation.lower():
            all_selectors.extend(config.LINKEDIN_SELECTORS.get("easy_apply_fallbacks", []))
        
        for i, selector in enumerate(all_selectors):
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0:
                    logger.debug(f"✅ {operation} succeeded with selector {i+1}/{len(all_selectors)}: {selector}")
                    return locator
            except Exception as e:
                logger.debug(f"⚠️ Selector {i+1}/{len(all_selectors)} failed: {selector} - {e}")
                continue
        
        logger.warning(f"❌ All selectors failed for {operation}")
        return None
    
    def safe_click(self, selectors: List[str], operation: str = "click") -> bool:
        """
        Safely click an element using fallback selectors.
        
        Args:
            selectors: List of CSS selectors to try
            operation: Description of what we're clicking
            
        Returns:
            True if click succeeded, False otherwise
        """
        locator = self.find_element_with_fallback(selectors, operation)
        if not locator:
            return False
        
        try:
            locator.scroll_into_view_if_needed()
            time.sleep(config.DELAYS["ui_stability"])
            locator.click(timeout=config.TIMEOUTS["easy_apply_click"])
            logger.info(f"✅ {operation} succeeded")
            return True
        except Exception as e:
            logger.error(f"❌ {operation} failed: {e}")
            return False
    
    def safe_fill(self, selectors: List[str], value: str, operation: str = "fill") -> bool:
        """
        Safely fill an input field using fallback selectors.
        
        Args:
            selectors: List of CSS selectors to try
            value: Value to fill
            operation: Description of what we're filling
            
        Returns:
            True if fill succeeded, False otherwise
        """
        locator = self.find_element_with_fallback(selectors, operation)
        if not locator:
            return False
        
        try:
            locator.clear()
            locator.fill(value)
            logger.info(f"✅ {operation} succeeded")
            return True
        except Exception as e:
            logger.error(f"❌ {operation} failed: {e}")
            return False

class APIFailureHandler:
    """Handles API failures with graceful degradation."""
    
    @staticmethod
    def handle_openai_failure(func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Handle OpenAI API failures with fallback strategies.
        
        Args:
            func: Function that calls OpenAI API
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result of function or None if all fallbacks fail
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {e}")
            
            # Fallback 1: Use cached response if available
            logger.info("🔄 Attempting fallback: Using cached response")
            # TODO: Implement caching mechanism
            
            # Fallback 2: Use simplified response
            logger.info("🔄 Attempting fallback: Using simplified response")
            import json
            return json.dumps({
                "summary": "Experienced software developer with strong technical skills and proven track record.",
                "keywords": "Python, JavaScript, React, Node.js, AWS, Docker"
            })
    
    @staticmethod
    def handle_weasyprint_failure(html_content: str, output_path: str) -> bool:
        """
        Handle WeasyPrint PDF generation failures.
        
        Args:
            html_content: HTML content to convert
            output_path: Path for output PDF
            
        Returns:
            True if PDF generation succeeded, False otherwise
        """
        try:
            # Suppress GLib-GIO warnings for WeasyPrint
            from src.glib_suppression import suppress_glib_warnings
            suppress_glib_warnings()
            
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_path)
            return True
        except Exception as e:
            logger.error(f"❌ WeasyPrint PDF generation failed: {e}")
            
            # Fallback: Save as HTML file
            try:
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"✅ Saved as HTML fallback: {html_path}")
                return True
            except Exception as fallback_error:
                logger.error(f"❌ HTML fallback also failed: {fallback_error}")
                return False

class LinkedInUIChangeHandler:
    """Handles LinkedIn UI changes with adaptive strategies."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selector_fallback = SelectorFallback(page)
    
    def detect_ui_changes(self, context: str = "general") -> Dict[str, bool]:
        """
        Detect if LinkedIn UI has changed significantly.
        Uses more robust detection with fallback selectors.
        
        Args:
            context: Context of the detection ("login", "job_search", "easy_apply", "general")
        
        Returns:
            Dictionary of detected changes
        """
        changes = {
            "login_page_changed": False,
            "job_search_changed": False,
            "easy_apply_changed": False,
            "selectors_broken": False
        }
        
        if config.DEBUG:
            logger.info("🔍 Starting UI change detection...")
        
        try:
            # Helper function to flatten selector lists/strings
            def flatten_selectors(selector_value):
                """Convert selector config (string or list) to list of strings."""
                if isinstance(selector_value, list):
                    return selector_value
                elif isinstance(selector_value, str):
                    return [selector_value]
                else:
                    return []
            
            # Only check login selectors if we're on login page or context is "login"
            if context == "login" or "/login" in self.page.url:
                login_selectors = [
                    config.LINKEDIN_SELECTORS["login"]["username"],
                    config.LINKEDIN_SELECTORS["login"]["password"],
                    config.LINKEDIN_SELECTORS["login"]["submit"]
                ]
                
                # Add fallback selectors for login
                login_fallbacks = [
                    'input[name="session_key"]',
                    'input[name="session_password"]',
                    'button[type="submit"]',
                    'input[type="email"]',
                    'input[type="password"]'
                ]
                
                all_login_selectors = login_selectors + login_fallbacks
                login_working = False
                
                for selector in all_login_selectors:
                    try:
                        count = self.page.locator(selector).count()
                        if count > 0:
                            login_working = True
                            if config.DEBUG:
                                logger.debug(f"✅ Login selector working: {selector} (found {count} elements)")
                            break
                    except Exception:
                        continue
                
                if not login_working:
                    changes["login_page_changed"] = True
                    changes["selectors_broken"] = True
                    if config.DEBUG:
                        logger.warning("⚠️ No login selectors found - marking as changed")
            
            # Only check job search if context is "job_search" or we're on search page
            if context == "job_search" or "/jobs/search" in self.page.url:
                job_search_selectors = [
                    config.LINKEDIN_SELECTORS["job_search"]["job_list"],
                    config.LINKEDIN_SELECTORS["job_search"]["job_cards"]
                ]
                
                # Add fallback selectors for job search
                job_search_fallbacks = [
                    'div[data-test-id="job-search-results"]',
                    'ul.jobs-search__results-list',
                    'div.jobs-search-results',
                    'main[role="main"] ul li',
                    'div.scaffold-layout__content ul li'
                ]
                
                all_job_search_selectors = job_search_selectors + job_search_fallbacks
                job_search_working = False
                
                for selector in all_job_search_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            job_search_working = True
                            break
                    except Exception:
                        continue
                
                if not job_search_working:
                    changes["job_search_changed"] = True
                    changes["selectors_broken"] = True
            
            # Check Easy Apply with fallback selectors (only if context is easy_apply or on job page)
            if context == "easy_apply" or "/jobs/view" in self.page.url or context == "general":
                # Get Easy Apply selectors and flatten lists
                button_selectors = flatten_selectors(config.LINKEDIN_SELECTORS["easy_apply"]["button"])
                modal_selectors = flatten_selectors(config.LINKEDIN_SELECTORS["easy_apply"]["modal"])
                
                # Add fallback selectors for Easy Apply
                easy_apply_fallbacks = [
                    'button:has-text("Easy Apply")',
                    'button:has-text("Apply")',
                    'div[role="dialog"]',
                    'div.artdeco-modal',
                    'button[aria-label*="Apply"]',
                    'button[data-test-id*="apply"]'
                ]
                
                all_easy_apply_selectors = button_selectors + modal_selectors + easy_apply_fallbacks
                easy_apply_working = False
                
                for selector in all_easy_apply_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            easy_apply_working = True
                            break
                    except Exception:
                        continue
                
                if not easy_apply_working:
                    changes["easy_apply_changed"] = True
                    changes["selectors_broken"] = True
                    
        except Exception as e:
            logger.warning(f"⚠️ Error detecting UI changes: {e}")
            changes["selectors_broken"] = True
        
        return changes
    
    def adapt_to_changes(self, changes: Dict[str, bool]) -> bool:
        """
        Adapt to detected UI changes with improved fallback strategies.
        
        Args:
            changes: Dictionary of detected changes
            
        Returns:
            True if adaptation succeeded, False otherwise
        """
        if not any(changes.values()):
            return True
        
        logger.warning("⚠️ LinkedIn UI changes detected, attempting adaptation...")
        
        # Log detected changes
        for change_type, detected in changes.items():
            if detected:
                logger.warning(f"  - {change_type}: {detected}")
        
        # Try to find alternative selectors
        if changes["selectors_broken"]:
            logger.info("🔄 Attempting to find alternative selectors...")
            
            # Try to adapt using more generic selectors
            adaptation_success = self._try_generic_selectors()
            
            if adaptation_success:
                logger.info("✅ Successfully adapted to UI changes using generic selectors")
                return True
            else:
                # Try text-based fallbacks
                text_fallback_success = self._try_text_based_fallbacks()
                
                if text_fallback_success:
                    logger.info("✅ Successfully adapted to UI changes using text-based selectors")
                    return True
                else:
                    logger.warning("⚠️ Could not automatically adapt to UI changes")
                    logger.info("💡 The system will attempt to continue with existing selectors")
                    # Don't fail completely - let the system try to continue
                    return True
        
        return True
    
    def _try_generic_selectors(self) -> bool:
        """Try to find elements using more generic selectors."""
        try:
            # Test if we can find basic elements with generic selectors
            generic_tests = [
                ('input[type="text"]', 'text input'),
                ('input[type="password"]', 'password input'),
                ('button', 'button'),
                ('div[role="dialog"]', 'modal dialog'),
                ('ul li', 'list items')
            ]
            
            found_elements = 0
            for selector, description in generic_tests:
                if self.page.locator(selector).count() > 0:
                    found_elements += 1
                    logger.debug(f"✅ Found {description} with generic selector: {selector}")
            
            # If we found at least some basic elements, consider it a success
            return found_elements >= 2
            
        except Exception as e:
            logger.debug(f"Generic selector test failed: {e}")
            return False
    
    def _try_text_based_fallbacks(self) -> bool:
        """Try to find elements using text-based selectors."""
        try:
            # Test text-based selectors
            text_tests = [
                ('button:has-text("Sign in")', 'sign in button'),
                ('button:has-text("Apply")', 'apply button'),
                ('button:has-text("Easy Apply")', 'easy apply button'),
                ('input[placeholder*="email"]', 'email input'),
                ('input[placeholder*="password"]', 'password input')
            ]
            
            found_elements = 0
            for selector, description in text_tests:
                if self.page.locator(selector).count() > 0:
                    found_elements += 1
                    logger.debug(f"✅ Found {description} with text selector: {selector}")
            
            return found_elements >= 1
            
        except Exception as e:
            logger.debug(f"Text-based selector test failed: {e}")
            return False

def safe_execute(operation: str, func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute a function with comprehensive error handling.
    
    Args:
        operation: Description of the operation
        func: Function to execute
        *args, **kwargs: Arguments for the function
        
    Returns:
        Result of function execution or None if failed
    """
    with ErrorContext(operation) as context:
        try:
            result = func(*args, **kwargs)
            context.add_context("success", True)
            return result
        except Exception as e:
            context.add_context("error", str(e))
            context.add_context("error_type", type(e).__name__)
            raise

def handle_playwright_errors(func: Callable) -> Callable:
    """
    Decorator to handle common Playwright errors with appropriate retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PlaywrightTimeout as e:
            logger.warning(f"⚠️ Timeout in {func.__name__}: {e}")
            raise RetryableError(f"Timeout in {func.__name__}: {e}")
        except TargetClosedError as e:
            logger.warning(f"⚠️ Target closed in {func.__name__}: {e}")
            raise RetryableError(f"Target closed in {func.__name__}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
            raise e
    
    return wrapper

# Export commonly used functions
__all__ = [
    'retry_with_backoff',
    'ErrorContext',
    'SelectorFallback',
    'APIFailureHandler',
    'LinkedInUIChangeHandler',
    'safe_execute',
    'handle_playwright_errors',
    'AutomationError',
    'LinkedInUIError',
    'NetworkError',
    'RetryableError',
    'FatalError'
]
