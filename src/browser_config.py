# src/browser_config.py

import os
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Browser, BrowserContext, sync_playwright
from src.logging_config import get_logger, log_function_call, log_error_context
from src.debug_config import get_debug_config, is_debug_mode, get_debug_browser_args

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
        self.stealth_session = None
        
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
        Get enhanced browser arguments for stealth operation and automation detection avoidance.
        """
        args = [
            # Core stealth arguments - enhanced for better detection avoidance
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
            
            # Enhanced automation detection avoidance
            '--disable-automation',
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-extensions-except',
            '--disable-plugins-discovery',
            '--disable-component-extensions-with-background-pages',
            
            # Extension and plugin blocking
            '--disable-extensions',
            '--disable-extensions-file-access-check',
            '--disable-extensions-http-throttling',
            
            # Privacy and tracking prevention
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-background-networking',
            '--disable-sync',
            '--disable-background-mode',
            
            # Resource optimization (but keep JavaScript for LinkedIn GraphQL)
            # Note: Disabling images can cause GraphQL hydration issues
            # '--disable-images',  # Commented out to prevent GraphQL issues
            '--disable-javascript-harmony-shipping',
            '--disable-java',
            '--disable-flash',
            
            # Network and performance
            '--aggressive-cache-discard',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            
            # Enhanced security and detection avoidance
            '--disable-client-side-phishing-detection',
            '--disable-domain-reliability',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync-preferences',
            '--disable-web-resources',
            '--no-pings',
            '--no-zygote',
            '--use-mock-keychain',
            
            # Enhanced fingerprinting protection
            '--disable-features=VizDisplayCompositor',
            '--disable-features=WebRtcHideLocalIpsWithMdns',
            '--disable-features=WebRtcUseMinMaxVEADimensions',
            '--disable-features=WebRtcUseEchoCanceller3',
            '--disable-features=WebRtcUseMinMaxVEADimensions',
            '--disable-features=WebRtcUseEchoCanceller3',
            
            # Memory and performance optimizations
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            
            # User agent and fingerprinting - updated to more recent version
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        ]
        
        # Add headless mode if requested
        if self.headless:
            args.append('--headless=new')
        
        # Add debug-specific arguments if in debug mode
        if is_debug_mode():
            debug_args = get_debug_browser_args()
            args.extend(debug_args)
            logger.info(f"Added {len(debug_args)} debug-specific browser arguments")
        
        return args
    
    def get_realistic_user_agent(self) -> str:
        """Get a realistic user agent string matching the browser args."""
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    
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
        Get enhanced JavaScript code to inject for stealth operation.
        This helps avoid detection by removing automation indicators and masking browser fingerprint.
        """
        return """
        // Enhanced automation detection avoidance
        
        // Remove webdriver property completely
        Object.defineProperty(navigator, 'webdriver', {
            get: function() { return undefined; }
        });
        
        // Remove automation indicators
        delete window.navigator.webdriver;
        delete window.navigator.__webdriver_evaluate;
        delete window.navigator.__webdriver_script_function;
        delete window.navigator.__webdriver_script_func;
        delete window.navigator.__webdriver_script_fn;
        delete window.navigator.__fxdriver_evaluate;
        delete window.navigator.__driver_unwrapped;
        delete window.navigator.__webdriver_unwrapped;
        delete window.navigator.__driver_evaluate;
        delete window.navigator.__selenium_unwrapped;
        delete window.navigator.__fxdriver_unwrapped;
        
        // Mock realistic plugins
        Object.defineProperty(navigator, 'plugins', {
            get: function() { 
                return [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', filename: 'internal-nacl-plugin'}
                ]; 
            }
        });
        
        // Mock realistic languages
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en']; }
        });
        
        // Mock chrome runtime with realistic properties
        window.chrome = {
            runtime: {
                onConnect: undefined,
                onMessage: undefined,
                connect: function() {},
                sendMessage: function() {}
            },
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: 'disabled',
                    INSTALLED: 'installed',
                    NOT_INSTALLED: 'not_installed'
                },
                RunningState: {
                    CANNOT_RUN: 'cannot_run',
                    READY_TO_RUN: 'ready_to_run',
                    RUNNING: 'running'
                }
            }
        };
        
        // Mock permissions API
        if (window.navigator && window.navigator.permissions && window.navigator.permissions.query) {
            var originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = function(parameters) {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
        }
        
        // Mock realistic screen properties
        Object.defineProperty(screen, 'availHeight', {
            get: function() { return 1040; }
        });
        Object.defineProperty(screen, 'availWidth', {
            get: function() { return 1920; }
        });
        Object.defineProperty(screen, 'colorDepth', {
            get: function() { return 24; }
        });
        Object.defineProperty(screen, 'pixelDepth', {
            get: function() { return 24; }
        });
        
        // Mock realistic hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: function() { return 8; }
        });
        
        // Mock realistic device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: function() { return 8; }
        });
        
        // Mock realistic connection
        Object.defineProperty(navigator, 'connection', {
            get: function() { 
                return {
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                }; 
            }
        });
        
        // Mock realistic battery API
        if (navigator.getBattery) {
            navigator.getBattery = function() {
                return Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.8
                });
            };
        }
        
        // Enhanced console error filtering
        if (console && console.error) {
            var originalError = console.error;
            console.error = function() {
                var message = Array.prototype.join.call(arguments, ' ');
                if (message.includes('Failed to load resource') && 
                    (message.includes('chrome-extension://') || 
                     message.includes('net::ERR_BLOCKED_BY_CLIENT') ||
                     message.includes('net::ERR_FAILED'))) {
                    return;
                }
                if (message.includes('BooleanExpression with operator "numericGreaterThan"') ||
                    message.includes('EventSource response has a Content-Type') ||
                    message.includes('Content contains tags or attributes that are not allowed') ||
                    message.includes('HTML sanitized:') ||
                    message.includes('Attribute exception.tags of type object') ||
                    message.includes('TypeError: network error') ||
                    message.includes('grecaptcha.render is not a function') ||
                    message.includes('Refused to execute script') ||
                    message.includes('Refused to frame') ||
                    message.includes('GraphQLInvalidServerResponseError') ||
                    message.includes('Cannot read properties of undefined') ||
                    message.includes('_normalizeProjection') ||
                    message.includes('voyagerIdentityDashProfiles') ||
                    message.includes('voyagerDashMySettings') ||
                    message.includes('voyagerFeedDashThirdPartyIdSyncs') ||
                    message.includes('voyagerJobsDashJobPostingDetailSections')) {
                    return;
                }
                originalError.apply(console, arguments);
            };
        }
        
        // Enhanced console warning filtering
        if (console && console.warn) {
            var originalWarn = console.warn;
            console.warn = function() {
                var message = Array.prototype.join.call(arguments, ' ');
                if (message.includes('Third-party cookie will be blocked') ||
                    message.includes('BooleanExpression with operator "numericGreaterThan"') ||
                    message.includes('EventSource response has a Content-Type') ||
                    message.includes('Content contains tags or attributes that are not allowed') ||
                    message.includes('HTML sanitized:') ||
                    message.includes('Attribute exception.tags of type object') ||
                    message.includes('Refused to frame') ||
                    message.includes('Content Security Policy')) {
                    return;
                }
                originalWarn.apply(console, arguments);
            };
        }
        
        // Mock realistic timezone
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
            value: function() {
                return {
                    locale: 'en-US',
                    calendar: 'gregory',
                    numberingSystem: 'latn',
                    timeZone: 'America/New_York'
                };
            }
        });
        
        // Mock realistic canvas fingerprint
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            if (type === '2d') {
                const context = getContext.call(this, type);
                const originalFillText = context.fillText;
                context.fillText = function() {
                    // Add slight randomness to canvas fingerprint
                    const args = Array.from(arguments);
                    if (args.length >= 3) {
                        args[1] += Math.random() * 0.1;
                        args[2] += Math.random() * 0.1;
                    }
                    return originalFillText.apply(this, args);
                };
                return context;
            }
            return getContext.call(this, type);
        };
        
        // Mock realistic WebGL fingerprint
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Intel Inc.';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'Intel(R) Iris(TM) Graphics 6100';
            }
            return getParameter.call(this, parameter);
        };
        
        // Remove automation-related properties from window
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
        
        // Mock realistic media devices
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices = function() {
                return Promise.resolve([
                    {deviceId: 'default', groupId: 'group1', kind: 'audioinput', label: 'Default - Microphone'},
                    {deviceId: 'default', groupId: 'group1', kind: 'audiooutput', label: 'Default - Speaker'},
                    {deviceId: 'default', groupId: 'group1', kind: 'videoinput', label: 'Default - Camera'}
                ]);
            };
        }
        """
    
    def get_enhanced_stealth_script(self) -> str:
        """
        Get enhanced JavaScript code to inject for advanced stealth operation.
        This includes the original stealth script plus additional features.
        """
        base_script = self.get_stealth_script()
        
        enhanced_additions = """
        // Enhanced stealth features for session management
        
        // Add session continuity markers
        if (!window.stealthSessionData) {
            window.stealthSessionData = {
                sessionId: '""" + str(uuid.uuid4()) + """',
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                fingerprint: null
            };
        }
        
        // Enhanced automation detection avoidance
        Object.defineProperty(window, 'chrome', {
            get: function() {
                return {
                    runtime: {
                        onConnect: undefined,
                        onMessage: undefined,
                        connect: function() {},
                        sendMessage: function() {}
                    },
                    app: {
                        isInstalled: false
                    }
                };
            }
        });
        
        // Mock realistic performance timing
        const originalNow = performance.now;
        performance.now = function() {
            return originalNow.call(this) + Math.random() * 0.1;
        };
        
        // Enhanced mouse event simulation
        let mouseEvents = [];
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type.startsWith('mouse')) {
                mouseEvents.push({type, timestamp: Date.now()});
            }
            return originalAddEventListener.call(this, type, listener, options);
        };
        
        // Simulate realistic scroll behavior
        let scrollEvents = [];
        const originalScrollTo = window.scrollTo;
        window.scrollTo = function(x, y) {
            scrollEvents.push({x, y, timestamp: Date.now()});
            return originalScrollTo.call(this, x, y);
        };
        
        // Enhanced console filtering
        const originalConsoleLog = console.log;
        console.log = function() {
            const message = Array.prototype.join.call(arguments, ' ');
            if (message.includes('stealth') || message.includes('automation')) {
                return;
            }
            return originalConsoleLog.apply(console, arguments);
        };
        
        // Add realistic browser behavior markers
        window.stealthBehaviorMarkers = {
            mouseEvents: mouseEvents,
            scrollEvents: scrollEvents,
            lastActivity: Date.now(),
            sessionStart: Date.now()
        };
        
        console.log('Enhanced stealth script loaded successfully');
        """
        
        return base_script + enhanced_additions
    
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
    
    def get_stealth_config(self) -> Dict[str, Any]:
        """
        Get stealth configuration from app config.
        
        Returns:
            Dictionary containing stealth configuration
        """
        try:
            from src.config import get_config_manager
            config_manager = get_config_manager()
            app_config = config_manager.config
            
            # Extract stealth config
            stealth_config = app_config.stealth_config.dict()
            
            # Add profile directory path
            stealth_config['profile_dir'] = str(Path('stealth_profiles'))
            
            logger.debug("Retrieved stealth configuration", 
                        config_keys=list(stealth_config.keys()))
            
            return stealth_config
            
        except Exception as e:
            logger.warning("Could not retrieve stealth config, using defaults", error=str(e))
            # Fallback to default configuration
            return {
                'profile_dir': 'stealth_profiles',
                'enable_stealth_session': True,
                'enable_personality_modeling': True,
                'enable_fatigue_simulation': True,
                'enable_interruption_simulation': True,
                'enable_realistic_profiles': True,
                'enable_session_fingerprinting': True,
                'enable_behavioral_evolution': True,
                'enable_distraction_simulation': True,
                'session_persistence_method': 'localStorage',
                'session_cleanup_interval': 3600,
                'personality_consistency_level': 0.8,
                'behavioral_variance': 0.2,
                'profile_history_length': 100,
                'profile_update_frequency': 86400,
                'max_session_duration': 7200,
                'session_save_interval': 300,
                'profile_cleanup_age_days': 30
            }

    def create_context_with_stealth_session(self, browser: Browser) -> BrowserContext:
        """
        Create browser context with complete stealth session management.
        
        Args:
            browser: Playwright browser object
            
        Returns:
            Browser context with stealth session management
        """
        try:
            # Initialize stealth session manager
            from src.stealth_integration import StealthIntegration
            
            # Get stealth configuration
            stealth_config = self.get_stealth_config()
            
            self.stealth_session = StealthIntegration(stealth_config)
            
            # Get realistic user agent and headers
            user_agent = self.get_realistic_user_agent()
            headers = self.get_stealth_headers()
            
            # Create context with enhanced stealth settings
            self.context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers=headers,
                ignore_https_errors=True,
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
            )
            
            # Add enhanced stealth script first
            stealth_script = self.get_enhanced_stealth_script()
            self.context.add_init_script(stealth_script)
            
            # Set up request interception
            self.context.route("**/*", self._handle_route)
            
            # Initialize stealth session after context is fully set up
            try:
                self.stealth_session.initialize_stealth_session(self.context)
                logger.info("Stealth session initialized successfully")
            except Exception as stealth_error:
                logger.warning("Stealth session initialization failed, continuing without stealth", error=str(stealth_error))
                # Continue without stealth session - the context is still valid
                self.stealth_session = None
            
            logger.info("Browser context created with enhanced stealth session management")
            return self.context
            
        except Exception as e:
            logger.error(f"Failed to create context with stealth session: {e}")
            raise
    
    def _handle_route(self, route, request):
        """
        Handle route requests to gracefully deal with blocked resources.
        Uses debug configuration for less aggressive blocking in debug mode.
        """
        try:
            url = request.url
            debug_config = get_debug_config()
            route_config = debug_config.get_debug_route_handling()
            
            # Block problematic extensions and resources
            if route_config.get('block_extensions', True) and any(blocked in url for blocked in [
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
            # Note: Be more selective to avoid blocking LinkedIn's internal APIs
            if route_config.get('block_trackers', True) and any(tracker in url for tracker in [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com/tr',
                'doubleclick.net',
                'googlesyndication.com',
            ]) and 'linkedin.com' not in url:
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
            
            # In debug mode, allow all LinkedIn resources
            if route_config.get('allow_all_linkedin', False) and 'linkedin.com' in url:
                logger.debug(f"Allowing LinkedIn resource (debug mode): {url}")
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
