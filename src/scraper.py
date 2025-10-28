# src/scraper.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Handle TargetClosedError import compatibility
try:
    from playwright.sync_api import TargetClosedError
except ImportError:
    # TargetClosedError may not be available in all Playwright versions
    class TargetClosedError(Exception):  # type: ignore
        """Fallback for TargetClosedError when not available in Playwright."""
        pass

import signal
import threading
import time
import random
from src.utils import clean_text, normalize_skill, collect_job_links_with_pagination
from src.keyword_extractor import extract_keywords
from src.keyword_weighting import weigh_keywords
from src.resume_builder import build_resume
from src.easy_apply import apply_to_job
from src.llm_summary import generate_resume_summary
from src.human_behavior import HumanBehavior
from src.error_handler import (
    retry_with_backoff, ErrorContext, SelectorFallback, 
    LinkedInUIChangeHandler, safe_execute, handle_playwright_errors,
    RetryableError, FatalError, LinkedInUIError
)
from src.browser_config import EnhancedBrowserConfig
from src.resource_error_handler import ResourceErrorHandler
# CookieManager removed to prevent automated behavior detection
import src.config as config
from src.config import MAX_JOBS
from typing import Optional
import yaml
import json
import time
import os
import sys
from src.logging_config import get_logger, log_function_call, log_error_context, log_job_context, log_browser_context, debug_pause, debug_stop, debug_checkpoint, debug_skip_stops

logger = get_logger(__name__)

