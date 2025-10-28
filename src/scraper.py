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
from src.cookie_manager import CookieManager
import src.config as config
from src.config import MAX_JOBS
from typing import Optional
import yaml
import json
import time
import logging
import os
import sys

# Set console encoding to avoid Unicode issues on Windows
if sys.platform == "win32":
    import locale
    import os
    # Set environment variable for UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        # Try to set UTF-8 encoding
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        # Fallback to default
        pass

logger = logging.getLogger(__name__)

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
        print("[INFO] Browser monitoring started - program will exit if browser is manually closed")
        print("[DEBUG] Monitoring will only trigger after 5 consecutive connection failures")
        
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
        
        while self.monitoring:
            try:
                # Check if browser is still connected by trying to access browser contexts
                # This is more reliable than creating new pages
                contexts = self.browser.contexts
                if contexts:  # If we have contexts, browser is still alive
                    consecutive_failures = 0  # Reset failure counter on success
                else:
                    consecutive_failures += 1
                    
                time.sleep(check_interval)
            except Exception as e:
                consecutive_failures += 1
                if self.monitoring and consecutive_failures >= max_failures:
                    print(f"\n[WARNING] Browser connection lost after {consecutive_failures} consecutive failures: {e}")
                    print("[INFO] Browser was manually closed by user - forcing program exit")
                    self.force_exit = True
                    self.monitoring = False
                    
                    # Force exit the program
                    try:
                        # Try graceful exit first
                        print("[INFO] Attempting graceful shutdown...")
                        sys.exit(0)
                    except:
                        # Force exit if graceful doesn't work
                        os._exit(1)
                    break
                elif self.monitoring:
                    # Log the failure but don't exit yet
                    print(f"[DEBUG] Browser connection check failed ({consecutive_failures}/{max_failures}): {e}")
                    time.sleep(2)  # Wait a bit before retrying
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\n[INFO] Keyboard interrupt received - stopping monitoring")
                self.force_exit = True
                self.monitoring = False
                break
                
    def should_exit(self):
        """Check if program should exit due to browser closure."""
        return self.force_exit
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n[INFO] Received signal {signum} - initiating graceful shutdown...")
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
        
        # Launch browser with enhanced configuration
        browser = browser_config.launch_browser(p)
        
        # Create context with stealth settings
        context = browser_config.create_context(browser)
        
        # Initialize cookie manager
        cookie_manager = CookieManager()
        
        page = context.new_page()
        
        # Try to load existing cookies for persistent login
        saved_cookies = cookie_manager.load_cookies()
        if saved_cookies:
            print("[INFO] Found saved LinkedIn cookies - attempting to use existing session")
            try:
                # Prepare cookies for Playwright (ensure proper format)
                prepared_cookies = cookie_manager.prepare_cookies_for_playwright(
                    saved_cookies, 
                    url="https://www.linkedin.com"
                )
                
                # Navigate to LinkedIn domain first (required for setting cookies)
                page.goto("https://www.linkedin.com", timeout=config.TIMEOUTS["login"])
                time.sleep(1)  # Brief pause for domain to load
                
                # Add cookies to context
                context.add_cookies(prepared_cookies)  # type: ignore
                print(f"[INFO] Loaded {len(prepared_cookies)} cookies into browser context")
                
                # Navigate to feed to verify session
                page.goto("https://www.linkedin.com/feed/", timeout=config.TIMEOUTS["login"])
                
                # Simulate human-like viewing before checking login status
                HumanBehavior.simulate_hesitation(1.0, 2.0)
                HumanBehavior.simulate_viewport_movement(page)
                
                # Check if we're logged in
                current_url = page.url
                page_title = page.title()
                
                # Multiple checks for login success
                login_indicators = [
                    "/feed" in current_url,
                    "/in/" in current_url,
                    "LinkedIn" in page_title and "Feed" in page_title,
                    "Login" not in page_title and "Sign In" not in page_title
                ]
                
                if any(login_indicators):
                    print("[INFO] Successfully logged in using saved cookies - skipping login flow")
                    # Refresh cookies to update session
                    cookie_manager.refresh_cookies_if_needed(context, page)
                    skip_login = True
                else:
                    print("[INFO] Saved cookies appear to be expired or invalid - falling back to login")
                    # Delete invalid cookies to prevent future issues
                    cookie_manager.delete_cookies()
                    skip_login = False
                    
            except Exception as e:
                logger.warning(f"Failed to use saved cookies: {e}")
                print(f"[WARN] Could not use saved cookies: {e}")
                skip_login = False
        else:
            print("[INFO] No saved cookies found - will perform fresh login")
            skip_login = False
        
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

        #  LOGIN 
        if not skip_login:
            with ErrorContext("LinkedIn login", page) as login_context:
                login_context.add_context("email", email)
                login_context.add_context("search_url", search_url)
                
                # Debug pause before login
                if config.DEBUG:
                    print("[DEBUG] ⏸️  About to start LinkedIn login process")
                    print(f"[DEBUG] Email: {email}")
                    print("[DEBUG] Press Enter to continue...")
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                
                print("[INFO] Navigating to LinkedIn login page")
                page.goto("https://www.linkedin.com/login", timeout=config.TIMEOUTS["login"])
                
                # Debug pause after navigating to login page
                if config.DEBUG:
                    print("[DEBUG] ⏸️  Successfully navigated to LinkedIn login page")
                    print(f"[DEBUG] Current URL: {page.url}")
                    print(f"[DEBUG] Page title: {page.title()}")
                    print("[DEBUG] Press Enter to continue with login...")
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                
                # Check for UI changes before proceeding (with login context)
                ui_changes = ui_handler.detect_ui_changes(context="login")
                if ui_changes["login_page_changed"]:
                    logger.warning("LinkedIn login page UI changes detected")
                    if not ui_handler.adapt_to_changes(ui_changes):
                        raise LinkedInUIError("LinkedIn login page UI has changed and cannot be adapted")
                
                print("[INFO] Entering credentials")
                
                # Debug pause before entering credentials
                if config.DEBUG:
                    print("[DEBUG] ⏸️  About to enter login credentials")
                    print("[DEBUG] Press Enter to continue...")
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                
                # Use fallback selectors for login
                username_success = selector_fallback.safe_fill(
                    [config.LINKEDIN_SELECTORS["login"]["username"]], 
                    email, 
                    "username input"
                )
                if not username_success:
                    raise LinkedInUIError("Could not find username input field")
                
                # Debug pause after username entry
                if config.DEBUG:
                    print("[DEBUG] ⏸️  Username entered successfully")
                    print("[DEBUG] Press Enter to continue with password...")
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                
                password_success = selector_fallback.safe_fill(
                    [config.LINKEDIN_SELECTORS["login"]["password"]], 
                    password, 
                    "password input"
                )
                if not password_success:
                    raise LinkedInUIError("Could not find password input field")
                
                # Debug pause before clicking submit
                if config.DEBUG:
                    print("[DEBUG] ⏸️  Password entered successfully")
                    print("[DEBUG] Press Enter to submit login...")
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                
                submit_success = selector_fallback.safe_click(
                    [config.LINKEDIN_SELECTORS["login"]["submit"]], 
                    "login submit"
                )
                if not submit_success:
                    raise LinkedInUIError("Could not find or click login submit button")
                
                # Give LinkedIn a moment to process the login
                time.sleep(config.DELAYS["login_processing"])
        
        # Check for login success using multiple methods
        login_detected = skip_login  # If we skipped login, we're already logged in
        
        if not skip_login:
            try:
                # FIRST: Check for security verification page (must handle this before other login checks)
                page_title = page.title()
                current_url = page.url
                
                # Check if we're on security/checkpoint page
                if "Security Verification" in page_title or "security" in page_title.lower() or "checkpoint/challenge" in current_url:
                    print("[INFO] Security verification page detected. Waiting for verification to complete...")
                    
                    # Wait for redirect away from security page (LinkedIn may take 30-60 seconds)
                    try:
                        print("[INFO] Waiting for security check to complete (this may take 30-60 seconds)...")
                        page.wait_for_url(
                            lambda url: "checkpoint" not in url.lower(),
                            timeout=60000  # Increase timeout to 60 seconds
                        )
                        print("[INFO] Security verification page redirected")
                        time.sleep(3)  # Give page time to fully load
                        
                        # Check where we were redirected to
                        final_url = page.url
                        
                        # If redirected to login, verification failed
                        if "/login" in final_url or "uas/login" in final_url:
                            print("[ERROR] LinkedIn redirected to login page after security verification")
                            print("[ERROR] The security verification likely failed or requires manual completion")
                            print("[INFO] Please log in manually through the browser to complete the verification")
                            print("[INFO] This usually happens when LinkedIn detects automated login attempts")
                            raise RetryableError("Security verification failed - redirected to login")
                        
                        # If we got to a good page, mark as logged in
                        if "linkedin.com/feed" in final_url or "linkedin.com/in/" in final_url:
                            print("[INFO] Successfully logged in after security verification")
                            login_detected = True
                        else:
                            print(f"[INFO] Security verification completed (URL: {final_url})")
                            login_detected = True  # Assume success if not on login page
                            
                    except PlaywrightTimeout:
                        # Timeout waiting for redirect - check where we still are
                        final_url = page.url
                        print(f"[WARN] Security verification timed out. Still on: {final_url}")
                        
                        # If still on checkpoint page after timeout, ask user to complete manually
                        if "checkpoint" in final_url.lower():
                            print("[INFO] Security verification is taking longer than expected")
                            print("[INFO] The browser window is still open - please complete the security check manually")
                            print("[INFO] Once you're logged into LinkedIn (you'll see the feed), press Enter here...")
                            print("[INFO] The script will then save your session cookies for future automatic logins")
                            input("Press Enter once you're logged into LinkedIn...")
                            
                            # Check if user successfully logged in
                            time.sleep(2)  # Give page a moment to update
                            final_url = page.url
                            if "/feed" in final_url or "/in/" in final_url or "linkedin.com" in final_url:
                                print("[INFO] Successfully logged in manually")
                                login_detected = True
                            else:
                                print("[ERROR] Still not logged in. Please try again.")
                                raise RetryableError("Manual login completion failed")
                        else:
                            # Check if we got redirected somewhere else
                            if "/login" in final_url or "uas/login" in final_url:
                                print("[ERROR] LinkedIn redirected to login after security verification timeout")
                                raise RetryableError("Security verification timeout - redirected to login")
                            else:
                                # Unexpected state - but assume we might be logged in
                                print(f"[INFO] Security verification timed out but on unexpected page: {final_url}")
                                login_detected = True  # Optimistically assume success
                            
                    except Exception as e:
                        print(f"[WARN] Security verification wait error: {e}")
                        # Check where we ended up after the error
                        final_url = page.url
                        if "/login" in final_url or "uas/login" in final_url:
                            print("[ERROR] Error during security verification - redirected to login")
                            raise RetryableError("Security verification error - redirected to login")
                        elif "checkpoint" in final_url.lower():
                            print("[ERROR] Security verification error - still on checkpoint page")
                            raise RetryableError("Security verification error - check required")
                        else:
                            print(f"[INFO] Security verification error but on unexpected page: {final_url}")
                            login_detected = True  # Assume success
                
                # Method 1: Check URL - if we're redirected away from login page, likely successful
                current_url = page.url
                if "/login" not in current_url and ("linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url):
                    print(f"[INFO] Logged in successfully (URL redirect detected: {current_url}).")
                    login_detected = True
                
                # Method 2: Check page title
                elif not login_detected:
                    page_title = page.title()
                    if "Feed" in page_title or "LinkedIn" in page_title and "Sign In" not in page_title:
                        print(f"[INFO] Logged in successfully (page title indicates success: '{page_title}').")
                        login_detected = True
                
                # Method 3: Try common selectors as fallback
                if not login_detected:
                    login_success_selectors = config.LINKEDIN_SELECTORS["login_success"]
                    
                    for selector in login_success_selectors:
                        try:
                            page.wait_for_selector(selector, timeout=config.TIMEOUTS["login_success"])
                            print(f"[INFO] Logged in successfully (detected via: {selector}).")
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
                            print(f"[ERROR] {error_messages[error_type]}")
                            raise FatalError(f"Login failed: {error_type}")
                    
                    if "/login" in page.url:
                        print("[ERROR] Still on login page - credentials may be incorrect or CAPTCHA required.")
                        raise FatalError("Login failed: Still on login page")
                    else:
                        print("[ERROR] Login failed - unable to detect successful login. This could be due to:")
                        print("         • CAPTCHA/MFA challenge")
                        print("         • Invalid credentials") 
                        print("         • LinkedIn UI changes")
                        print("         • Rate limiting")
                        raise RetryableError("Login detection failed - may be temporary")
                
            except RetryableError as e:
                error_msg = str(e)
                # If we're in the middle of manual login, let the error propagate
                # Otherwise handle it normally
                if "manual login" in error_msg.lower():
                    raise e
                logger.error(f"Login failed: {e}")
                if config.DEBUG:
                    print(f"[DEBUG] Current URL: {page.url}")
                    print(f"[DEBUG] Page title: {page.title()}")
                    print("[DEBUG] Press Enter to continue or Ctrl+C to exit...")
                    input()
                raise e
            except FatalError as e:
                logger.error(f"Login failed: {e}")
                if config.DEBUG:
                    print(f"[DEBUG] Current URL: {page.url}")
                    print(f"[DEBUG] Page title: {page.title()}")
                    print("[DEBUG] Press Enter to continue or Ctrl+C to exit...")
                    input()
                raise e
            except Exception as e:
                logger.error(f"Unexpected error during login: {e}")
                raise RetryableError(f"Unexpected login error: {e}")
            
            # Save cookies after successful login
            if login_detected:
                try:
                    # Wait a moment for all cookies to be set
                    time.sleep(2)
                    
                    cookies = context.cookies()
                    # Convert to dict if needed
                    cookies_dict = [dict(c) for c in cookies]
                    
                    # Filter to only LinkedIn cookies for security
                    linkedin_cookies = [
                        c for c in cookies_dict 
                        if 'linkedin.com' in c.get('domain', '') or 'linkedin.com' in c.get('url', '')
                    ]
                    
                    if linkedin_cookies:
                        cookie_manager.save_cookies(linkedin_cookies)
                        print(f"[INFO] Saved {len(linkedin_cookies)} LinkedIn session cookies")
                    else:
                        logger.warning("No LinkedIn cookies found to save")
                        
                except Exception as e:
                    logger.warning(f"Failed to save cookies: {e}")
                    print(f"[WARN] Could not save cookies for future sessions: {e}")

        #  GO TO JOBS PAGE FIRST (like before)
        print("[INFO] Navigating to LinkedIn Jobs page initially...")
        
        # Debug pause before navigation
        if config.DEBUG:
            print("[DEBUG] ⏸️  About to navigate to LinkedIn Jobs page")
            print("[DEBUG] Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        
        # Navigate to LinkedIn Jobs page first
        try:
            page.goto("https://www.linkedin.com/jobs/", timeout=config.TIMEOUTS["search_page"], wait_until="domcontentloaded")
            print("[INFO] Successfully navigated to LinkedIn Jobs page")
            
            # Debug pause after initial navigation
            if config.DEBUG:
                print("[DEBUG] ⏸️  Successfully navigated to LinkedIn Jobs page")
                print(f"[DEBUG] Current URL: {page.url}")
                print(f"[DEBUG] Page title: {page.title()}")
                print("[DEBUG] Press Enter to continue to job search...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("[DEBUG] Continuing automatically...")
                    
        except Exception as e:
            print(f"[WARN] Failed to navigate to LinkedIn Jobs page: {e}")
            print("[INFO] Continuing with direct search URL navigation...")
        
        #  GO TO SEARCH PAGE 
        print(f"[INFO] Navigating to job search URL: {search_url}")
        
        # Debug pause before search navigation
        if config.DEBUG:
            print("[DEBUG] ⏸️  About to navigate to specific job search URL")
            print(f"[DEBUG] Search URL: {search_url}")
            print("[DEBUG] Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        
        # Enhanced navigation with retry logic and error handling
        navigation_success = False
        max_navigation_attempts = 3
        
        for attempt in range(max_navigation_attempts):
            try:
                print(f"[INFO] Navigation attempt {attempt + 1}/{max_navigation_attempts}")
                
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    delay = 2 + (attempt * 2)  # 2s, 4s, 6s delays
                    print(f"[INFO] Waiting {delay}s before retry...")
                    time.sleep(delay)
                
                # Try to navigate to the search page
                page.goto(search_url, timeout=config.TIMEOUTS["search_page"], wait_until="domcontentloaded")
                
                # Verify we're on the correct page
                current_url = page.url
                if "linkedin.com/jobs" in current_url or "linkedin.com/search" in current_url:
                    print(f"[INFO] Successfully navigated to job search page: {current_url}")
                    navigation_success = True
                    break
                else:
                    print(f"[WARN] Unexpected URL after navigation: {current_url}")
                    if attempt < max_navigation_attempts - 1:
                        print(f"[INFO] Retrying navigation...")
                        continue
                    else:
                        print(f"[ERROR] Failed to reach job search page after {max_navigation_attempts} attempts")
                        raise RetryableError("Failed to navigate to job search page")
                        
            except PlaywrightTimeout as e:
                print(f"[WARN] Navigation timeout on attempt {attempt + 1}: {e}")
                if attempt < max_navigation_attempts - 1:
                    print(f"[INFO] Retrying navigation...")
                    continue
                else:
                    print(f"[ERROR] Navigation failed after {max_navigation_attempts} attempts due to timeout")
                    raise RetryableError(f"Navigation timeout: {e}")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"[WARN] Navigation error on attempt {attempt + 1}: {error_msg}")
                
                # Check for specific error types
                if "ERR_HTTP_RESPONSE_CODE_FAILURE" in error_msg:
                    print(f"[INFO] LinkedIn returned HTTP error - likely anti-bot protection")
                    print(f"[INFO] This may be due to:")
                    print(f"  • LinkedIn's anti-bot measures")
                    print(f"  • Rate limiting from too many requests")
                    print(f"  • IP address being flagged")
                    print(f"  • Browser fingerprint detection")
                    
                    if attempt < max_navigation_attempts - 1:
                        print(f"[INFO] Retrying with longer delay...")
                        # Add extra delay for anti-bot protection
                        extra_delay = 5 + (attempt * 3)  # 5s, 8s, 11s delays
                        print(f"[INFO] Adding extra {extra_delay}s delay for anti-bot protection...")
                        time.sleep(extra_delay)
                        continue
                    else:
                        print(f"[ERROR] LinkedIn blocked navigation after {max_navigation_attempts} attempts")
                        print(f"[ERROR] Suggestions:")
                        print(f"  • Wait 10-15 minutes before trying again")
                        print(f"  • Try using a different IP address/VPN")
                        print(f"  • Log into LinkedIn manually first to verify account")
                        print(f"  • Check if LinkedIn has flagged your account")
                        raise RetryableError("LinkedIn blocked navigation - try again later")
                        
                elif "net::ERR_" in error_msg:
                    print(f"[INFO] Network error detected: {error_msg}")
                    if attempt < max_navigation_attempts - 1:
                        print(f"[INFO] Retrying navigation...")
                        continue
                    else:
                        print(f"[ERROR] Network error persisted after {max_navigation_attempts} attempts")
                        raise RetryableError(f"Network error: {e}")
                        
                else:
                    print(f"[ERROR] Unexpected navigation error: {error_msg}")
                    if attempt < max_navigation_attempts - 1:
                        print(f"[INFO] Retrying navigation...")
                        continue
                    else:
                        raise RetryableError(f"Navigation failed: {e}")
        
        if not navigation_success:
            print(f"[ERROR] Failed to navigate to job search page after all attempts")
            print(f"[INFO] Attempting fallback navigation strategy...")
            
            # Fallback: Try navigating to LinkedIn home first, then to jobs
            try:
                print(f"[INFO] Fallback: Navigating to LinkedIn home page first...")
                page.goto("https://www.linkedin.com/feed/", timeout=config.TIMEOUTS["search_page"])
                time.sleep(3)  # Wait for page to load
                
                print(f"[INFO] Fallback: Now navigating to job search...")
                page.goto(search_url, timeout=config.TIMEOUTS["search_page"])
                
                current_url = page.url
                if "linkedin.com/jobs" in current_url or "linkedin.com/search" in current_url:
                    print(f"[INFO] Fallback navigation successful: {current_url}")
                    navigation_success = True
                else:
                    print(f"[ERROR] Fallback navigation also failed: {current_url}")
                    raise RetryableError("All navigation attempts failed")
                    
            except Exception as fallback_error:
                print(f"[ERROR] Fallback navigation failed: {fallback_error}")
                raise RetryableError("Navigation failed after all retry attempts and fallback")
        
        if not navigation_success:
            print(f"[ERROR] Failed to navigate to job search page after all attempts")
            raise RetryableError("Navigation failed after all retry attempts")
        
        if config.DEBUG:
            print(f"[DEBUG] Current URL: {page.url}")
            print(f"[DEBUG] Page title: {page.title()}")

        #  COLLECT JOB LINKS 
        print("[INFO] Collecting job links...")
        
        # Debug pause before job collection
        if config.DEBUG:
            print("[DEBUG] ⏸️  About to start collecting job links")
            print(f"[DEBUG] Max jobs: {max_jobs}")
            print("[DEBUG] Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        
        job_links = collect_job_links_with_pagination(page, search_url, max_jobs=max_jobs)
        if not job_links:
            print("[WARN] No job links found")
            return []
        
        print(f"[INFO] Found {len(job_links)} job links")
        
        # Debug pause after job collection
        if config.DEBUG:
            print("[DEBUG] ⏸️  Job collection completed")
            print(f"[DEBUG] Found {len(job_links)} job links")
            print("[DEBUG] Press Enter to continue with job processing...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")

        #  LOAD PERSONAL INFO 
        print("[INFO] Loading personal information...")
        try:
            with open(personal_info_path, "r", encoding="utf-8") as f:
                personal_info = yaml.safe_load(f)
        except Exception as e:
            print(f"[ERROR] Could not load {personal_info_path}: {e}")
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
        
        # Debug pause before starting job processing loop
        if config.DEBUG:
            print("[DEBUG] ⏸️  About to start job processing loop")
            print(f"[DEBUG] Will process {len(job_links)} jobs")
            print("[DEBUG] Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        
        for idx, job_url in enumerate(job_links, start=1):
            # Check if browser was manually closed
            if browser_monitor.should_exit():
                print("\n[INFO] Browser was manually closed - stopping job processing")
                break
                
            print(f"\n[INFO] [{idx}/{len(job_links)}] Opening job page: {job_url}")
            
            # Debug pause before each job
            if config.DEBUG:
                print(f"[DEBUG] ⏸️  About to process job {idx}/{len(job_links)}")
                print(f"[DEBUG] Job URL: {job_url}")
                print("[DEBUG] Press Enter to continue...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("[DEBUG] Continuing automatically...")

            with ErrorContext(f"Processing job {idx}/{len(job_links)}", page) as job_context:
                job_context.add_context("job_url", job_url)
                job_context.add_context("job_index", idx)
                
                try:
                    # [OK] Check if browser was manually closed
                    if browser_monitor.should_exit():
                        print("\n[INFO] Browser was manually closed - stopping job processing")
                        break
                        
                    # [OK] Check if browser context is still valid
                    try:
                        # Test if context is still valid by checking if we can create a page
                        job_page = context.new_page()
                    except Exception as context_error:
                        print(f"[ERROR] Browser context is no longer valid: {context_error}")
                        print(f"[ERROR] Cannot process more jobs. Stopping.")
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
                            print(f"  [INFO] Waiting {delay:.1f}s (increased due to {scrape_jobs_from_search.consecutive_failures} recent failure(s))...")
                        else:
                            delay = random.uniform(base_min, base_max)
                            print(f"  [INFO] Waiting {delay:.1f}s to avoid rate limiting...")
                        time.sleep(delay)
                    
                    try:
                        job_page.goto(job_url, timeout=config.TIMEOUTS["job_page"])
                    except TargetClosedError:
                        print(f"[WARN] LinkedIn closed the tab unexpectedly for {job_url}. Skipping.")
                        job_context.add_context("error", "TargetClosedError")
                        continue
                    except PlaywrightTimeout:
                        print(f"[WARN] Timeout loading {job_url}. Skipping.")
                        
                        # Track timeout failures for adaptive delay
                        if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                            scrape_jobs_from_search.consecutive_failures = 0
                        scrape_jobs_from_search.consecutive_failures += 1
                        
                        # Wait longer after timeout
                        wait_time = random.uniform(*config.DELAYS["graphql_failure_wait"])
                        print(f"  [WARN] Waiting {wait_time:.1f}s after timeout...")
                        time.sleep(wait_time)
                        
                        job_context.add_context("error", "PlaywrightTimeout")
                        continue
                    except Exception as e:
                        error_msg = str(e)
                        if "ERR_HTTP_RESPONSE_CODE_FAILURE" in error_msg:
                            print(f"[WARN] LinkedIn rate limiting detected for {job_url}. Skipping.")
                            
                            # Track rate limit failures for adaptive delay
                            if not hasattr(scrape_jobs_from_search, 'consecutive_failures'):
                                scrape_jobs_from_search.consecutive_failures = 0
                            scrape_jobs_from_search.consecutive_failures += 2  # Rate limits are more serious
                            
                            # Wait longer after rate limit detection
                            wait_time = random.uniform(*config.DELAYS["rate_limit_wait"])
                            print(f"  [WARN] Waiting {wait_time:.1f}s after rate limit detection...")
                            time.sleep(wait_time)
                            
                            job_context.add_context("error", "RateLimited")
                            continue
                        elif "net::ERR_" in error_msg:
                            print(f"[WARN] Network error for {job_url}: {error_msg}. Skipping.")
                            job_context.add_context("error", f"NetworkError: {error_msg}")
                            continue
                        else:
                            print(f"[WARN] Unexpected error loading {job_url}: {error_msg}. Skipping.")
                            job_context.add_context("error", f"UnexpectedError: {error_msg}")
                            continue

                    # [OK] Detect expired/unavailable job
                    if job_page.locator(config.LINKEDIN_SELECTORS["job_detail"]["unavailable"]).count():
                        print(f"[INFO] Job {job_url} is unavailable or expired. Skipping.")
                        job_page.close()
                        continue

                    job_page.wait_for_selector("h1", timeout=config.TIMEOUTS["job_title"])
                    
                    # Simulate human viewing the page
                    HumanBehavior.simulate_viewport_movement(job_page)
                    HumanBehavior.simulate_hesitation(0.5, 1.2)  # Pause to "read" job title
                    
                    # Enhanced GraphQL failure detection and handling
                    if config.DEBUG:
                        print(f"  [DEBUG] Checking for GraphQL loading indicators...")
                    
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
                                print(f"  [ERROR] GraphQL error detected: {error_selector}")
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
                                print(f"  [DEBUG] No GraphQL loading indicators detected")
                            break
                        else:
                            if config.DEBUG:
                                print(f"  [DEBUG] GraphQL loading indicators still present, waiting...")
                            time.sleep(0.5)
                    
                    # Handle GraphQL errors
                    if graphql_error_detected:
                        print(f"  [ERROR] GraphQL error detected on job page - likely bot detection")
                        print(f"  [INFO] This may indicate:")
                        print(f"    • LinkedIn has detected automated behavior")
                        print(f"    • Session cookies are invalid/expired")
                        print(f"    • Rate limiting is in effect")
                        print(f"    • IP address is flagged")
                        
                        # Try to recover session by refreshing cookies
                        print(f"  [INFO] Attempting session recovery...")
                        try:
                            cookie_refreshed = cookie_manager.refresh_cookies_if_needed(context, job_page)
                            if cookie_refreshed:
                                print(f"  [INFO] Session cookies refreshed - retrying job page")
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

                    # [OK] LLM summary + skills with error handling
                    try:
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
                        from src.error_handler import APIFailureHandler
                        pdf_path = build_resume(payload)
                        
                        # Verify PDF was created successfully
                        if not pdf_path or not os.path.exists(pdf_path):
                            raise Exception("PDF file was not created or is not accessible")
                        
                        print(f"[INFO] Resume generated: {pdf_path}")
                        job_context.add_context("resume_path", pdf_path)
                        
                    except Exception as e:
                        print(f"  [ERROR] Resume generation failed for {title} @ {company}: {e}")
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
                        if config.DEBUG:
                            print("\n[DEBUG] About to attempt LinkedIn Easy Apply...")
                        print("  [INFO] Attempting LinkedIn Easy Apply")
                        
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
                    job_context.add_context("error", str(e))
                    logger.error(f"Job processing failed: {e}")
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
        
        # Cleanup browser configuration
        browser_config.cleanup()
        
        return jobs_data
