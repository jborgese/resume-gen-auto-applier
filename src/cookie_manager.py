# src/cookie_manager.py

import json
import os
from pathlib import Path
from typing import List, Optional
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
        Load cookies from disk.
        
        Returns:
            List of cookie dictionaries if file exists, None otherwise
        """
        if not self.cookies_file.exists():
            logger.debug(f"Cookie file not found: {self.cookies_file}")
            return None
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            logger.info(f"Loaded {len(cookies)} cookies from {self.cookies_file}")
            print(f"[INFO] Loaded {len(cookies)} cookies from {self.cookies_file}")
            return cookies
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            print(f"[WARN] Failed to load cookies: {e}")
            return None
    
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