class BrowserMonitor:
    """
    Monitors browser connection and forces program exit when browser is manually closed.
    
    This class runs a background thread that periodically checks if the browser
    is still connected. If the browser is manually closed by the user, it will
    detect this and force the program to exit gracefully.
    
    Features:
    - Monitors browser connection every 5 seconds
    - Requires 5 consecutive failures before triggering
    - Detects manual browser closure
    - Handles graceful shutdown with signal handlers
    - Only active when ENABLE_BROWSER_MONITORING=true environment variable is set
    """
    def __init__(self, browser, context):
        self.browser = browser
        self.context = context
        self.monitoring = False
        self.monitor_thread = None
        self.force_exit = False
        self._setup_signal_handlers()
        
    def start_monitoring(self):
        """Start monitoring browser connection."""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.force_exit = False
        self.monitor_thread = threading.Thread(target=self._monitor_browser, daemon=True)
        self.monitor_thread.start()
        logger.info("Browser monitoring started - program will exit if browser is manually closed")
        logger.debug("Monitoring will only trigger after 5 consecutive connection failures")
        
    def stop_monitoring(self):
        """Stop monitoring browser connection."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            
    def _monitor_browser(self):
        """Monitor browser connection in a separate thread."""
        consecutive_failures = 0
        max_failures = 5  # Only trigger after 5 consecutive failures
        check_interval = 5  # Check every 5 seconds (less frequent)
        
        # Wait a bit before starting monitoring to allow browser to fully initialize
        # This prevents false positives when the browser is still starting up
        time.sleep(15)
        
        while self.monitoring:
            try:
                # Check if browser is still connected by trying to access browser contexts
                # This is more reliable than creating new pages
                contexts = self.browser.contexts
                if contexts and len(contexts) > 0:  # If we have contexts, browser is still alive
                    consecutive_failures = 0  # Reset failure counter on success
                else:
                    # Don't count empty contexts as failure immediately - browser might still be starting
                    if consecutive_failures > 0:  # Only increment if we already had failures
                        consecutive_failures += 1
                    
                time.sleep(check_interval)
            except Exception as e:
                consecutive_failures += 1
                if self.monitoring and consecutive_failures >= max_failures:
                    logger.warning("Browser connection lost", 
                                 consecutive_failures=consecutive_failures, 
                                 error=str(e))
                    logger.info("Browser was manually closed by user - forcing program exit")
                    self.force_exit = True
                    self.monitoring = False
                    
                    # Force exit the program
                    try:
                        # Try graceful exit first
                        logger.info("Attempting graceful shutdown")
                        sys.exit(0)
                    except:
                        # Force exit if graceful doesn't work
                        os._exit(1)
                    break
                elif self.monitoring:
                    # Log the failure but don't exit yet
                    logger.debug("Browser connection check failed", 
                                 consecutive_failures=consecutive_failures, 
                                 max_failures=max_failures, 
                                 error=str(e))
                    time.sleep(2)  # Wait a bit before retrying
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                logger.info("Keyboard interrupt received - stopping monitoring")
                self.force_exit = True
                self.monitoring = False
                break
                
    def should_exit(self):
        """Check if program should exit due to browser closure."""
        return self.force_exit
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received signal - initiating graceful shutdown", signal=signum)
            self.force_exit = True
            self.monitoring = False
            
        # Handle common termination signals
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)   # Termination signal

def scrape_jobs_from_search(
    search_url: str,
    email: str,
    password: str,
    max_jobs: Optional[int] = None,
    personal_info_path: str = "personal_info.yaml"
) -> list:
    """
    Logs into LinkedIn, scrapes job listings from a search URL,
    tailors + builds a resume PDF (with personal_info.yaml fields),
    then (if enabled) runs Easy Apply on each job.
    Returns a list of job_data dicts including paths to generated PDFs.
    """
    # Debug checkpoint at function start
    debug_checkpoint("scrape_jobs_from_search_start", 
                    search_url=search_url, 
                    email=email, 
                    max_jobs=max_jobs,
                    personal_info_path=personal_info_path)
    
    # Use default max if not provided
    if max_jobs is None:
        max_jobs = MAX_JOBS

    # Start Playwright with enhanced browser configuration
    with sync_playwright() as p:
        # Use enhanced browser configuration for better reliability
        browser_config = EnhancedBrowserConfig(
            debug=config.DEBUG,
            headless=config.HEADLESS_MODE
        )
        
        # Debug stop before browser launch
        if not debug_skip_stops():
            debug_stop("About to launch browser", 
                      debug_mode=config.DEBUG,
                      headless_mode=config.HEADLESS_MODE,
                      browser_type="chromium")
        
        # Launch browser with enhanced configuration
        browser = browser_config.launch_browser(p)
        
        # Debug checkpoint after browser launch
        debug_checkpoint("browser_launched", browser_type="chromium")
        
        # Create context with stealth session management
        context = browser_config.create_context_with_stealth_session(browser)
        
        # Debug checkpoint after context creation
        debug_checkpoint("browser_context_created_with_stealth")
        
        # Get stealth session manager
        stealth_session = browser_config.stealth_session
        
        page = context.new_page()
        
        # Initialize resource error handling
        resource_handler = ResourceErrorHandler(page)
        resource_handler.setup_error_handling()
        
        # Initialize browser monitoring (disabled by default to avoid false positives)
        browser_monitor = BrowserMonitor(browser, context)
        # Only enable monitoring if explicitly requested via environment variable
        if config.ENABLE_BROWSER_MONITORING:
            browser_monitor.start_monitoring()
        
        # Initialize error handling components
        ui_handler = LinkedInUIChangeHandler(page)
        selector_fallback = SelectorFallback(page)

        # Session state restoration will be attempted after navigation
        session_restored = False
        
        # LOGIN (only if session not restored)
        if not session_restored:
            # Debug stop before login process
            if not debug_skip_stops():
                debug_stop("About to start LinkedIn login process", 
                          email=email,
                          search_url=search_url)
            
            with ErrorContext("LinkedIn login", page) as login_context:
                login_context.add_context("email", email)
                login_context.add_context("search_url", search_url)
                
                # Debug pause before login
                debug_pause("About to start LinkedIn login process", email=email)
                
                logger.info("Navigating to LinkedIn login page")
                page.goto("https://www.linkedin.com/login", timeout=config.TIMEOUTS["login"])
                
                # Debug pause after navigating to login page
                debug_pause("Successfully navigated to LinkedIn login page", 
                           current_url=page.url, 
                           page_title=page.title())
                
                # Try to restore session state now that we have a valid page
                if stealth_session and not session_restored:
                    try:
                        session_restored = stealth_session.restore_session_state(page)
                        if session_restored:
                            logger.info("Restored existing stealth session")
                        else:
                            logger.info("No existing session found, creating new stealth session")
                    except Exception as e:
                        logger.debug("Could not restore session state", error=str(e))
                        session_restored = False
                
                # Check for UI changes before proceeding (with login context)
                ui_changes = ui_handler.detect_ui_changes(context="login")
                if ui_changes["login_page_changed"]:
                    logger.warning("LinkedIn login page UI changes detected")
                    if not ui_handler.adapt_to_changes(ui_changes):
                        raise LinkedInUIError("LinkedIn login page UI has changed and cannot be adapted")
                
                # Check if we need to perform login
                if session_restored:
                    logger.info("Session restored, skipping login process")
                else:
                    logger.info("Performing stealth login with realistic behavior")
                    
                    # Use stealth session for realistic login flow
                    if stealth_session:
                        login_success = stealth_session.simulate_realistic_login_flow(page, email, password)
                        if not login_success:
                            logger.warning("Stealth login failed, falling back to standard login")
                            # Fallback to standard login
                            username_success = selector_fallback.safe_fill(
                                [config.LINKEDIN_SELECTORS["login"]["username"]], 
                                email, 
                                "username input"
                            )
                            if not username_success:
                                raise LinkedInUIError("Could not find username input field")
                            
                            password_success = selector_fallback.safe_fill(
                                [config.LINKEDIN_SELECTORS["login"]["password"]], 
                                password, 
                                "password input"
                            )
                            if not password_success:
                                raise LinkedInUIError("Could not find password input field")
                            
                            # Click login button
                            submit_success = selector_fallback.safe_click(
                                [config.LINKEDIN_SELECTORS["login"]["submit"]], 
                                "login submit"
                            )
                            if not submit_success:
                                raise LinkedInUIError("Could not find or click login submit button")
                    else:
                        # Fallback to standard login if stealth session not available
                        logger.warning("Stealth session not available, using standard login")
                        username_success = selector_fallback.safe_fill(
                            [config.LINKEDIN_SELECTORS["login"]["username"]], 
                            email, 
                            "username input"
                        )
                        if not username_success:
                            raise LinkedInUIError("Could not find username input field")
                        
                        password_success = selector_fallback.safe_fill(
                            [config.LINKEDIN_SELECTORS["login"]["password"]], 
                            password, 
                            "password input"
                        )
                        if not password_success:
                            raise LinkedInUIError("Could not find password input field")
                        
                        # Click login button
                        submit_success = selector_fallback.safe_click(
                            [config.LINKEDIN_SELECTORS["login"]["submit"]], 
                            "login submit"
                        )
                        if not submit_success:
                            raise LinkedInUIError("Could not find or click login submit button")
        
        # Check for login success using multiple methods
        login_detected = session_restored  # If we restored session, we're already logged in
        
        if not session_restored:
            try:
                # FIRST: Check for security verification page (must handle this before other login checks)
                page_title = page.title()
                current_url = page.url
                
                # Check if we're on security/checkpoint page
                if "Security Verification" in page_title or "security" in page_title.lower() or "checkpoint/challenge" in current_url:
                    logger.info("Security verification page detected")
                    
                    # Check if reCAPTCHA is broken (common with automation)
                    try:
                        # Look for reCAPTCHA errors in console logs
                        page.wait_for_timeout(3000)  # Wait 3 seconds for page to load
                        
                        # Check if we can detect broken reCAPTCHA
                        page_content = page.content()
                        if "grecaptcha.render is not a function" in page_content or "recaptcha" in page_content.lower():
                            logger.warning("reCAPTCHA appears to be broken - this is common with automated browsers")
                            logger.info("LinkedIn has detected automated behavior and is blocking the security check")
                            logger.info("Please complete the security verification manually in the browser window")
                            logger.info("Once you see the LinkedIn feed, press Enter here to continue...")
                            
                            # Wait for manual completion (with timeout for non-interactive environments)
                            try:
                                import sys
                                if sys.stdin.isatty():
                                    input("Press Enter once you've completed the security check and are logged into LinkedIn...")
                                else:
                                    logger.info("Non-interactive environment detected - waiting 30 seconds for manual completion")
                                    time.sleep(30)
                            except (EOFError, KeyboardInterrupt):
                                logger.info("Manual intervention cancelled or timed out")
                                raise RetryableError("Manual security verification cancelled")
                            
                            # Verify manual login success
                            time.sleep(2)
                            final_url = page.url
                            final_title = page.title()
                            
                            if "/feed" in final_url or "/in/" in final_url or ("LinkedIn" in final_title and "Feed" in final_title):
                                logger.info("Manual security verification completed successfully")
                                login_detected = True
                            else:
                                logger.error("Still not logged in after manual verification")
                                raise RetryableError("Manual security verification failed")
                        else:
                            # Try automatic waiting (original logic)
                            logger.info("Waiting for automatic security check to complete")
                            # Handle automatic security verification
                            try:
                                logger.info("Waiting for automatic security check to complete", timeout_seconds=30)
                                page.wait_for_url(
                                    lambda url: "checkpoint" not in url.lower(),
                                    timeout=30000  # 30 seconds timeout
                                )
                                logger.info("Security verification page redirected")
                                time.sleep(3)  # Give page time to fully load
                                
                                # Check where we were redirected to
                                final_url = page.url
                                
                                # If redirected to login, verification failed
                                if "/login" in final_url or "uas/login" in final_url:
                                    logger.error("LinkedIn redirected to login page after security verification")
                                    raise RetryableError("Security verification failed - redirected to login")
                                else:
                                    logger.info("Security verification completed successfully")
                                    login_detected = True
                            except Exception as e:
                                logger.error("Automatic security verification failed", error=str(e))
                                raise RetryableError("Security verification failed")
                            
                    except Exception as e:
                        logger.warning("Error during security verification detection", error=str(e))
                        # Fall back to manual intervention (with timeout for non-interactive environments)
                        logger.info("Security verification failed - switching to manual mode")
                        logger.info("Please complete the security check manually in the browser window")
                        try:
                            import sys
                            if sys.stdin.isatty():
                                input("Press Enter once you're logged into LinkedIn...")
                            else:
                                logger.info("Non-interactive environment detected - waiting 30 seconds for manual completion")
                                time.sleep(30)
                        except (EOFError, KeyboardInterrupt):
                            logger.info("Manual intervention cancelled or timed out")
                            raise RetryableError("Manual security verification cancelled")
                        
                        time.sleep(2)
                        final_url = page.url
                        if "/feed" in final_url or "/in/" in final_url:
                            logger.info("Manual security verification completed")
                            login_detected = True
                        else:
                            raise RetryableError("Security verification failed")
                
                # Method 1: Check URL - if we're redirected away from login page, likely successful
                current_url = page.url
                if "/login" not in current_url and ("linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url):
                    logger.info("Logged in successfully", current_url=current_url)
                    login_detected = True
                
                # Method 2: Check page title
                elif not login_detected:
                    page_title = page.title()
                    if "Feed" in page_title or "LinkedIn" in page_title and "Sign In" not in page_title:
                        logger.info("Logged in successfully", page_title=page_title)
                        login_detected = True
                
                # Method 3: Try common selectors as fallback
                if not login_detected:
                    login_success_selectors = config.LINKEDIN_SELECTORS["login_success"]
                    
                    for selector in login_success_selectors:
                        try:
                            page.wait_for_selector(selector, timeout=config.TIMEOUTS["login_success"])
                            logger.info("Logged in successfully", selector=selector)
                            login_detected = True
                            break
                        except PlaywrightTimeout:
                            continue
                
                # If still no success, check for error conditions
                if not login_detected:
                    # Check for common error indicators
                    error_indicators = {
                        'captcha': 'div.challenge',
                        'invalid_credentials': '[data-test-id="sign-in-error"]',
                        'form_error': '.form__input--error'
                    }
                    
                    for error_type, selector in error_indicators.items():
                        if page.locator(selector).count() > 0:
                            error_messages = {
                                'captcha': "Login blocked by security challenge/CAPTCHA. Please log in manually first.",
                                'invalid_credentials': "Invalid credentials. Please check your LINKEDIN_EMAIL and LINKEDIN_PASSWORD.",
                                'form_error': "Login form error detected. Please check your credentials."
                            }
                            logger.error("Login form error detected. Please check your credentials.", error_type=error_type)
                            raise FatalError(f"Login failed: {error_type}")
                    
                    if "/login" in page.url:
                        logger.error("Still on login page - credentials may be incorrect or CAPTCHA required.")
                        raise FatalError("Login failed: Still on login page")
                    else:
                        logger.error("Login failed - unable to detect successful login. This could be due to:")
                        logger.error("• CAPTCHA/MFA challenge")
                        logger.error("• Invalid credentials")
                        logger.error("• LinkedIn UI changes")
                        logger.error("• Rate limiting")
                        raise RetryableError("Login detection failed - may be temporary")
                
            except RetryableError as e:
                error_msg = str(e)
                # If we're in the middle of manual login, let the error propagate
                # Otherwise handle it normally
                if "manual login" in error_msg.lower():
                    raise e
                logger.error(f"Login failed: {e}")
                debug_pause("Current URL and page title", current_url=page.url, page_title=page.title())
                raise e
            except FatalError as e:
                logger.error(f"Login failed: {e}")
                debug_pause("Current URL and page title", current_url=page.url, page_title=page.title())
                raise e
            except Exception as e:
                logger.error(f"Unexpected error during login: {e}")
                raise RetryableError(f"Unexpected login error: {e}")
            
            # Session established - no cookie saving to avoid detection
            if login_detected:
                # Wait for session to be fully established
                logger.info("Waiting for LinkedIn session to be fully established...")
                time.sleep(5)
                
                # Verify we're still logged in before proceeding
                current_url = page.url
                page_title = page.title()
                
                # Check if we're still on a valid LinkedIn page (not redirected to login)
                if "/login" in current_url or "Sign In" in page_title:
                    logger.warning("Session appears invalid after login - may need to retry")
                    raise RetryableError("Session validation failed after login")
                
                logger.info("Session validated successfully - proceeding with job search")

        #  GO TO JOBS PAGE FIRST (like before)
        logger.info("Navigating to LinkedIn Jobs page initially")
        
        # Debug stop before jobs page navigation
        if not debug_skip_stops():
            debug_stop("About to navigate to LinkedIn Jobs page", 
                      current_url=page.url,
                      page_title=page.title())
        
        # Debug pause before navigation
        debug_pause("About to navigate to LinkedIn Jobs page")
        
        # Navigate to LinkedIn Jobs page first
        try:
            page.goto("https://www.linkedin.com/jobs/", timeout=config.TIMEOUTS["search_page"], wait_until="domcontentloaded")
            logger.info("Successfully navigated to LinkedIn Jobs page")
            
            # Debug pause after initial navigation
            debug_pause("Successfully navigated to LinkedIn Jobs page", 
                       current_url=page.url, 
                       page_title=page.title())
                    
        except Exception as e:
            logger.warning("Failed to navigate to LinkedIn Jobs page", error=str(e))
            logger.info("Continuing with direct search URL navigation")
        
        #  GO TO SEARCH PAGE 
        logger.info("Navigating to job search URL", search_url=search_url)
        
        # Debug stop before search page navigation
        if not debug_skip_stops():
            debug_stop("About to navigate to specific job search URL", 
                      search_url=search_url,
                      current_url=page.url)
        
        # Debug pause before search navigation
        debug_pause("About to navigate to specific job search URL", search_url=search_url)
        
        # Enhanced navigation with retry logic and error handling
        navigation_success = False
        max_navigation_attempts = 3
        
        for attempt in range(max_navigation_attempts):
            try:
                logger.info("Navigation attempt", attempt=attempt + 1, max_attempts=max_navigation_attempts)
                
                # Add randomized delays to avoid detection
                HumanBehavior.simulate_enhanced_hesitation(1.0, 3.0)
                HumanBehavior.simulate_natural_viewport_interaction(page)
                
                # Try to navigate to the search page
                page.goto(search_url, timeout=config.TIMEOUTS["search_page"], wait_until="domcontentloaded")
                
                # Verify we're on the correct page
                current_url = page.url
                if "linkedin.com/jobs" in current_url or "linkedin.com/search" in current_url:
                    logger.info("Successfully navigated to job search page", current_url=current_url)
                    navigation_success = True
                    break
                else:
                    logger.warning("Unexpected URL after navigation", current_url=current_url)
                    if attempt < max_navigation_attempts - 1:
                        logger.info("Retrying navigation")
                        continue
                    else:
                        logger.error("Failed to reach job search page", max_attempts=max_navigation_attempts)
                        raise RetryableError("Failed to navigate to job search page")
                        
            except PlaywrightTimeout as e:
                logger.warning("Navigation timeout", attempt=attempt + 1, error=str(e))
                if attempt < max_navigation_attempts - 1:
                    print(f"[INFO] Retrying navigation...")
                    continue
                else:
                    logger.error("Navigation failed due to timeout", max_attempts=max_navigation_attempts)
                    raise RetryableError(f"Navigation timeout: {e}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning("Navigation error", attempt=attempt + 1, error_msg=error_msg)
                
                # Check for specific error types
                if "ERR_HTTP_RESPONSE_CODE_FAILURE" in error_msg:
                    logger.info("LinkedIn returned HTTP error - likely anti-bot protection")
                    logger.info("This may be due to:")
                    logger.info("• LinkedIn's anti-bot measures")
                    logger.info("• Rate limiting from too many requests")
                    logger.info("• IP address being flagged")
                    logger.info("• Browser fingerprint detection")
                    
                    if attempt < max_navigation_attempts - 1:
                        logger.info("Retrying with longer delay")
                        # Add extra delay for anti-bot protection
                        extra_delay = 5 + (attempt * 3)  # 5s, 8s, 11s delays
                        logger.info("Adding extra delay for anti-bot protection", extra_delay=extra_delay)
                        time.sleep(extra_delay)
                        continue
                    else:
                        logger.error("LinkedIn blocked navigation", max_attempts=max_navigation_attempts)
                        logger.error("Suggestions:")
                        logger.error("• Wait 10-15 minutes before trying again")
                        logger.error("• Try using a different IP address/VPN")
                        logger.error("• Log into LinkedIn manually first to verify account")
                        logger.error("• Check if LinkedIn has flagged your account")
                        raise RetryableError("LinkedIn blocked navigation - try again later")
                        
                elif "net::ERR_" in error_msg:
                    logger.info("Network error detected", error_msg=error_msg)
                    if attempt < max_navigation_attempts - 1:
                        logger.info("Retrying navigation")
                        continue
                    else:
                        logger.error("Network error persisted", max_attempts=max_navigation_attempts)
                        raise RetryableError(f"Network error: {e}")
                        
                else:
                    logger.error("Unexpected navigation error", error_msg=error_msg)
                    if attempt < max_navigation_attempts - 1:
                        logger.info("Retrying navigation")
                        continue
                    else:
                        raise RetryableError(f"Navigation failed: {e}")
        
        if not navigation_success:
            logger.error("Failed to navigate to job search page after all attempts")
            logger.info("Attempting fallback navigation strategy")
            
            # Fallback: Try navigating to LinkedIn home first, then to jobs
            try:
                logger.info("Fallback: Navigating to LinkedIn home page first")
                page.goto("https://www.linkedin.com/feed/", timeout=config.TIMEOUTS["search_page"])
                time.sleep(3)  # Wait for page to load
                
                logger.info("Fallback: Now navigating to job search")
                page.goto(search_url, timeout=config.TIMEOUTS["search_page"])
                
                current_url = page.url
                if "linkedin.com/jobs" in current_url or "linkedin.com/search" in current_url:
                    logger.info("Fallback navigation successful", current_url=current_url)
                    navigation_success = True
                else:
                    logger.error("Fallback navigation also failed", current_url=current_url)
                    raise RetryableError("All navigation attempts failed")
                    
            except Exception as fallback_error:
                logger.error("Fallback navigation failed", error=str(fallback_error))
                raise RetryableError("Navigation failed after all retry attempts and fallback")
        
        if not navigation_success:
            logger.error("Failed to navigate to job search page after all attempts")
            raise RetryableError("Navigation failed after all retry attempts")
        
        if config.DEBUG:
            logger.debug("Current URL and page title", current_url=page.url, page_title=page.title())

        #  COLLECT JOB LINKS 
        logger.info("Collecting job links")
        
        # Debug stop before job collection
        if not debug_skip_stops():
            debug_stop("About to start collecting job links", 
                      max_jobs=max_jobs,
                      search_url=search_url,
                      current_url=page.url)
        
        # Debug pause before job collection
        # Debug pause before collecting job links
        debug_pause("About to start collecting job links", max_jobs=max_jobs)
        
        job_links = collect_job_links_with_pagination(page, search_url, max_jobs=max_jobs)
        if not job_links:
            logger.warning("No job links found")
            return []
        
        logger.info("Found job links", count=len(job_links))
        
        # Debug pause after job collection
        # Debug pause after job collection
        debug_pause("Job collection completed", job_count=len(job_links))

        #  LOAD PERSONAL INFO 
        logger.info("Loading personal information")
        try:
            with open(personal_info_path, "r", encoding="utf-8") as f:
                personal_info = yaml.safe_load(f)
        except Exception as e:
            logger.error("Could not load personal info", file_path=personal_info_path, error=str(e))
            return []

        # Build experiences list
        experiences = []
        for entry in personal_info.get("job_history", []):
            experiences.append({
                "role": entry.get("title", ""),
                "company": entry.get("company", ""),
                "years": f"{entry.get('start_date', '')} - {entry.get('end_date', 'Present')}",
                "responsibilities": entry.get("responsibilities", [])
            })

        # Education & references
        education  = personal_info.get("education", [])
        references = personal_info.get("references", [])

        #  SCRAPE, BUILD & APPLY LOOP 
        jobs_data = []  
        
        # Debug stop before job processing loop
        if not debug_skip_stops():
            debug_stop("About to start job processing loop", 
                      job_count=len(job_links),
                      max_jobs=max_jobs,
                      auto_apply=config.AUTO_APPLY)
        
        # Debug pause before starting job processing loop
        # Debug pause before job processing loop
        debug_pause("About to start job processing loop", job_count=len(job_links))
        
        for idx, job_url in enumerate(job_links, start=1):
            # Check if browser was manually closed
            if browser_monitor.should_exit():
                logger.info("Browser was manually closed - stopping job processing")
                break
                
            logger.info("Opening job page", job_index=idx, total_jobs=len(job_links), job_url=job_url)
            
            # Debug pause before each job
            # Debug pause before processing each job
            debug_pause("About to process job", job_index=idx, total_jobs=len(job_links), job_url=job_url)

            with ErrorContext(f"Processing job {idx}/{len(job_links)}", page) as job_context:
                job_context.add_context("job_url", job_url)
                job_context.add_context("job_index", idx)
                
                try:
                    # [OK] Check if browser was manually closed
                    if browser_monitor.should_exit():
                        logger.info("Browser was manually closed - stopping job processing")
                        break
                        
                    # [OK] Check if browser context is still valid
                    try:
                        # Test if context is still valid by checking if we can create a page
                        job_page = context.new_page()
                        
                        # Maintain stealth session continuity
                        if stealth_session:
                            stealth_session.maintain_stealth_continuity(job_page)
                    except Exception as context_error:
                        logger.error("Browser context is no longer valid", error=str(context_error))
                        logger.error("Cannot process more jobs. Stopping.")
                        break

                    # Add delay between job page requests to avoid rate limiting
                    if idx > 1:  # Skip delay for first job
                        # Adaptive delay: increase if we've seen failures
                        base_min, base_max = config.DELAYS["between_jobs"]
                        
                        # Track consecutive failures to increase delay
                        if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                            scrape_jobs_from_search.consecutive_failures = 0
                        
                        # Increase delay if we've had recent failures
                        if scrape_jobs_from_search.consecutive_failures > 0:
                            multiplier = 1 + (scrape_jobs_from_search.consecutive_failures * 0.5)
                            delay = random.uniform(base_min * multiplier, base_max * multiplier)
                            logger.info("Waiting", delay=delay, reason=f"increased due to {scrape_jobs_from_search.consecutive_failures} recent failure(s)")
                        else:
                            delay = random.uniform(base_min, base_max)
                            logger.info("Waiting to avoid rate limiting", delay=delay)
                        time.sleep(delay)
                    
                    try:
                        job_page.goto(job_url, timeout=config.TIMEOUTS["job_page"])
                    except TargetClosedError:
                        logger.warning("LinkedIn closed the tab unexpectedly", job_url=job_url)
                        job_context.add_context("error", "TargetClosedError")
                        continue
                    except PlaywrightTimeout:
                        logger.warning("Timeout loading job", job_url=job_url)
                        
                        # Track timeout failures for adaptive delay
                        if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                            scrape_jobs_from_search.consecutive_failures = 0
                        scrape_jobs_from_search.consecutive_failures += 1
                        
                        # Wait longer after timeout
                        wait_time = random.uniform(*config.DELAYS["graphql_failure_wait"])
                        logger.warning("Waiting after timeout", wait_time=wait_time)
                        time.sleep(wait_time)
                        
                        job_context.add_context("error", "PlaywrightTimeout")
                        continue
                    except Exception as e:
                        error_msg = str(e)
                        if "ERR_HTTP_RESPONSE_CODE_FAILURE" in error_msg:
                            logger.warning("LinkedIn rate limiting detected", job_url=job_url)
                            
                            # Track rate limit failures for adaptive delay
                            if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = 0
                            scrape_jobs_from_search.consecutive_failures += 2  # Rate limits are more serious
                            
                            # Wait longer after rate limit detection
                            wait_time = random.uniform(*config.DELAYS["rate_limit_wait"])
                            logger.warning("Waiting after rate limit detection", wait_time=wait_time)
                            time.sleep(wait_time)
                            
                            job_context.add_context("error", "RateLimited")
                            continue
                        elif "net::ERR_" in error_msg:
                            logger.warning("Network error for job", job_url=job_url, error_msg=error_msg)
                            job_context.add_context("error", f"NetworkError: {error_msg}")
                            continue
                        else:
                            logger.warning("Unexpected error loading job", job_url=job_url, error_msg=error_msg)
                            job_context.add_context("error", f"UnexpectedError: {error_msg}")
                            continue

                    # [OK] Enhanced job availability detection
                    def is_job_unavailable(page):
                        """
                        Enhanced job availability detection with multiple indicators.
                        Returns True if job is definitely unavailable, False otherwise.
                        """
                        try:
                            # Wait for page to stabilize first
                            time.sleep(2)
                            
                            # Check for multiple unavailable indicators
                            unavailable_selectors = [
                                config.LINKEDIN_SELECTORS["job_detail"]["unavailable"],
                                "div.jobs-unavailable",
                                "div[data-test-id*='unavailable']",
                                "div:has-text('This job is no longer available')",
                                "div:has-text('Job not found')",
                                "div:has-text('This job posting is no longer available')"
                            ]
                            
                            # Check for any unavailable indicators
                            for selector in unavailable_selectors:
                                if page.locator(selector).count() > 0:
                                    logger.debug("Found unavailable indicator", selector=selector)
                                    return True
                            
                            # Check for error pages or redirects
                            current_url = page.url
                            page_title = page.title()
                            
                            # If we're redirected to an error page or main jobs page
                            if ("error" in current_url.lower() or 
                                "not-found" in current_url.lower() or
                                "jobs" in current_url.lower() and "view" not in current_url.lower()):
                                logger.debug("Detected redirect to error/main page", current_url=current_url)
                                return True
                            
                            # Check if page title indicates error
                            if ("not found" in page_title.lower() or 
                                "unavailable" in page_title.lower() or
                                "error" in page_title.lower()):
                                logger.debug("Page title indicates unavailability", page_title=page_title)
                                return True
                            
                            # Check if job title element exists (basic availability check)
                            try:
                                title_element = page.locator("h1")
                                if title_element.count() == 0:
                                    logger.debug("No job title found - likely unavailable")
                                    return True
                            except:
                                logger.debug("Could not check for job title")
                                return True
                            
                            return False
                            
                        except Exception as e:
                            logger.warning("Error checking job availability", error=str(e))
                            # If we can't determine availability, assume it's available
                            return False
                    
                    # Check if job is unavailable (only if enabled in config)
                    if config.SKIP_UNAVAILABLE_JOBS and is_job_unavailable(job_page):
                        logger.info("Job is unavailable or expired", job_url=job_url)
                        job_page.close()
                        continue
                    elif not config.SKIP_UNAVAILABLE_JOBS:
                        logger.debug("Skipping unavailable job detection (disabled in config)")

                    job_page.wait_for_selector("h1", timeout=config.TIMEOUTS["job_title"])
                    
                    # Simulate human viewing the page
                    HumanBehavior.simulate_viewport_movement(job_page)
                    HumanBehavior.simulate_enhanced_hesitation(0.5, 1.2)  # Pause to "read" job title
                    
                    # Enhanced GraphQL failure detection and handling
                    if config.DEBUG:
                        logger.debug("Checking for GraphQL loading indicators")
                    
                    # Check for GraphQL-specific loading indicators
                    graphql_loading_selectors = [
                        ".scaffold-skeleton-container",
                        ".job-description-skeleton__text-container", 
                        "div[aria-busy='true'][alt*='Loading']",
                        ".loading-spinner",
                        ".artdeco-loader",
                        ".jobs-unified-top-card__loading",
                        ".jobs-description__loading"
                    ]
                    
                    # Also check for GraphQL error indicators
                    graphql_error_selectors = [
                        "div:has-text('Something went wrong')",
                        "div:has-text('Try refreshing the page')",
                        ".error-page",
                        ".jobs-unavailable",
                        "[data-test-id*='error']"
                    ]
                    
                    max_wait_time = 20  # Increased to 20 seconds for GraphQL
                    wait_start = time.time()
                    graphql_error_detected = False
                    
                    while time.time() - wait_start < max_wait_time:
                        # Check for GraphQL errors first
                        for error_selector in graphql_error_selectors:
                            if job_page.locator(error_selector).count() > 0:
                                logger.error("GraphQL error detected", error_selector=error_selector)
                                graphql_error_detected = True
                                break
                        
                        if graphql_error_detected:
                            break
                        
                        # Check for loading indicators
                        loading_detected = False
                        for loading_selector in graphql_loading_selectors:
                            if job_page.locator(loading_selector).count() > 0:
                                loading_detected = True
                                break
                        
                        if not loading_detected:
                            if config.DEBUG:
                                logger.debug("No GraphQL loading indicators detected")
                            break
                        else:
                            if config.DEBUG:
                                logger.debug("GraphQL loading indicators still present, waiting")
                            time.sleep(0.5)
                    
                    # Handle GraphQL errors
                    if graphql_error_detected:
                        logger.error("GraphQL error detected on job page - likely bot detection")
                        logger.info("This may indicate:")
                        logger.info("• LinkedIn has detected automated behavior")
                        logger.info("• Session cookies are invalid/expired")
                        logger.info("• Rate limiting is in effect")
                        logger.info("• IP address is flagged")
                        
                        # Try to recover session by refreshing cookies
                        logger.info("Attempting session recovery")
                        try:
                            # Cookie manager removed to prevent automated behavior detection
                            # Skip cookie refresh and continue with manual intervention
                            logger.info("Skipping cookie refresh to avoid automated behavior detection")
                            cookie_refreshed = False
                            if cookie_refreshed:
                                logger.info("Session cookies refreshed - retrying job page")
                                # Close current page and retry
                                job_page.close()
                                time.sleep(2)
                                
                                # Create new page and retry
                                retry_page = context.new_page()
                                retry_page.goto(job_url, timeout=config.TIMEOUTS["job_page"])
                                time.sleep(3)  # Give page time to load
                                
                                # Check if GraphQL error is resolved
                                retry_content = retry_page.inner_text("body").lower()
                                if "something went wrong" not in retry_content and "try refreshing" not in retry_content:
                                    print(f"  [SUCCESS] Session recovery successful - continuing with job")
                                    job_page = retry_page  # Use the recovered page
                                    graphql_error_detected = False  # Reset error flag
                                else:
                                    print(f"  [WARN] Session recovery failed - GraphQL error persists")
                                    retry_page.close()
                            else:
                                print(f"  [WARN] Could not refresh session cookies")
                        except Exception as recovery_error:
                            print(f"  [WARN] Session recovery failed: {recovery_error}")
                        
                        if graphql_error_detected:  # If still has error after recovery attempt
                            # Track GraphQL failures for adaptive delay
                            if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = 0
                            scrape_jobs_from_search.consecutive_failures += 3  # GraphQL errors are serious
                            
                            # Wait longer after GraphQL errors
                            wait_time = random.uniform(*config.DELAYS["graphql_failure_wait"])
                            print(f"  [WARN] Waiting {wait_time:.1f}s after GraphQL error...")
                            time.sleep(wait_time)
                            
                            job_page.close()
                            continue
                    
                    # Check if we timed out waiting for content
                    if time.time() - wait_start >= max_wait_time:
                        print(f"  [WARN] Job description appears to be stuck loading (GraphQL timeout).")
                        print(f"  [INFO] This may indicate GraphQL API issues or bot detection.")
                        
                        # Track timeout failures
                        if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                            scrape_jobs_from_search.consecutive_failures = 0
                        scrape_jobs_from_search.consecutive_failures += 2
                        
                        # Wait after timeout
                        wait_time = random.uniform(*config.DELAYS["graphql_failure_wait"])
                        print(f"  [WARN] Waiting {wait_time:.1f}s after GraphQL timeout...")
                        time.sleep(wait_time)
                    
                    # Additional wait for page to stabilize after loaders disappear
                    time.sleep(1.5)  # Increased wait time

                    # --- SCRAPE METADATA ---
                    title_sel = ",".join(config.LINKEDIN_SELECTORS["job_detail"]["title"])
                    titles = job_page.locator(title_sel).all_inner_texts()
                    title = titles[0].strip() if titles else "N/A"

                    comp_sel = ",".join(config.LINKEDIN_SELECTORS["job_detail"]["company"])
                    comps = job_page.locator(comp_sel).all_inner_texts()
                    company = comps[0].strip() if comps else "N/A"

                    locs = job_page.locator(config.LINKEDIN_SELECTORS["job_detail"]["location"]).all_inner_texts()
                    location = "N/A"
                    for loc in locs:
                        clean_loc = loc.strip()
                        if "," in clean_loc or "Metropolitan Area" in clean_loc:
                            location = clean_loc
                            break

                    # [OK] Description (scraped ONCE) with fallback selectors
                    # Wait for description to actually load (not just selector to exist)
                    raw_desc = ""
                    desc_selectors = config.LINKEDIN_SELECTORS["job_detail"]["description"]
                    
                    # Wait for description content to load with timeout
                    description_loaded = False
                    max_wait_time = 15  # Maximum seconds to wait for description
                    wait_start = time.time()
                    
                    if config.DEBUG:
                        print(f"  [DEBUG] Waiting for job description to load (max {max_wait_time}s)...")
                    
                    while time.time() - wait_start < max_wait_time and not description_loaded:
                        # Try each selector until we find one that works
                        for selector in desc_selectors if isinstance(desc_selectors, list) else [desc_selectors]:
                            try:
                                desc_locator = job_page.locator(selector)
                                if desc_locator.count() > 0:
                                    # Use .first() to avoid strict mode violation when multiple elements match
                                    # Check if description actually has content (not just skeleton/loading)
                                    raw_desc = desc_locator.first.inner_text().strip()
                                    
                                    # Skip if it's just skeleton/loading text
                                    if "scaffold-skeleton" in raw_desc.lower() or len(raw_desc) < 50:
                                        continue
                                    
                                    # Description is loaded if it has substantial content
                                    # LinkedIn often shows loading spinners/placeholders, so check for real content
                                    if len(raw_desc) > 100:  # At least 100 chars indicates real content
                                        description_loaded = True
                                        if config.DEBUG:
                                            print(f"  [DEBUG] Description loaded ({len(raw_desc)} chars)")
                                        break
                            except Exception as e:
                                if config.DEBUG:
                                    # Only log strict mode violations as warnings, not every retry
                                    if "strict mode violation" not in str(e):
                                        print(f"  [DEBUG] Selector check failed: {e}")
                                continue
                        
                        if not description_loaded:
                            # Wait a bit before retrying
                            time.sleep(0.5)
                    
                    # If description still not loaded, try fallback approach
                    if not description_loaded and not raw_desc:
                        if config.DEBUG:
                            print(f"  [DEBUG] Description not loaded via selectors, trying fallback...")
                        try:
                            # Try to find any div that might contain job description using more specific selector
                            potential_desc = job_page.locator('#job-details').first
                            if potential_desc.count() > 0:
                                raw_desc = potential_desc.inner_text().strip()
                                # Skip skeleton content
                                if "scaffold-skeleton" not in raw_desc.lower() and len(raw_desc) > 100:
                                    description_loaded = True
                        except Exception as e:
                            if config.DEBUG:
                                print(f"  [DEBUG] Fallback check failed: {e}")
                    
                    if not description_loaded:
                        if len(raw_desc) == 0:
                            print(f"  [WARN] Job description failed to load - likely GraphQL/bot prevention. Skipping job.")
                            
                            # Track failures for adaptive delay
                            if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = 0
                            scrape_jobs_from_search.consecutive_failures += 1
                            
                            # If multiple failures, wait longer before next job
                            if scrape_jobs_from_search.consecutive_failures >= 3:
                                wait_time = random.uniform(*config.DELAYS["rate_limit_wait"])
                                print(f"  [WARN] Multiple failures detected. Waiting {wait_time:.1f}s before next job to avoid rate limiting...")
                                time.sleep(wait_time)
                            
                            job_page.close()
                            continue
                        else:
                            print(f"  [WARN] Job description may not have fully loaded (only {len(raw_desc)} chars). Continuing anyway...")
                            # Reset failure counter on partial success
                            if hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = max(0, scrape_jobs_from_search.consecutive_failures - 1)
                    
                    desc = clean_text(raw_desc)
                    print(f"  [INFO] Description captured ({len(raw_desc)} -> {len(desc)} chars after cleaning)")

                    # Simulate reading the job description (human-like behavior)
                    HumanBehavior.simulate_reading(raw_desc[:500], min_time=1.0, max_time=3.0)  # Read first 500 chars
                    HumanBehavior.simulate_viewport_movement(job_page)  # Occasional scroll while reading

                    # [OK] Extract & weight keywords
                    kws = extract_keywords(desc)
                    weighted = weigh_keywords(desc, kws)
                    extracted = [kw for kw, _ in weighted]
                    print(f"  [INFO] Extracted {len(extracted)} keywords.")

                    # Debug checkpoint after keyword extraction
                    debug_checkpoint("keywords_extracted", 
                                   job_title=title,
                                   company=company,
                                   keyword_count=len(extracted),
                                   keywords=extracted[:10])  # First 10 keywords

                    # [OK] LLM summary + skills with error handling
                    try:
                        # Debug stop before LLM processing
                        if not debug_skip_stops():
                            debug_stop("About to generate LLM summary", 
                                      job_title=title,
                                      company=company,
                                      description_length=len(desc),
                                      extracted_keywords=extracted[:5])
                        
                        from src.error_handler import APIFailureHandler
                        raw_summary = APIFailureHandler.handle_openai_failure(
                            generate_resume_summary, title, company, desc
                        )
                        
                        if raw_summary is None:
                            print(f"  [WARN] LLM summary generation failed for {title} @ {company}. Using fallback.")
                            raw_summary = {
                                "summary": f"Experienced software developer with strong technical skills in {', '.join(extracted[:5])}.",
                                "keywords": ", ".join(extracted[:7])
                            }
                            raw_summary = json.dumps(raw_summary)
                        
                        # Handle case where raw_summary might be a dict instead of JSON string
                        if isinstance(raw_summary, dict):
                            raw_summary = json.dumps(raw_summary)
                        
                        parsed = json.loads(raw_summary)
                    except json.JSONDecodeError as e:
                        print(f"  [ERROR] LLM returned invalid JSON for {title} @ {company}: {e}")
                        print(f"  [DEBUG] Raw summary was: {raw_summary}")
                        print("  [SKIP] Skipping this job because summary couldn't be parsed.")
                        job_context.add_context("error", f"JSONDecodeError: {e}")
                        job_page.close()
                        continue   # [SKIP] this job entirely
                    except Exception as e:
                        print(f"  [ERROR] Unexpected error in LLM processing for {title} @ {company}: {e}")
                        job_context.add_context("error", f"LLM processing error: {e}")
                        job_page.close()
                        continue

                    summary_text = parsed.get("summary", "").strip()
                    llm_skills  = [kw.strip() for kw in parsed.get("keywords", "").split(",") if kw.strip()]

                    if not summary_text:
                        print(f"  [WARN] Empty summary for {title} @ {company}. Skipping this job.")
                        job_context.add_context("error", "Empty summary")
                        job_page.close()
                        continue   # [SKIP] Also skip if summary field came back blank

                    # [OK] Build payload for resume
                    payload = {
                        "name":        f"{personal_info.get('first_name','')} {personal_info.get('last_name','')}",
                        "email":       personal_info.get("email",""),
                        "phone":       personal_info.get("phone",""),
                        "linkedin":    personal_info.get("linkedin",""),
                        "github":      personal_info.get("github",""),
                        "address":     personal_info.get("address",""),
                        "summary":     summary_text,
                        "skills": [normalize_skill(kw) for kw in (llm_skills or extracted)],
                        "matched_keywords": extracted,
                        "experiences": experiences,
                        "education":   education,
                        "references":  references,
                        "title":       title,
                        "company":     company,
                        "location":    location,
                        "description": desc,
                    }

                    # [OK] Generate tailored resume PDF with error handling
                    try:
                        # Debug stop before resume building
                        if not debug_skip_stops():
                            debug_stop("About to build resume PDF", 
                                      job_title=title,
                                      company=company,
                                      summary_length=len(summary_text),
                                      skills_count=len(llm_skills or extracted))
                        
                        from src.error_handler import APIFailureHandler
                        pdf_path = build_resume(payload)
                        
                        # Verify PDF was created successfully
                        if not pdf_path or not os.path.exists(pdf_path):
                            raise Exception("PDF file was not created or is not accessible")
                        
                        logger.info("Resume generated", pdf_path=pdf_path)
                        job_context.add_context("resume_path", pdf_path)
                        
                    except Exception as e:
                        logger.error("Resume generation failed", title=title, company=company, error=str(e))
                        job_context.add_context("error", f"Resume generation failed: {e}")
                        
                        # Try fallback PDF generation
                        try:
                            fallback_pdf = APIFailureHandler.handle_weasyprint_failure(
                                f"<html><body><h1>{title}</h1><p>Resume generation failed</p></body></html>",
                                str(config.FILE_PATHS["resumes_dir"] / f"fallback_{idx}.pdf")
                            )
                            if fallback_pdf:
                                print(f"  [INFO] Fallback resume created")
                                pdf_path = str(config.FILE_PATHS["resumes_dir"] / f"fallback_{idx}.pdf")
                            else:
                                print(f"  [ERROR] Fallback resume generation also failed")
                                job_page.close()
                                continue
                        except Exception as fallback_error:
                            print(f"  [ERROR] Fallback resume generation failed: {fallback_error}")
                            job_page.close()
                            continue

                    # [OK] Easy Apply automation with error handling
                    apply_status = "skipped"
                    apply_error = None
                    if config.AUTO_APPLY:
                        # Debug stop before Easy Apply
                        if not debug_skip_stops():
                            debug_stop("About to attempt LinkedIn Easy Apply", 
                                      job_title=title,
                                      company=company,
                                      pdf_path=pdf_path,
                                      job_url=job_url)
                        
                        if config.DEBUG:
                            print("\n[DEBUG] About to attempt LinkedIn Easy Apply...")
                        logger.info("Attempting LinkedIn Easy Apply")
                        
                        try:
                            # Check if browser was manually closed before Easy Apply
                            if browser_monitor.should_exit():
                                print("\n[INFO] Browser was manually closed during Easy Apply - stopping")
                                break
                                
                            # Check for UI changes before Easy Apply (with context-aware detection)
                            ui_changes = ui_handler.detect_ui_changes(context="easy_apply")
                            if ui_changes["easy_apply_changed"]:
                                logger.warning("LinkedIn Easy Apply UI changes detected")
                                if not ui_handler.adapt_to_changes(ui_changes):
                                    raise LinkedInUIError("LinkedIn Easy Apply UI has changed and cannot be adapted")
                            
                            ok = apply_to_job(job_page, pdf_path, job_url)
                            apply_status = "applied" if ok else "failed"
                            print(f"  [RESULT] Easy Apply {'SUCCESS' if ok else 'FAILED'}")
                            job_context.add_context("apply_status", apply_status)
                            
                            # Reset failure counter on successful job processing
                            if ok and hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = 0
                                
                        except LinkedInUIError as e:
                            apply_status = "failed"
                            apply_error = f"UI Error: {e}"
                            print(f"  [ERROR] Easy Apply UI error: {apply_error}")
                            job_context.add_context("error", apply_error)
                        except RetryableError as e:
                            apply_status = "failed"
                            apply_error = f"Retryable Error: {e}"
                            print(f"  [ERROR] Easy Apply retryable error: {apply_error}")
                            job_context.add_context("error", apply_error)
                        except Exception as e:
                            apply_status = "failed"
                            apply_error = f"Unexpected Error: {e}"
                            print(f"  [ERROR] Easy Apply failed: {apply_error}")
                            job_context.add_context("error", apply_error)

                    # [OK] Store job results
                    jobs_data.append({
                        **payload,
                        "url":          job_url,
                        "pdf_path":     pdf_path,
                        "apply_status": apply_status,
                        "apply_error":  apply_error,
                    })
                    
                    # Reset failure counter on successful job processing (even if Easy Apply disabled)
                    if hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                        scrape_jobs_from_search.consecutive_failures = 0

                    job_page.close()

                except Exception as e:
                    error_msg = str(e)
                    job_context.add_context("error", error_msg)
                    
                    # Provide more detailed error information
                    if error_msg == "'unavailable'":
                        logger.error("Job processing failed: Job detected as unavailable", 
                                   job_url=job_url, 
                                   job_index=idx,
                                   error_type="unavailable_detection")
                        logger.info("This may be a false positive - check if the job is actually available")
                    else:
                        logger.error("Job processing failed", 
                                   job_url=job_url, 
                                   job_index=idx,
                                   error=error_msg)
                    
                    try:
                        job_page.close()
                    except:
                        pass
                    # Don't close the browser context, just continue to next job
                    continue

        # Stop browser monitoring before returning
        browser_monitor.stop_monitoring()
        
        # Report resource error summary
        error_summary = resource_handler.get_error_summary()
        if error_summary['total_errors'] > 0:
            print(f"[INFO] Resource error summary: {error_summary}")
            recommendations = resource_handler.get_recommendations()
            if recommendations:
                print(f"[INFO] Recommendations: {', '.join(recommendations)}")
        
        # Cleanup stealth session
        if stealth_session:
            stealth_session.save_session_state(page)
            stealth_session.cleanup_stealth_session()
            logger.info("Stealth session cleaned up")
        
        # Cleanup browser configuration
        browser_config.cleanup()
        
        # Debug checkpoint at function end
        debug_checkpoint("scrape_jobs_from_search_complete", 
                        jobs_processed=len(jobs_data),
                        total_jobs_found=len(job_links))
        
        return jobs_data
    
    def _handle_automatic_security_verification(self, page):
        """Handle automatic security verification waiting."""
        try:
            logger.info("Waiting for automatic security check to complete", timeout_seconds=30)
            page.wait_for_url(
                lambda url: "checkpoint" not in url.lower(),
                timeout=30000  # 30 seconds timeout
            )
            logger.info("Security verification page redirected")
            time.sleep(3)  # Give page time to fully load
            
            # Check where we were redirected to
            final_url = page.url
            
            # If redirected to login, verification failed
            if "/login" in final_url or "uas/login" in final_url:
                logger.error("LinkedIn redirected to login page after security verification")
                raise RetryableError("Security verification failed - redirected to login")
            
            # If we got to a good page, mark as logged in
            if "linkedin.com/feed" in final_url or "linkedin.com/in/" in final_url:
                logger.info("Successfully logged in after automatic security verification")
            else:
                logger.info("Security verification completed", final_url=final_url)
                
        except PlaywrightTimeout:
            # Timeout waiting for redirect - fall back to manual
            final_url = page.url
            logger.warning("Automatic security verification timed out", final_url=final_url)
            raise RetryableError("Automatic security verification timeout")
            
        except Exception as e:
            logger.warning("Automatic security verification error", error=str(e))
            raise RetryableError(f"Security verification error: {e}")
