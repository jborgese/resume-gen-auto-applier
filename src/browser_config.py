# src/browser_config.py

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Browser, BrowserContext, sync_playwright
from src.logging_config import get_logger, log_function_call, log_error_context

logger = get_logger(__name__)

class EnhancedBrowserConfig:
    """
    Enhanced browser configuration for LinkedIn automation with:
    - Clean browser profile
    - Extension blocking
    - Headless mode support
    - Better error handling for blocked resources
    - Stealth features to avoid detection
    """
    
    def __init__(self, debug: bool = False, headless: bool = False):
        self.debug = debug
        self.headless = headless
        self.temp_profile_dir = None
        self.browser = None
        self.context = None
        
    def create_clean_profile(self) -> str:
        """
        Create a clean, isolated browser profile directory.
        This ensures no extensions or cached data interfere with automation.
        Note: This is currently not used as we use regular browser launch with clean args.
        """
        try:
            # Create a temporary directory for the browser profile
            self.temp_profile_dir = tempfile.mkdtemp(prefix="linkedin_automation_")
            logger.info(f"Created clean browser profile: {self.temp_profile_dir}")
            return self.temp_profile_dir
        except Exception as e:
            logger.error(f"Failed to create clean profile: {e}")
            raise
    
    def get_stealth_args(self) -> List[str]:
        """
        Get browser arguments for stealth operation and extension blocking.
        """
        args = [
            # Core stealth arguments
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            
            # Extension and plugin blocking
            '--disable-extensions',
            '--disable-extensions-file-access-check',
            '--disable-extensions-http-throttling',
            '--disable-extensions-except',
            # REMOVED: '--disable-plugins' - may interfere with LinkedIn functionality
            # REMOVED: '--disable-plugins-discovery' - may interfere with LinkedIn functionality
            
            # Privacy and tracking prevention
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-background-networking',
            '--disable-sync',
            '--disable-background-mode',
            
            # Resource optimization (but keep JavaScript for LinkedIn GraphQL)
            '--disable-images',  # Block images to reduce resource usage
            '--disable-javascript-harmony-shipping',
            # REMOVED: '--disable-javascript' - LinkedIn requires JavaScript for GraphQL
            '--disable-java',
            '--disable-flash',
            # REMOVED: '--disable-plugins' - may interfere with LinkedIn functionality
            
            # Network and performance
            '--aggressive-cache-discard',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            
            # Security and detection avoidance
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-domain-reliability',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync-preferences',
            '--disable-web-resources',
            '--no-pings',
            '--no-zygote',
            '--use-mock-keychain',
            
            # User agent and fingerprinting
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Note: user-data-dir is handled via launch_persistent_context if needed
        # For now, we'll use regular launch with clean args
        
        # Add headless mode if requested
        if self.headless:
            args.append('--headless=new')
        
        return args
    
    def get_realistic_user_agent(self) -> str:
        """Get a realistic user agent string."""
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def get_stealth_headers(self) -> Dict[str, str]:
        """Get realistic HTTP headers to avoid detection."""
        return {
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    def get_stealth_script(self) -> str:
        """
        Get JavaScript code to inject for stealth operation.
        This helps avoid detection by removing automation indicators.
        """
        return """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: function() { return undefined; }
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: function() { return [1, 2, 3, 4, 5]; }
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en']; }
        });
        
        // Mock chrome runtime
        window.chrome = {
            runtime: {}
        };
        
        // Mock permissions
        if (window.navigator && window.navigator.permissions && window.navigator.permissions.query) {
            var originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = function(parameters) {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
        }
        
        // Block resource loading errors from console
        if (console && console.error) {
            var originalError = console.error;
            console.error = function() {
                var message = Array.prototype.join.call(arguments, ' ');
                if (message.includes('Failed to load resource') && 
                    (message.includes('chrome-extension://') || 
                     message.includes('net::ERR_BLOCKED_BY_CLIENT'))) {
                    return;
                }
                if (message.includes('BooleanExpression with operator "numericGreaterThan"') ||
                    message.includes('EventSource response has a Content-Type') ||
                    message.includes('Content contains tags or attributes that are not allowed') ||
                    message.includes('HTML sanitized:') ||
                    message.includes('Attribute exception.tags of type object') ||
                    message.includes('TypeError: network error')) {
                    return;
                }
                originalError.apply(console, arguments);
            };
        }
        
        // Block third-party cookie warnings
        if (console && console.warn) {
            var originalWarn = console.warn;
            console.warn = function() {
                var message = Array.prototype.join.call(arguments, ' ');
                if (message.includes('Third-party cookie will be blocked') ||
                    message.includes('BooleanExpression with operator "numericGreaterThan"') ||
                    message.includes('EventSource response has a Content-Type') ||
                    message.includes('Content contains tags or attributes that are not allowed') ||
                    message.includes('HTML sanitized:') ||
                    message.includes('Attribute exception.tags of type object')) {
                    return;
                }
                originalWarn.apply(console, arguments);
            };
        }
        """
    
    def launch_browser(self, playwright) -> Browser:
        """
        Launch browser with enhanced configuration.
        Uses regular launch for better compatibility.
        """
        try:
            # Get stealth arguments
            args = self.get_stealth_args()
            
            logger.info(f"Launching browser with {len(args)} stealth arguments")
            logger.debug(f"Browser args: {args[:10]}...")  # Log first 10 args
            
            # Launch browser with clean configuration
            self.browser = playwright.chromium.launch(
                headless=self.headless,
                args=args
            )
            
            logger.info("Browser launched successfully")
            return self.browser
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    def launch_persistent_browser(self, playwright) -> tuple[Browser, BrowserContext]:
        """
        Launch browser with persistent context for clean profiles.
        This is an alternative method that provides better isolation.
        """
        try:
            # Create clean profile
            self.create_clean_profile()
            
            # Get stealth arguments (without user-data-dir)
            args = self.get_stealth_args()
            
            logger.info(f"Launching persistent browser with {len(args)} stealth arguments")
            logger.debug(f"Browser args: {args[:10]}...")  # Log first 10 args
            
            # Launch browser with persistent context
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=self.temp_profile_dir,
                headless=self.headless,
                args=args
            )
            
            # Get browser from context
            self.browser = context.browser
            self.context = context
            
            logger.info("Persistent browser launched successfully")
            return self.browser, context
            
        except Exception as e:
            logger.error(f"Failed to launch persistent browser: {e}")
            raise
    
    def create_context(self, browser: Browser) -> BrowserContext:
        """
        Create browser context with enhanced configuration.
        """
        try:
            # Get realistic user agent and headers
            user_agent = self.get_realistic_user_agent()
            headers = self.get_stealth_headers()
            
            # Create context with stealth settings
            self.context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers=headers,
                # Block resources that commonly cause issues
                ignore_https_errors=True,
                # Set realistic device metrics
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
            )
            
            # Add stealth script
            stealth_script = self.get_stealth_script()
            self.context.add_init_script(stealth_script)
            
            # Set up request interception to handle blocked resources
            self.context.route("**/*", self._handle_route)
            
            logger.info("Browser context created with stealth configuration")
            return self.context
            
        except Exception as e:
            logger.error(f"Failed to create browser context: {e}")
            raise
    
    def _handle_route(self, route, request):
        """
        Handle route requests to gracefully deal with blocked resources.
        """
        try:
            url = request.url
            
            # Block problematic extensions and resources
            if any(blocked in url for blocked in [
                'chrome-extension://',
                'moz-extension://',
                'safari-extension://',
                'chrome://',
                'about:',
            ]):
                logger.debug(f"Blocking problematic resource: {url}")
                route.abort()
                return
            
            # Block common tracking and analytics (but allow LinkedIn GraphQL)
            if any(tracker in url for tracker in [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com/tr',
                'doubleclick.net',
                'googlesyndication.com',
            ]):
                logger.debug(f"Blocking tracker: {url}")
                route.abort()
                return
            
            # Allow LinkedIn GraphQL and API endpoints
            if any(linkedin_api in url for linkedin_api in [
                'linkedin.com/voyager',
                'linkedin.com/graphql',
                'linkedin.com/api',
                'linkedin.com/voyagerApi',
            ]):
                logger.debug(f"Allowing LinkedIn API: {url}")
                route.continue_()
                return
            
            # Allow other requests to proceed
            route.continue_()
            
        except Exception as e:
            logger.debug(f"Route handling error: {e}")
            # If route handling fails, continue with the request
            try:
                route.continue_()
            except:
                pass
    
    def cleanup(self):
        """
        Clean up temporary files and resources.
        """
        try:
            if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
                shutil.rmtree(self.temp_profile_dir)
                logger.info(f"Cleaned up temporary profile: {self.temp_profile_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary profile: {e}")
        
        try:
            if self.context:
                self.context.close()
        except Exception as e:
            logger.warning(f"Failed to close context: {e}")
        
        try:
            if self.browser:
                self.browser.close()
        except Exception as e:
            logger.warning(f"Failed to close browser: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
