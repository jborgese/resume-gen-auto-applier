# src/stealth_session_manager.py

import json
import time
import random
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from playwright.sync_api import Page, BrowserContext
from src.logging_config import get_logger

logger = get_logger(__name__)


class StealthSessionManager:
    """
    Central coordinator for stealth session management that avoids automation detection by:
    1. Simulating realistic user behavior patterns
    2. Creating persistent browser profiles with realistic data
    3. Implementing session state without obvious automation markers
    4. Using behavioral patterns instead of cookie persistence
    """
    
    def __init__(self, profile_dir: str = "stealth_profiles"):
        """
        Initialize the stealth session manager.
        
        Args:
            profile_dir: Directory to store stealth profile data
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(exist_ok=True)
        
        # Core components
        self.user_personality = self._generate_user_personality()
        self.session_state = {}
        self.browsing_history = []
        self.session_fingerprint = None
        self.session_id = self._generate_session_id()
        
        # Session tracking
        self.session_start_time = time.time()
        self.activity_history = []
        self.interaction_count = 0
        
        logger.info("StealthSessionManager initialized", 
                   session_id=self.session_id,
                   profile_dir=str(self.profile_dir))
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def _generate_user_personality(self) -> Dict[str, Any]:
        """
        Generate a consistent user personality for this session.
        This personality will remain consistent across the session.
        """
        personality = {
            # Typing and reading characteristics
            'typing_speed_wpm': random.uniform(30, 60),
            'reading_speed_wpm': random.uniform(150, 300),
            'hesitation_level': random.uniform(0.1, 0.3),
            'error_rate': random.uniform(0.02, 0.05),
            
            # Interaction style
            'interaction_style': random.choice(['careful', 'quick', 'methodical']),
            'distraction_level': random.uniform(0.05, 0.2),
            'preferred_scroll_speed': random.uniform(200, 500),
            'click_accuracy': random.uniform(0.85, 0.98),
            
            # Decision making
            'decision_speed': random.uniform(0.5, 2.0),
            'risk_tolerance': random.uniform(0.1, 0.9),
            'attention_span': random.uniform(5, 30),
            'multitasking_ability': random.uniform(0.1, 0.8),
            
            # Behavioral patterns
            'preferred_click_delay': random.uniform(0.1, 0.5),
            'scroll_pause_frequency': random.uniform(0.1, 0.4),
            'form_filling_style': random.choice(['sequential', 'random', 'careful']),
            'error_correction_style': random.choice(['immediate', 'batch', 'ignore']),
            
            # Session characteristics
            'session_fatigue_rate': random.uniform(0.01, 0.05),
            'break_frequency': random.uniform(0.05, 0.2),
            'focus_duration': random.uniform(10, 45),
        }
        
        logger.debug("Generated user personality", personality_keys=list(personality.keys()))
        return personality
    
    def create_realistic_browser_profile(self, context: BrowserContext) -> None:
        """
        Create a realistic browser profile with browsing history and preferences.
        
        Args:
            context: Playwright browser context to inject profile data into
        """
        try:
            # Generate realistic browsing history
            browsing_history = self._generate_realistic_browsing_history()
            
            # Generate realistic preferences
            preferences = self._generate_realistic_preferences()
            
            # Generate realistic cache data
            cache_data = self._generate_realistic_cache_data()
            
            # Generate realistic local storage data
            local_storage_data = self._generate_realistic_local_storage()
            
            # Inject all data into the browser context
            self._inject_profile_data(context, browsing_history, preferences, cache_data, local_storage_data)
            
            # Store profile data for session continuity
            self.browsing_history = browsing_history
            self.session_state['profile_data'] = {
                'browsing_history': browsing_history,
                'preferences': preferences,
                'cache_data': cache_data,
                'local_storage_data': local_storage_data
            }
            
            logger.info("Created realistic browser profile", 
                       history_items=len(browsing_history),
                       preferences_count=len(preferences),
                       cache_items=len(cache_data.get('images', [])))
                       
        except Exception as e:
            logger.error("Failed to create realistic browser profile", error=str(e))
            raise
    
    def _generate_realistic_browsing_history(self) -> List[Dict[str, Any]]:
        """Generate realistic browsing history with professional focus."""
        base_time = time.time() - (7 * 24 * 3600)  # 7 days ago
        
        history_items = []
        
        # Professional sites (70% of history)
        professional_sites = [
            {'url': 'https://www.linkedin.com/feed/', 'title': 'LinkedIn Feed'},
            {'url': 'https://www.linkedin.com/jobs/', 'title': 'LinkedIn Jobs'},
            {'url': 'https://www.linkedin.com/mynetwork/', 'title': 'LinkedIn My Network'},
            {'url': 'https://www.indeed.com/', 'title': 'Indeed Jobs'},
            {'url': 'https://www.glassdoor.com/', 'title': 'Glassdoor'},
            {'url': 'https://www.monster.com/', 'title': 'Monster Jobs'},
            {'url': 'https://github.com/', 'title': 'GitHub'},
            {'url': 'https://stackoverflow.com/', 'title': 'Stack Overflow'},
            {'url': 'https://www.coursera.org/', 'title': 'Coursera'},
            {'url': 'https://www.udemy.com/', 'title': 'Udemy'},
            {'url': 'https://www.linkedin.com/learning/', 'title': 'LinkedIn Learning'},
            {'url': 'https://www.techcrunch.com/', 'title': 'TechCrunch'},
        ]
        
        # General sites (30% of history)
        general_sites = [
            {'url': 'https://www.google.com/', 'title': 'Google'},
            {'url': 'https://www.youtube.com/', 'title': 'YouTube'},
            {'url': 'https://www.reddit.com/', 'title': 'Reddit'},
            {'url': 'https://www.wikipedia.org/', 'title': 'Wikipedia'},
            {'url': 'https://www.cnn.com/', 'title': 'CNN'},
            {'url': 'https://www.bbc.com/', 'title': 'BBC News'},
            {'url': 'https://www.nytimes.com/', 'title': 'New York Times'},
        ]
        
        # Generate realistic visit patterns
        total_visits = random.randint(50, 150)
        
        for i in range(total_visits):
            # Choose site type based on probability
            if random.random() < 0.7:  # 70% professional
                site_info = random.choice(professional_sites)
            else:  # 30% general
                site_info = random.choice(general_sites)
            
            # Realistic timestamps (more visits during work hours)
            hour = random.randint(8, 22)
            if 9 <= hour <= 17:  # Work hours - more likely
                if random.random() < 0.3:
                    hour = random.randint(9, 17)
            
            # Calculate visit time with realistic intervals
            if i == 0:
                visit_time = base_time
            else:
                # Vary intervals based on time of day and site type
                if 9 <= hour <= 17:  # Work hours
                    interval = random.uniform(1800, 7200)  # 30min to 2hr
                else:  # Off hours
                    interval = random.uniform(3600, 14400)  # 1hr to 4hr
                
                visit_time = history_items[-1]['visit_time'] + interval
            
            # Generate realistic visit count (some sites visited multiple times)
            visit_count = 1
            if random.random() < 0.3:  # 30% chance of multiple visits
                visit_count = random.randint(2, 5)
            
            history_items.append({
                'url': site_info['url'],
                'title': site_info['title'],
                'visit_time': visit_time,
                'visit_count': visit_count,
                'last_visit': visit_time + random.uniform(0, 3600)  # Within 1 hour
            })
        
        # Sort by visit time
        history_items.sort(key=lambda x: x['visit_time'])
        
        logger.debug("Generated browsing history", 
                    total_items=len(history_items),
                    professional_items=len([h for h in history_items if 'linkedin.com' in h['url'] or 'indeed.com' in h['url']]))
        
        return history_items
    
    def _generate_realistic_preferences(self) -> Dict[str, Any]:
        """Generate realistic user preferences."""
        preferences = {
            'language': 'en-US',
            'timezone': 'America/New_York',
            'date_format': 'MM/DD/YYYY',
            'number_format': 'US',
            'theme': random.choice(['light', 'dark', 'auto']),
            'notifications': {
                'email': random.choice([True, False]),
                'push': random.choice([True, False]),
                'sms': False,
                'desktop': random.choice([True, False])
            },
            'privacy': {
                'tracking_protection': random.choice([True, False]),
                'do_not_track': random.choice([True, False]),
                'third_party_cookies': random.choice([True, False])
            },
            'accessibility': {
                'high_contrast': random.choice([True, False]),
                'reduced_motion': random.choice([True, False]),
                'screen_reader': False
            },
            'performance': {
                'hardware_acceleration': random.choice([True, False]),
                'preload_pages': random.choice([True, False]),
                'cache_size': random.randint(100, 1000)  # MB
            }
        }
        
        return preferences
    
    def _generate_realistic_cache_data(self) -> Dict[str, Any]:
        """Generate realistic cache data."""
        cache_data = {
            'images': [
                {
                    'url': 'https://static.licdn.com/sc/h/abc123',
                    'size': random.randint(1024, 10240),
                    'type': 'image/jpeg',
                    'cached_time': time.time() - random.uniform(0, 86400)
                },
                {
                    'url': 'https://media.licdn.com/dms/image/def456',
                    'size': random.randint(2048, 20480),
                    'type': 'image/png',
                    'cached_time': time.time() - random.uniform(0, 86400)
                }
            ],
            'css': [
                {
                    'url': 'https://static.licdn.com/sc/h/styles.css',
                    'size': random.randint(512, 2048),
                    'type': 'text/css',
                    'cached_time': time.time() - random.uniform(0, 86400)
                }
            ],
            'js': [
                {
                    'url': 'https://static.licdn.com/sc/h/script.js',
                    'size': random.randint(1024, 8192),
                    'type': 'application/javascript',
                    'cached_time': time.time() - random.uniform(0, 86400)
                }
            ]
        }
        
        return cache_data
    
    def _generate_realistic_local_storage(self) -> Dict[str, Any]:
        """Generate realistic local storage data."""
        local_storage_data = {
            'user_preferences': {
                'theme': random.choice(['light', 'dark']),
                'language': 'en-US',
                'notifications_enabled': random.choice([True, False])
            },
            'session_data': {
                'last_activity': time.time() - random.uniform(0, 3600),
                'page_views': random.randint(10, 100),
                'interaction_count': random.randint(50, 500)
            },
            'form_data': {
                'saved_searches': [
                    'software engineer',
                    'python developer',
                    'remote jobs'
                ],
                'recent_companies': [
                    'Google',
                    'Microsoft',
                    'Amazon',
                    'Apple'
                ]
            }
        }
        
        return local_storage_data
    
    def _inject_profile_data(self, context: BrowserContext, browsing_history: List[Dict], 
                           preferences: Dict, cache_data: Dict, local_storage_data: Dict) -> None:
        """
        Inject profile data into browser context using JavaScript.
        
        Args:
            context: Browser context to inject data into
            browsing_history: Generated browsing history
            preferences: User preferences
            cache_data: Cache data
            local_storage_data: Local storage data
        """
        try:
            # Create injection script
            injection_script = f"""
            // Inject realistic browsing history
            const history = {json.dumps(browsing_history)};
            if (window.history && window.history.pushState) {{
                // Simulate history entries (limited by browser security)
                console.log('Simulated browsing history:', history.length, 'items');
            }}
            
            // Inject preferences into localStorage
            const preferences = {json.dumps(preferences)};
            localStorage.setItem('user_preferences', JSON.stringify(preferences));
            
            // Inject session data
            const sessionData = {json.dumps(local_storage_data)};
            localStorage.setItem('session_data', JSON.stringify(sessionData));
            
            // Inject form data
            const formData = {json.dumps(local_storage_data.get('form_data', {}))};
            localStorage.setItem('form_data', JSON.stringify(formData));
            
            // Inject cache simulation data
            const cacheData = {json.dumps(cache_data)};
            sessionStorage.setItem('cache_simulation', JSON.stringify(cacheData));
            
            // Add realistic user agent hints
            Object.defineProperty(navigator, 'doNotTrack', {{
                get: function() {{ return preferences.privacy.do_not_track ? '1' : '0'; }}
            }});
            
            // Simulate realistic connection
            Object.defineProperty(navigator, 'connection', {{
                get: function() {{
                    return {{
                        effectiveType: '4g',
                        rtt: {random.randint(20, 100)},
                        downlink: {random.uniform(5, 25)},
                        saveData: false
                    }};
                }}
            }});
            
            console.log('Stealth profile data injected successfully');
            """
            
            # Add the injection script to the context
            context.add_init_script(injection_script)
            
            logger.debug("Injected profile data into browser context")
            
        except Exception as e:
            logger.error("Failed to inject profile data", error=str(e))
            raise
    
    def simulate_realistic_login_flow(self, page: Page, email: str, password: str) -> bool:
        """
        Simulate realistic login behavior with personality-based patterns.
        
        Args:
            page: Playwright page object
            email: Email address for login
            password: Password for login
            
        Returns:
            True if login flow was simulated successfully, False otherwise
        """
        try:
            logger.info("Starting realistic login flow simulation")
            
            # Simulate realistic page loading delay
            self._simulate_page_loading_delay()
            
            # Simulate reading the login page
            self._simulate_page_reading(page, "login page")
            
            # Occasional "forgot password" behavior (5% chance)
            if random.random() < 0.05:
                self._simulate_forgot_password_attempt(page)
            
            # Realistic typing patterns
            self._simulate_realistic_typing(page, email, password)
            
            # Occasional login failures (2% chance)
            if random.random() < 0.02:
                return self._simulate_login_failure_recovery(page)
            
            # Track interaction
            self.interaction_count += 1
            self.activity_history.append({
                'action': 'login_simulation',
                'timestamp': time.time(),
                'duration': random.uniform(2, 5)
            })
            
            logger.info("Completed realistic login flow simulation")
            return True
            
        except Exception as e:
            logger.error("Failed to simulate realistic login flow", error=str(e))
            return False
    
    def _simulate_page_loading_delay(self) -> None:
        """Simulate realistic page loading delay based on connection speed."""
        # Simulate different connection speeds
        connection_speed = random.choice(['slow', 'medium', 'fast'])
        
        if connection_speed == 'slow':
            delay = random.uniform(2, 5)
        elif connection_speed == 'medium':
            delay = random.uniform(1, 2)
        else:
            delay = random.uniform(0.5, 1)
        
        logger.debug("Simulating page loading delay", 
                    connection_speed=connection_speed, 
                    delay=delay)
        
        time.sleep(delay)
    
    def _simulate_page_reading(self, page: Page, page_type: str) -> None:
        """
        Simulate realistic page reading behavior.
        
        Args:
            page: Playwright page object
            page_type: Type of page being read
        """
        try:
            # Get page content length
            content_length = len(page.inner_text("body"))
            
            # Calculate reading time based on user personality
            words = content_length / 5  # Approximate word count
            reading_time = (words / self.user_personality['reading_speed_wpm']) * 60
            
            # Add realistic variance
            reading_time *= random.uniform(0.7, 1.3)
            
            # Cap reading time
            reading_time = min(reading_time, 10)  # Max 10 seconds
            
            logger.debug("Simulating page reading", 
                        page_type=page_type, 
                        reading_time=reading_time,
                        content_length=content_length)
            
            time.sleep(reading_time)
            
        except Exception as e:
            logger.debug("Could not simulate page reading", error=str(e))
            time.sleep(random.uniform(1, 3))  # Fallback delay
    
    def _simulate_forgot_password_attempt(self, page: Page) -> None:
        """Simulate occasional 'forgot password' behavior."""
        try:
            logger.debug("Simulating forgot password attempt")
            
            # Look for forgot password link
            forgot_link = page.locator('a:has-text("Forgot password"), a:has-text("Forgot your password")')
            if forgot_link.count() > 0:
                # Hover over the link (but don't click)
                forgot_link.hover()
                time.sleep(random.uniform(0.5, 1.5))
                
                # Move mouse away
                page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                time.sleep(random.uniform(0.3, 0.8))
            
        except Exception as e:
            logger.debug("Could not simulate forgot password attempt", error=str(e))
    
    def _simulate_realistic_typing(self, page: Page, email: str, password: str) -> None:
        """
        Simulate realistic typing patterns based on user personality.
        
        Args:
            page: Playwright page object
            email: Email address to type
            password: Password to type
        """
        try:
            # Find email field
            email_field = page.locator('input[type="email"], input[id="username"], input[name="session_key"]')
            if email_field.count() > 0:
                # Simulate realistic email typing
                self._type_with_personality(page, email_field.first, email)
                
                # Pause between fields (realistic behavior)
                time.sleep(random.uniform(0.5, 1.5))
            
            # Find password field
            password_field = page.locator('input[type="password"], input[id="password"], input[name="session_password"]')
            if password_field.count() > 0:
                # Simulate realistic password typing
                self._type_with_personality(page, password_field.first, password)
                
        except Exception as e:
            logger.error("Failed to simulate realistic typing", error=str(e))
    
    def _type_with_personality(self, page: Page, field, text: str) -> None:
        """
        Type text with realistic personality-based patterns.
        
        Args:
            page: Playwright page object
            field: Form field to type into
            text: Text to type
        """
        try:
            # Focus field
            field.focus()
            time.sleep(random.uniform(0.2, 0.5))
            
            # Clear existing content
            field.fill("")
            time.sleep(random.uniform(0.3, 0.7))
            
            # Type with realistic patterns
            words = text.split()
            for word_idx, word in enumerate(words):
                if word_idx > 0:
                    # Pause between words
                    word_pause = random.uniform(0.15, 0.4)
                    time.sleep(word_pause)
                
                # Type word character by character
                for char_idx, char in enumerate(word):
                    # Base typing speed varies by character type
                    if char in 'aeiou':
                        base_delay = random.uniform(0.08, 0.18)
                    elif char in 'qwertyuiop':
                        base_delay = random.uniform(0.06, 0.14)
                    elif char in 'asdfghjkl':
                        base_delay = random.uniform(0.07, 0.15)
                    elif char in 'zxcvbnm':
                        base_delay = random.uniform(0.08, 0.16)
                    else:
                        base_delay = random.uniform(0.1, 0.2)
                    
                    # Adjust for user personality
                    base_delay *= (60 / self.user_personality['typing_speed_wpm'])
                    
                    # Add occasional longer pauses (thinking, re-reading)
                    if random.random() < 0.08:  # 8% chance
                        base_delay += random.uniform(0.4, 1.2)
                    
                    field.type(char, delay=base_delay)
                
                # Simulate occasional typo correction
                if random.random() < self.user_personality['error_rate']:
                    self._simulate_typo_correction(field, word)
                    
        except Exception as e:
            logger.error("Failed to type with personality", error=str(e))
    
    def _simulate_typo_correction(self, field, word: str) -> None:
        """
        Simulate realistic typo correction.
        
        Args:
            field: Form field
            word: Word that had a typo
        """
        try:
            # Pause as if noticing the error
            time.sleep(random.uniform(0.3, 0.8))
            
            # Backspace with variable speed
            backspace_count = random.randint(1, min(3, len(word)))
            for _ in range(backspace_count):
                field.press("Backspace")
                time.sleep(random.uniform(0.1, 0.25))
            
            # Retype with slightly faster speed
            retype_text = word[-backspace_count:]
            for char in retype_text:
                field.type(char, delay=random.uniform(0.05, 0.12))
                
        except Exception as e:
            logger.debug("Could not simulate typo correction", error=str(e))
    
    def _simulate_login_failure_recovery(self, page: Page) -> bool:
        """
        Simulate login failure and recovery.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            logger.debug("Simulating login failure and recovery")
            
            # Simulate typing wrong password first
            password_field = page.locator('input[type="password"]')
            if password_field.count() > 0:
                # Type wrong password
                wrong_password = "wrongpassword123"
                self._type_with_personality(page, password_field.first, wrong_password)
                
                # Click login button
                login_button = page.locator('button[type="submit"]')
                if login_button.count() > 0:
                    login_button.click()
                    time.sleep(random.uniform(1, 2))
                    
                    # Clear password field
                    password_field.fill("")
                    time.sleep(random.uniform(0.5, 1))
                    
                    # Type correct password
                    correct_password = "correctpassword123"  # This would be the actual password
                    self._type_with_personality(page, password_field.first, correct_password)
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.debug("Could not simulate login failure recovery", error=str(e))
            return False
    
    def maintain_session_continuity(self, page: Page) -> None:
        """
        Maintain session continuity using advanced techniques.
        
        Args:
            page: Playwright page object
        """
        try:
            # Inject session continuity markers
            self._inject_session_markers(page)
            
            # Maintain behavioral consistency
            self._maintain_behavioral_consistency(page)
            
            # Simulate realistic session state
            self._simulate_realistic_session_state(page)
            
            # Track session activity
            self.activity_history.append({
                'action': 'session_continuity',
                'timestamp': time.time(),
                'session_duration': time.time() - self.session_start_time
            })
            
        except Exception as e:
            logger.error("Failed to maintain session continuity", error=str(e))
    
    def _inject_session_markers(self, page: Page) -> None:
        """Inject session continuity markers into the page."""
        try:
            session_data = {
                'session_id': self.session_id,
                'user_preferences': self.user_personality,
                'last_activity': time.time(),
                'browsing_pattern': self._get_browsing_pattern(),
                'interaction_count': self.interaction_count
            }
            
            # Use localStorage instead of cookies
            page.evaluate(f"""
                localStorage.setItem('stealth_session', JSON.stringify({json.dumps(session_data)}));
                sessionStorage.setItem('session_marker', '{session_data['session_id']}');
                
                // Add session continuity indicators
                window.stealthSessionData = {json.dumps(session_data)};
            """)
            
            logger.debug("Injected session markers")
            
        except Exception as e:
            logger.debug("Could not inject session markers", error=str(e))
    
    def _get_browsing_pattern(self) -> Dict[str, Any]:
        """Get current browsing pattern based on personality."""
        return {
            'scroll_speed': self.user_personality['preferred_scroll_speed'],
            'click_accuracy': self.user_personality['click_accuracy'],
            'interaction_style': self.user_personality['interaction_style'],
            'hesitation_level': self.user_personality['hesitation_level']
        }
    
    def _maintain_behavioral_consistency(self, page: Page) -> None:
        """Maintain behavioral consistency throughout the session."""
        try:
            # Update personality based on session fatigue
            session_duration = time.time() - self.session_start_time
            fatigue_factor = 1 + (session_duration / 3600) * self.user_personality['session_fatigue_rate']
            
            # Adjust typing speed based on fatigue
            adjusted_typing_speed = self.user_personality['typing_speed_wpm'] / fatigue_factor
            
            # Update session state
            self.session_state['fatigue_factor'] = fatigue_factor
            self.session_state['adjusted_typing_speed'] = adjusted_typing_speed
            
            logger.debug("Maintained behavioral consistency", 
                        fatigue_factor=fatigue_factor,
                        session_duration=session_duration)
            
        except Exception as e:
            logger.debug("Could not maintain behavioral consistency", error=str(e))
    
    def _simulate_realistic_session_state(self, page: Page) -> None:
        """Simulate realistic session state."""
        try:
            # Simulate occasional micro-interactions
            if random.random() < 0.1:  # 10% chance
                self._simulate_micro_interaction(page)
            
            # Simulate occasional page checking
            if random.random() < 0.05:  # 5% chance
                self._simulate_page_checking(page)
                
        except Exception as e:
            logger.debug("Could not simulate realistic session state", error=str(e))
    
    def _simulate_micro_interaction(self, page: Page) -> None:
        """Simulate realistic micro-interactions."""
        try:
            # Small mouse movement
            viewport = page.viewport_size
            if viewport:
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            logger.debug("Could not simulate micro-interaction", error=str(e))
    
    def _simulate_page_checking(self, page: Page) -> None:
        """Simulate realistic page checking behavior."""
        try:
            # Small scroll to "check something"
            scroll_amount = random.randint(-100, 100)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.debug("Could not simulate page checking", error=str(e))
    
    def save_session_state(self, page: Page) -> None:
        """
        Save session state using non-cookie mechanisms.
        
        Args:
            page: Playwright page object
        """
        try:
            session_data = {
                'session_id': self.session_id,
                'last_activity': time.time(),
                'user_preferences': self.user_personality,
                'browsing_history': self.browsing_history[-10:],  # Last 10 items
                'session_fingerprint': self.session_fingerprint,
                'interaction_count': self.interaction_count,
                'activity_history': self.activity_history[-20:],  # Last 20 activities
                'session_duration': time.time() - self.session_start_time
            }
            
            # Save to localStorage
            page.evaluate(f"""
                localStorage.setItem('stealth_session', JSON.stringify({json.dumps(session_data)}));
                localStorage.setItem('session_timestamp', '{time.time()}');
            """)
            
            # Also save to file for persistence across browser sessions
            session_file = self.profile_dir / f"session_{self.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info("Saved session state", 
                       session_id=self.session_id,
                       interaction_count=self.interaction_count)
                
        except Exception as e:
            logger.error("Failed to save session state", error=str(e))
    
    def restore_session_state(self, page: Page) -> bool:
        """
        Restore session state from localStorage and files.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if session state was restored successfully, False otherwise
        """
        try:
            # Try to restore from localStorage first
            session_data = page.evaluate("""
                const data = localStorage.getItem('stealth_session');
                return data ? JSON.parse(data) : null;
            """)
            
            if session_data:
                # Restore session data
                self.session_id = session_data.get('session_id', self.session_id)
                self.user_personality = session_data.get('user_preferences', self.user_personality)
                self.browsing_history = session_data.get('browsing_history', [])
                self.session_fingerprint = session_data.get('session_fingerprint')
                self.interaction_count = session_data.get('interaction_count', 0)
                self.activity_history = session_data.get('activity_history', [])
                
                logger.info("Restored session state from localStorage", 
                           session_id=self.session_id,
                           interaction_count=self.interaction_count)
                return True
            
            # Try to restore from file
            session_files = list(self.profile_dir.glob("session_*.json"))
            if session_files:
                # Get the most recent session file
                latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
                
                with open(latest_file, 'r') as f:
                    session_data = json.load(f)
                
                # Restore session data
                self.session_id = session_data.get('session_id', self.session_id)
                self.user_personality = session_data.get('user_preferences', self.user_personality)
                self.browsing_history = session_data.get('browsing_history', [])
                self.session_fingerprint = session_data.get('session_fingerprint')
                self.interaction_count = session_data.get('interaction_count', 0)
                self.activity_history = session_data.get('activity_history', [])
                
                logger.info("Restored session state from file", 
                           session_id=self.session_id,
                           file_path=str(latest_file))
                return True
                
        except Exception as e:
            logger.debug("Could not restore session state", error=str(e))
        
        return False
    
    def cleanup_session(self) -> None:
        """Clean up session resources and data."""
        try:
            # Clean up old session files
            session_files = list(self.profile_dir.glob("session_*.json"))
            current_time = time.time()
            
            for session_file in session_files:
                file_age = current_time - session_file.stat().st_mtime
                if file_age > 86400:  # Older than 24 hours
                    session_file.unlink()
                    logger.debug("Cleaned up old session file", file_path=str(session_file))
            
            logger.info("Session cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup session", error=str(e))
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            'session_id': self.session_id,
            'session_duration': time.time() - self.session_start_time,
            'interaction_count': self.interaction_count,
            'activity_count': len(self.activity_history),
            'browsing_history_count': len(self.browsing_history),
            'personality_traits': len(self.user_personality),
            'profile_dir': str(self.profile_dir)
        }
