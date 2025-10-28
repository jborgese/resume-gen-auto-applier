# src/persistent_profile_manager.py

import json
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import BrowserContext
from src.logging_config import get_logger

logger = get_logger(__name__)


class PersistentProfileManager:
    """
    Creates and manages realistic browser profiles with browsing history,
    preferences, and cache data to avoid automation detection.
    """
    
    def __init__(self, profile_dir: Path):
        """
        Initialize the persistent profile manager.
        
        Args:
            profile_dir: Directory to store profile data
        """
        self.profile_dir = profile_dir
        self.profile_dir.mkdir(exist_ok=True)
        
        # Profile data storage
        self.profile_data = {}
        self.profile_id = self._generate_profile_id()
        
        # Profile characteristics
        self.user_demographics = self._generate_user_demographics()
        self.browsing_patterns = self._generate_browsing_patterns()
        
        logger.info("PersistentProfileManager initialized", 
                   profile_id=self.profile_id,
                   profile_dir=str(self.profile_dir))
    
    def _generate_profile_id(self) -> str:
        """Generate a unique profile ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_user_demographics(self) -> Dict[str, Any]:
        """Generate realistic user demographics."""
        demographics = {
            'age_group': random.choice(['25-34', '35-44', '45-54']),
            'location': random.choice(['US', 'CA', 'UK', 'AU']),
            'timezone': random.choice([
                'America/New_York', 'America/Los_Angeles', 'America/Chicago',
                'Europe/London', 'Europe/Paris', 'Australia/Sydney'
            ]),
            'language': random.choice(['en-US', 'en-CA', 'en-GB', 'en-AU']),
            'device_type': random.choice(['desktop', 'laptop']),
            'os': random.choice(['Windows', 'macOS', 'Linux']),
            'browser': 'Chrome',
            'screen_resolution': random.choice([
                '1920x1080', '1366x768', '1440x900', '2560x1440'
            ])
        }
        
        return demographics
    
    def _generate_browsing_patterns(self) -> Dict[str, Any]:
        """Generate realistic browsing patterns."""
        patterns = {
            'peak_hours': random.choice(['morning', 'afternoon', 'evening']),
            'browsing_frequency': random.choice(['daily', 'weekly', 'occasional']),
            'session_duration': random.uniform(15, 120),  # minutes
            'page_views_per_session': random.randint(5, 25),
            'scroll_behavior': random.choice(['thorough', 'quick', 'selective']),
            'click_behavior': random.choice(['precise', 'rapid', 'hesitant']),
            'form_filling_style': random.choice(['careful', 'quick', 'methodical'])
        }
        
        return patterns
    
    def create_realistic_profile(self) -> Dict[str, Any]:
        """
        Create a complete realistic browser profile.
        
        Returns:
            Dictionary containing all profile data
        """
        try:
            logger.info("Creating realistic browser profile")
            
            profile_data = {
                'profile_id': self.profile_id,
                'demographics': self.user_demographics,
                'browsing_patterns': self.browsing_patterns,
                'browsing_history': self.generate_browsing_history(),
                'preferences': self.generate_preferences(),
                'cache_data': self.generate_cache_data(),
                'local_storage_data': self.generate_local_storage_data(),
                'bookmarks': self.generate_bookmarks(),
                'downloads': self.generate_download_history(),
                'search_history': self.generate_search_history(),
                'form_data': self.generate_form_data(),
                'created_at': time.time(),
                'last_updated': time.time()
            }
            
            # Store profile data
            self.profile_data = profile_data
            
            # Save profile to file
            self._save_profile_to_file()
            
            logger.info("Created realistic browser profile", 
                       profile_id=self.profile_id,
                       history_items=len(profile_data['browsing_history']))
            
            return profile_data
            
        except Exception as e:
            logger.error("Failed to create realistic profile", error=str(e))
            raise
    
    def generate_browsing_history(self) -> List[Dict[str, Any]]:
        """Generate realistic browsing history with professional focus."""
        base_time = time.time() - (14 * 24 * 3600)  # 14 days ago
        
        history_items = []
        
        # Professional sites (75% of history)
        professional_sites = [
            {'url': 'https://www.linkedin.com/feed/', 'title': 'LinkedIn Feed', 'category': 'professional'},
            {'url': 'https://www.linkedin.com/jobs/', 'title': 'LinkedIn Jobs', 'category': 'job_search'},
            {'url': 'https://www.linkedin.com/mynetwork/', 'title': 'LinkedIn My Network', 'category': 'professional'},
            {'url': 'https://www.linkedin.com/learning/', 'title': 'LinkedIn Learning', 'category': 'education'},
            {'url': 'https://www.indeed.com/', 'title': 'Indeed Jobs', 'category': 'job_search'},
            {'url': 'https://www.glassdoor.com/', 'title': 'Glassdoor', 'category': 'job_search'},
            {'url': 'https://www.monster.com/', 'title': 'Monster Jobs', 'category': 'job_search'},
            {'url': 'https://github.com/', 'title': 'GitHub', 'category': 'development'},
            {'url': 'https://stackoverflow.com/', 'title': 'Stack Overflow', 'category': 'development'},
            {'url': 'https://www.coursera.org/', 'title': 'Coursera', 'category': 'education'},
            {'url': 'https://www.udemy.com/', 'title': 'Udemy', 'category': 'education'},
            {'url': 'https://www.techcrunch.com/', 'title': 'TechCrunch', 'category': 'news'},
            {'url': 'https://www.hackernews.com/', 'title': 'Hacker News', 'category': 'news'},
            {'url': 'https://www.reddit.com/r/programming/', 'title': 'Programming Reddit', 'category': 'community'},
            {'url': 'https://www.medium.com/', 'title': 'Medium', 'category': 'content'},
        ]
        
        # General sites (25% of history)
        general_sites = [
            {'url': 'https://www.google.com/', 'title': 'Google', 'category': 'search'},
            {'url': 'https://www.youtube.com/', 'title': 'YouTube', 'category': 'entertainment'},
            {'url': 'https://www.reddit.com/', 'title': 'Reddit', 'category': 'community'},
            {'url': 'https://www.wikipedia.org/', 'title': 'Wikipedia', 'category': 'reference'},
            {'url': 'https://www.cnn.com/', 'title': 'CNN', 'category': 'news'},
            {'url': 'https://www.bbc.com/', 'title': 'BBC News', 'category': 'news'},
            {'url': 'https://www.nytimes.com/', 'title': 'New York Times', 'category': 'news'},
            {'url': 'https://www.amazon.com/', 'title': 'Amazon', 'category': 'shopping'},
        ]
        
        # Generate realistic visit patterns
        total_visits = random.randint(80, 200)
        
        for i in range(total_visits):
            # Choose site type based on probability and time of day
            current_hour = random.randint(8, 22)
            
            if 9 <= current_hour <= 17:  # Work hours - more professional sites
                if random.random() < 0.8:  # 80% professional during work hours
                    site_info = random.choice(professional_sites)
                else:
                    site_info = random.choice(general_sites)
            else:  # Off hours - more general sites
                if random.random() < 0.4:  # 40% professional during off hours
                    site_info = random.choice(professional_sites)
                else:
                    site_info = random.choice(general_sites)
            
            # Calculate visit time with realistic intervals
            if i == 0:
                visit_time = base_time
            else:
                # Vary intervals based on time of day and site type
                if 9 <= current_hour <= 17:  # Work hours
                    interval = random.uniform(1800, 7200)  # 30min to 2hr
                else:  # Off hours
                    interval = random.uniform(3600, 14400)  # 1hr to 4hr
                
                visit_time = history_items[-1]['visit_time'] + interval
            
            # Generate realistic visit count (some sites visited multiple times)
            visit_count = 1
            if random.random() < 0.4:  # 40% chance of multiple visits
                visit_count = random.randint(2, 8)
            
            # Generate realistic page views per visit
            page_views = random.randint(1, 5)
            
            history_items.append({
                'url': site_info['url'],
                'title': site_info['title'],
                'category': site_info['category'],
                'visit_time': visit_time,
                'visit_count': visit_count,
                'page_views': page_views,
                'last_visit': visit_time + random.uniform(0, 3600),  # Within 1 hour
                'session_duration': random.uniform(30, 600)  # 30 seconds to 10 minutes
            })
        
        # Sort by visit time
        history_items.sort(key=lambda x: x['visit_time'])
        
        logger.debug("Generated browsing history", 
                    total_items=len(history_items),
                    professional_items=len([h for h in history_items if h['category'] in ['professional', 'job_search', 'development']]))
        
        return history_items
    
    def generate_preferences(self) -> Dict[str, Any]:
        """Generate realistic user preferences."""
        preferences = {
            'language': self.user_demographics['language'],
            'timezone': self.user_demographics['timezone'],
            'date_format': 'MM/DD/YYYY' if self.user_demographics['location'] in ['US'] else 'DD/MM/YYYY',
            'number_format': 'US' if self.user_demographics['location'] in ['US'] else 'International',
            'theme': random.choice(['light', 'dark', 'auto']),
            'notifications': {
                'email': random.choice([True, False]),
                'push': random.choice([True, False]),
                'sms': False,
                'desktop': random.choice([True, False]),
                'browser': random.choice([True, False])
            },
            'privacy': {
                'tracking_protection': random.choice([True, False]),
                'do_not_track': random.choice([True, False]),
                'third_party_cookies': random.choice([True, False]),
                'location_sharing': random.choice([True, False]),
                'analytics_opt_out': random.choice([True, False])
            },
            'accessibility': {
                'high_contrast': random.choice([True, False]),
                'reduced_motion': random.choice([True, False]),
                'screen_reader': False,
                'font_size': random.choice(['small', 'medium', 'large']),
                'zoom_level': random.uniform(100, 150)
            },
            'performance': {
                'hardware_acceleration': random.choice([True, False]),
                'preload_pages': random.choice([True, False]),
                'cache_size': random.randint(100, 1000),  # MB
                'image_quality': random.choice(['high', 'medium', 'low']),
                'video_quality': random.choice(['high', 'medium', 'low'])
            },
            'security': {
                'password_manager': random.choice([True, False]),
                'two_factor_auth': random.choice([True, False]),
                'secure_browsing': random.choice([True, False]),
                'phishing_protection': random.choice([True, False])
            }
        }
        
        return preferences
    
    def generate_cache_data(self) -> Dict[str, Any]:
        """Generate realistic cache data."""
        cache_data = {
            'images': [
                {
                    'url': 'https://static.licdn.com/sc/h/abc123',
                    'size': random.randint(1024, 10240),
                    'type': 'image/jpeg',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 10)
                },
                {
                    'url': 'https://media.licdn.com/dms/image/def456',
                    'size': random.randint(2048, 20480),
                    'type': 'image/png',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 5)
                },
                {
                    'url': 'https://static.licdn.com/sc/h/company-logo',
                    'size': random.randint(512, 2048),
                    'type': 'image/svg+xml',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 15)
                }
            ],
            'css': [
                {
                    'url': 'https://static.licdn.com/sc/h/styles.css',
                    'size': random.randint(512, 2048),
                    'type': 'text/css',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 20)
                },
                {
                    'url': 'https://static.licdn.com/sc/h/components.css',
                    'size': random.randint(1024, 4096),
                    'type': 'text/css',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 15)
                }
            ],
            'js': [
                {
                    'url': 'https://static.licdn.com/sc/h/script.js',
                    'size': random.randint(1024, 8192),
                    'type': 'application/javascript',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 25)
                },
                {
                    'url': 'https://static.licdn.com/sc/h/vendor.js',
                    'size': random.randint(2048, 16384),
                    'type': 'application/javascript',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 20)
                }
            ],
            'fonts': [
                {
                    'url': 'https://static.licdn.com/sc/h/font.woff2',
                    'size': random.randint(2048, 8192),
                    'type': 'font/woff2',
                    'cached_time': time.time() - random.uniform(0, 86400),
                    'access_count': random.randint(1, 30)
                }
            ]
        }
        
        return cache_data
    
    def generate_local_storage_data(self) -> Dict[str, Any]:
        """Generate realistic local storage data."""
        local_storage_data = {
            'user_preferences': {
                'theme': random.choice(['light', 'dark']),
                'language': self.user_demographics['language'],
                'notifications_enabled': random.choice([True, False]),
                'auto_save': random.choice([True, False]),
                'remember_me': random.choice([True, False])
            },
            'session_data': {
                'last_activity': time.time() - random.uniform(0, 3600),
                'page_views': random.randint(10, 100),
                'interaction_count': random.randint(50, 500),
                'session_duration': random.uniform(300, 3600),  # 5 minutes to 1 hour
                'login_count': random.randint(1, 10)
            },
            'form_data': {
                'saved_searches': [
                    'software engineer',
                    'python developer',
                    'remote jobs',
                    'senior developer',
                    'full stack developer'
                ],
                'recent_companies': [
                    'Google',
                    'Microsoft',
                    'Amazon',
                    'Apple',
                    'Meta',
                    'Netflix',
                    'Spotify'
                ],
                'saved_locations': [
                    'San Francisco, CA',
                    'New York, NY',
                    'Seattle, WA',
                    'Austin, TX',
                    'Remote'
                ]
            },
            'analytics_data': {
                'page_load_times': [random.uniform(0.5, 3.0) for _ in range(20)],
                'click_events': random.randint(100, 1000),
                'scroll_events': random.randint(500, 5000),
                'form_submissions': random.randint(5, 50)
            }
        }
        
        return local_storage_data
    
    def generate_bookmarks(self) -> List[Dict[str, Any]]:
        """Generate realistic bookmarks."""
        bookmarks = [
            {
                'title': 'LinkedIn Jobs',
                'url': 'https://www.linkedin.com/jobs/',
                'folder': 'Job Search',
                'created_at': time.time() - random.uniform(0, 86400 * 30),
                'access_count': random.randint(1, 20)
            },
            {
                'title': 'GitHub',
                'url': 'https://github.com/',
                'folder': 'Development',
                'created_at': time.time() - random.uniform(0, 86400 * 30),
                'access_count': random.randint(1, 15)
            },
            {
                'title': 'Stack Overflow',
                'url': 'https://stackoverflow.com/',
                'folder': 'Development',
                'created_at': time.time() - random.uniform(0, 86400 * 30),
                'access_count': random.randint(1, 25)
            },
            {
                'title': 'Indeed Jobs',
                'url': 'https://www.indeed.com/',
                'folder': 'Job Search',
                'created_at': time.time() - random.uniform(0, 86400 * 30),
                'access_count': random.randint(1, 10)
            },
            {
                'title': 'Google',
                'url': 'https://www.google.com/',
                'folder': 'General',
                'created_at': time.time() - random.uniform(0, 86400 * 30),
                'access_count': random.randint(1, 50)
            }
        ]
        
        return bookmarks
    
    def generate_download_history(self) -> List[Dict[str, Any]]:
        """Generate realistic download history."""
        downloads = [
            {
                'filename': 'resume_template.docx',
                'url': 'https://example.com/resume-template.docx',
                'size': random.randint(1024, 10240),
                'download_time': time.time() - random.uniform(0, 86400 * 7),
                'file_type': 'document'
            },
            {
                'filename': 'job_description.pdf',
                'url': 'https://example.com/job-description.pdf',
                'size': random.randint(2048, 20480),
                'download_time': time.time() - random.uniform(0, 86400 * 3),
                'file_type': 'document'
            },
            {
                'filename': 'company_logo.png',
                'url': 'https://example.com/logo.png',
                'size': random.randint(512, 2048),
                'download_time': time.time() - random.uniform(0, 86400 * 5),
                'file_type': 'image'
            }
        ]
        
        return downloads
    
    def generate_search_history(self) -> List[Dict[str, Any]]:
        """Generate realistic search history."""
        search_terms = [
            'python developer jobs',
            'remote software engineer',
            'senior developer salary',
            'linkedin profile tips',
            'resume writing advice',
            'interview preparation',
            'coding interview questions',
            'tech companies hiring',
            'software engineering trends',
            'career development'
        ]
        
        search_history = []
        for term in search_terms:
            if random.random() < 0.7:  # 70% chance of searching each term
                search_history.append({
                    'term': term,
                    'timestamp': time.time() - random.uniform(0, 86400 * 14),
                    'result_count': random.randint(100, 10000),
                    'clicked_results': random.randint(0, 5)
                })
        
        return search_history
    
    def generate_form_data(self) -> Dict[str, Any]:
        """Generate realistic form data."""
        form_data = {
            'contact_info': {
                'email': 'user@example.com',
                'phone': f'({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}',
                'address': f'{random.randint(100, 9999)} Main St',
                'city': random.choice(['San Francisco', 'New York', 'Seattle', 'Austin', 'Boston']),
                'state': random.choice(['CA', 'NY', 'WA', 'TX', 'MA']),
                'zip': f'{random.randint(10000, 99999)}'
            },
            'professional_info': {
                'current_title': random.choice([
                    'Software Engineer',
                    'Senior Developer',
                    'Full Stack Developer',
                    'Python Developer',
                    'Software Architect'
                ]),
                'experience_years': random.randint(2, 15),
                'education_level': random.choice(['Bachelor', 'Master', 'PhD']),
                'skills': [
                    'Python', 'JavaScript', 'React', 'Node.js', 'SQL',
                    'AWS', 'Docker', 'Git', 'Agile', 'Machine Learning'
                ]
            },
            'preferences': {
                'job_type': random.choice(['Full-time', 'Contract', 'Part-time']),
                'remote_preference': random.choice(['Remote', 'Hybrid', 'On-site']),
                'salary_range': f'${random.randint(80, 200)}k - ${random.randint(200, 400)}k',
                'location_preference': random.choice(['Any', 'West Coast', 'East Coast', 'Remote'])
            }
        }
        
        return form_data
    
    def inject_profile_data(self, context: BrowserContext) -> None:
        """
        Inject profile data into browser context using JavaScript.
        
        Args:
            context: Browser context to inject data into
        """
        try:
            if not self.profile_data:
                self.create_realistic_profile()
            
            # Create comprehensive injection script
            injection_script = f"""
            // Inject comprehensive profile data
            const profileData = {json.dumps(self.profile_data)};
            
            // Store browsing history for stealth (safe approach)
            const history = profileData.browsing_history;
            try {{
                localStorage.setItem('stealth_browsing_history', JSON.stringify(history.slice(0, 10)));
                console.log('Stored browsing history:', history.length, 'items');
            }} catch (e) {{
                console.log('Could not store browsing history:', e.message);
            }}
            
            // Inject preferences into localStorage (safe)
            const preferences = profileData.preferences;
            try {{
                localStorage.setItem('user_preferences', JSON.stringify(preferences));
            }} catch (e) {{
                console.log('Could not set user preferences:', e.message);
            }}
            
            // Inject session data (safe)
            const sessionData = profileData.local_storage_data;
            try {{
                localStorage.setItem('session_data', JSON.stringify(sessionData));
            }} catch (e) {{
                console.log('Could not set session data:', e.message);
            }}
            
            // Inject form data (safe)
            const formData = profileData.form_data;
            try {{
                localStorage.setItem('form_data', JSON.stringify(formData));
            }} catch (e) {{
                console.log('Could not set form data:', e.message);
            }}
            
            // Inject bookmarks (safe)
            const bookmarks = profileData.bookmarks;
            try {{
                localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
            }} catch (e) {{
                console.log('Could not set bookmarks:', e.message);
            }}
            
            // Inject search history (safe)
            const searchHistory = profileData.search_history;
            try {{
                localStorage.setItem('search_history', JSON.stringify(searchHistory));
            }} catch (e) {{
                console.log('Could not set search history:', e.message);
            }}
            
            // Inject cache simulation data (safe)
            const cacheData = profileData.cache_data;
            try {{
                sessionStorage.setItem('cache_simulation', JSON.stringify(cacheData));
            }} catch (e) {{
                console.log('Could not set cache data:', e.message);
            }}
            
            // Inject analytics data (safe)
            const analyticsData = profileData.local_storage_data.analytics_data;
            try {{
                localStorage.setItem('analytics_data', JSON.stringify(analyticsData));
            }} catch (e) {{
                console.log('Could not set analytics data:', e.message);
            }}
            
            // Store user preferences for stealth (safe approach)
            try {{
                localStorage.setItem('stealth_user_preferences', JSON.stringify({{
                    do_not_track: preferences.privacy.do_not_track,
                    language: '{self.user_demographics['language']}',
                    timezone: '{self.user_demographics['timezone']}',
                    screen_resolution: '{self.user_demographics['screen_resolution']}'
                }}));
            }} catch (e) {{
                console.log('Could not set stealth preferences:', e.message);
            }}
            
            // Store profile data globally for access
            window.stealthProfileData = profileData;
            
            console.log('Stealth profile data injected successfully');
            console.log('Profile ID:', profileData.profile_id);
            console.log('Demographics:', profileData.demographics);
            """
            
            # Add the injection script to the context
            context.add_init_script(injection_script)
            
            logger.info("Injected comprehensive profile data into browser context",
                       profile_id=self.profile_id)
            
        except Exception as e:
            logger.error("Failed to inject profile data", error=str(e))
            raise
    
    def _save_profile_to_file(self) -> None:
        """Save profile data to file for persistence."""
        try:
            profile_file = self.profile_dir / f"profile_{self.profile_id}.json"
            
            with open(profile_file, 'w') as f:
                json.dump(self.profile_data, f, indent=2)
            
            logger.debug("Saved profile data to file", 
                        file_path=str(profile_file))
            
        except Exception as e:
            logger.error("Failed to save profile to file", error=str(e))
    
    def load_profile_from_file(self, profile_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load profile data from file.
        
        Args:
            profile_id: Specific profile ID to load, or None for latest
            
        Returns:
            Profile data if found, None otherwise
        """
        try:
            if profile_id:
                profile_file = self.profile_dir / f"profile_{profile_id}.json"
            else:
                # Find the most recent profile file
                profile_files = list(self.profile_dir.glob("profile_*.json"))
                if not profile_files:
                    return None
                
                profile_file = max(profile_files, key=lambda f: f.stat().st_mtime)
            
            if not profile_file.exists():
                return None
            
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
            
            self.profile_data = profile_data
            self.profile_id = profile_data['profile_id']
            
            logger.info("Loaded profile data from file", 
                       profile_id=self.profile_id,
                       file_path=str(profile_file))
            
            return profile_data
            
        except Exception as e:
            logger.error("Failed to load profile from file", error=str(e))
            return None
    
    def update_profile_data(self, updates: Dict[str, Any]) -> None:
        """
        Update profile data with new information.
        
        Args:
            updates: Dictionary of updates to apply
        """
        try:
            if not self.profile_data:
                self.create_realistic_profile()
            
            # Update profile data
            for key, value in updates.items():
                if key in self.profile_data:
                    if isinstance(self.profile_data[key], dict) and isinstance(value, dict):
                        self.profile_data[key].update(value)
                    else:
                        self.profile_data[key] = value
            
            # Update timestamp
            self.profile_data['last_updated'] = time.time()
            
            # Save updated profile
            self._save_profile_to_file()
            
            logger.debug("Updated profile data", updates=list(updates.keys()))
            
        except Exception as e:
            logger.error("Failed to update profile data", error=str(e))
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """Get current profile statistics."""
        if not self.profile_data:
            return {}
        
        return {
            'profile_id': self.profile_id,
            'created_at': self.profile_data.get('created_at'),
            'last_updated': self.profile_data.get('last_updated'),
            'browsing_history_count': len(self.profile_data.get('browsing_history', [])),
            'bookmarks_count': len(self.profile_data.get('bookmarks', [])),
            'downloads_count': len(self.profile_data.get('downloads', [])),
            'search_history_count': len(self.profile_data.get('search_history', [])),
            'demographics': self.profile_data.get('demographics', {}),
            'browsing_patterns': self.profile_data.get('browsing_patterns', {})
        }
    
    def cleanup_old_profiles(self, max_age_days: int = 30) -> None:
        """
        Clean up old profile files.
        
        Args:
            max_age_days: Maximum age of profiles to keep
        """
        try:
            profile_files = list(self.profile_dir.glob("profile_*.json"))
            current_time = time.time()
            max_age_seconds = max_age_days * 86400
            
            cleaned_count = 0
            for profile_file in profile_files:
                file_age = current_time - profile_file.stat().st_mtime
                if file_age > max_age_seconds:
                    profile_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info("Cleaned up old profile files", 
                           cleaned_count=cleaned_count,
                           max_age_days=max_age_days)
            
        except Exception as e:
            logger.error("Failed to cleanup old profiles", error=str(e))
