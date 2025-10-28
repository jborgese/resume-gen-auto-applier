# src/cookie_manager.py

import json
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CookieManager:
    """
    Manages LinkedIn session cookies for persistent login.
    Saves cookies to disk after successful manual login,
    and reloads them for subsequent automated runs.
    """
    
    def __init__(self, cookies_file: str = "linkedin_cookies.json"):
        """
        Initialize the cookie manager.
        
        Args:
            cookies_file: Path to the JSON file where cookies will be stored
        """
        # Store cookies in the project root directory
        project_root = Path(__file__).parent.parent
        self.cookies_file = project_root / cookies_file
        self.cookies: List[dict] = []
        
    def save_cookies(self, cookies: List[dict]) -> bool:
        """
        Save cookies to disk.
        
        Args:
            cookies: List of cookie dictionaries from Playwright
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save cookies to file
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
            print(f"[INFO] Saved {len(cookies)} cookies to {self.cookies_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            print(f"[ERROR] Failed to save cookies: {e}")
            return False
    
    def load_cookies(self) -> Optional[List[dict]]:
        """
        Load cookies from disk and validate them.
        
        Returns:
            List of valid cookie dictionaries if file exists, None otherwise
        """
        if not self.cookies_file.exists():
            logger.debug(f"Cookie file not found: {self.cookies_file}")
            return None
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Validate and filter expired cookies
            valid_cookies = self._validate_cookies(cookies)
            
            if len(valid_cookies) < len(cookies):
                expired_count = len(cookies) - len(valid_cookies)
                logger.warning(f"Filtered out {expired_count} expired cookies")
                print(f"[WARN] Filtered out {expired_count} expired cookies")
                
                # Save cleaned cookies back to file
                if valid_cookies:
                    self.save_cookies(valid_cookies)
                else:
                    # All cookies expired, delete file
                    self.delete_cookies()
                    logger.info("All cookies expired - deleted cookie file")
                    print("[INFO] All cookies expired - will need fresh login")
                    return None
            
            # Check cookie freshness (LinkedIn cookies older than 7 days may be suspicious)
            cookie_age = self._get_cookie_age(cookies)
            if cookie_age > 7 * 24 * 3600:  # 7 days in seconds
                logger.warning(f"Cookies are {cookie_age / (24*3600):.1f} days old - may need refresh")
                print(f"[WARN] Cookies are {cookie_age / (24*3600):.1f} days old - LinkedIn may require refresh")
            
            logger.info(f"Loaded {len(valid_cookies)} valid cookies from {self.cookies_file}")
            print(f"[INFO] Loaded {len(valid_cookies)} valid cookies from {self.cookies_file}")
            return valid_cookies
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            print(f"[WARN] Failed to load cookies: {e}")
            return None
    
    def _validate_cookies(self, cookies: List[dict]) -> List[dict]:
        """
        Validate cookies and filter out expired ones.
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            List of valid (non-expired) cookies
        """
        valid_cookies = []
        current_time = time.time()
        
        for cookie in cookies:
            # Check expiration
            expires = cookie.get('expires', -1)
            
            # -1 means session cookie (expires when browser closes)
            if expires == -1:
                valid_cookies.append(cookie)
                continue
            
            # Check if cookie is expired
            if expires > current_time:
                valid_cookies.append(cookie)
            else:
                logger.debug(f"Cookie '{cookie.get('name', 'unknown')}' expired")
        
        return valid_cookies
    
    def _get_cookie_age(self, cookies: List[dict]) -> float:
        """
        Get the age of the oldest cookie (based on file modification time).
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            Age in seconds, or 0 if file doesn't exist
        """
        if not self.cookies_file.exists():
            return 0
        
        file_mtime = self.cookies_file.stat().st_mtime
        return time.time() - file_mtime
    
    def prepare_cookies_for_playwright(self, cookies: List[dict], url: str = "https://www.linkedin.com") -> List[dict]:
        """
        Prepare cookies for Playwright by ensuring required fields are present.
        
        Args:
            cookies: List of cookie dictionaries
            url: URL to associate cookies with (required by Playwright)
            
        Returns:
            List of cookies with required Playwright fields
        """
        prepared_cookies = []
        
        for cookie in cookies:
            # Ensure required fields exist
            prepared_cookie = {
                'name': cookie.get('name', ''),
                'value': cookie.get('value', ''),
                'domain': cookie.get('domain', '.linkedin.com'),
                'path': cookie.get('path', '/'),
                'expires': cookie.get('expires', -1),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', True),
                'sameSite': cookie.get('sameSite', 'None')
            }
            
            # Playwright requires 'url' field when adding cookies
            # Normalize domain to ensure proper matching
            domain = prepared_cookie['domain']
            if domain.startswith('.'):
                # Use www subdomain for LinkedIn
                prepared_cookie['url'] = f"https://www{domain[1:]}/"
            else:
                prepared_cookie['url'] = f"https://{domain}/"
            
            prepared_cookies.append(prepared_cookie)
        
        return prepared_cookies
    
    def refresh_cookies_if_needed(self, context, page) -> bool:
        """
        Refresh cookies if they're getting stale during a session.
        Enhanced to handle GraphQL authentication issues.
        
        Args:
            context: Playwright browser context
            page: Playwright page object
            
        Returns:
            True if cookies were refreshed, False otherwise
        """
        try:
            # Check if cookies need refresh (after 15 minutes of use, not 30)
            if self.cookies_file.exists():
                # Get cookie file age
                file_mtime = self.cookies_file.stat().st_mtime
                cookie_age = time.time() - file_mtime
                
                # If cookies are old but session is still valid, refresh them
                if cookie_age > 15 * 60:  # Reduced to 15 minutes for better session management
                    current_cookies = context.cookies()
                    if current_cookies:
                        cookies_dict = [dict(c) for c in current_cookies]
                        
                        # Filter to only LinkedIn cookies
                        linkedin_cookies = [
                            c for c in cookies_dict 
                            if 'linkedin.com' in c.get('domain', '') or 'linkedin.com' in c.get('url', '')
                        ]
                        
                        if linkedin_cookies:
                            self.save_cookies(linkedin_cookies)
                            logger.info("Refreshed cookies during session")
                            print("[INFO] Refreshed session cookies")
                            return True
                            
            # Also check for GraphQL authentication issues
            try:
                # Check if we're getting GraphQL errors by looking at page content
                page_content = page.inner_text("body").lower()
                if "something went wrong" in page_content or "try refreshing" in page_content:
                    logger.warning("GraphQL error detected - refreshing cookies")
                    print("[WARN] GraphQL error detected - attempting cookie refresh")
                    
                    # Force cookie refresh
                    current_cookies = context.cookies()
                    if current_cookies:
                        cookies_dict = [dict(c) for c in current_cookies]
                        linkedin_cookies = [
                            c for c in cookies_dict 
                            if 'linkedin.com' in c.get('domain', '') or 'linkedin.com' in c.get('url', '')
                        ]
                        
                        if linkedin_cookies:
                            self.save_cookies(linkedin_cookies)
                            logger.info("Refreshed cookies due to GraphQL error")
                            print("[INFO] Refreshed cookies due to GraphQL error")
                            return True
                            
            except Exception as e:
                logger.debug(f"Could not check for GraphQL errors: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to refresh cookies: {e}")
        
        return False
    
    def delete_cookies(self) -> bool:
        """
        Delete the cookies file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.cookies_file.exists():
                self.cookies_file.unlink()
                logger.info(f"Deleted cookie file: {self.cookies_file}")
                print(f"[INFO] Deleted cookie file: {self.cookies_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete cookies: {e}")
            return False
        return False
    
    def cookies_exist(self) -> bool:
        """
        Check if cookies file exists.
        
        Returns:
            True if file exists, False otherwise
        """
        return self.cookies_file.exists()


