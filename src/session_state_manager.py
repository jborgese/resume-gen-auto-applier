# src/session_state_manager.py

import json
import time
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page
from src.logging_config import get_logger

logger = get_logger(__name__)


class SessionStateManager:
    """
    Manages session state without using cookies to avoid automation detection.
    Uses localStorage, sessionStorage, and file-based persistence.
    """
    
    def __init__(self, profile_dir: Path):
        """
        Initialize the session state manager.
        
        Args:
            profile_dir: Directory to store session state data
        """
        self.profile_dir = profile_dir
        self.profile_dir.mkdir(exist_ok=True)
        
        # Session data
        self.session_data = {}
        self.fingerprint = None
        self.session_id = self._generate_session_id()
        
        # State tracking
        self.state_version = 1
        self.last_save_time = time.time()
        self.save_interval = 300  # 5 minutes
        
        logger.info("SessionStateManager initialized", 
                   session_id=self.session_id,
                   profile_dir=str(self.profile_dir))
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def generate_session_fingerprint(self, page: Page) -> str:
        """
        Generate unique session fingerprint based on browser characteristics.
        
        Args:
            page: Playwright page object
            
        Returns:
            Unique session fingerprint
        """
        try:
            # Get browser characteristics
            characteristics = page.evaluate("""
                () => {
                    return {
                        userAgent: navigator.userAgent,
                        language: navigator.language,
                        platform: navigator.platform,
                        screenWidth: screen.width,
                        screenHeight: screen.height,
                        colorDepth: screen.colorDepth,
                        pixelDepth: screen.pixelDepth,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        cookieEnabled: navigator.cookieEnabled,
                        doNotTrack: navigator.doNotTrack,
                        hardwareConcurrency: navigator.hardwareConcurrency,
                        deviceMemory: navigator.deviceMemory,
                        connection: navigator.connection ? {
                            effectiveType: navigator.connection.effectiveType,
                            rtt: navigator.connection.rtt,
                            downlink: navigator.connection.downlink
                        } : null
                    };
                }
            """)
            
            # Create fingerprint hash
            fingerprint_data = json.dumps(characteristics, sort_keys=True)
            fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            self.fingerprint = fingerprint
            
            logger.debug("Generated session fingerprint", 
                        fingerprint=fingerprint[:16] + "...")
            
            return fingerprint
            
        except Exception as e:
            logger.error("Failed to generate session fingerprint", error=str(e))
            # Fallback fingerprint
            self.fingerprint = hashlib.sha256(str(time.time()).encode()).hexdigest()
            return self.fingerprint
    
    def save_session_state(self, page: Page, additional_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Save session state using multiple mechanisms.
        
        Args:
            page: Playwright page object
            additional_data: Additional data to include in session state
        """
        try:
            # Generate fingerprint if not exists
            if not self.fingerprint:
                self.generate_session_fingerprint(page)
            
            # Collect current session data
            current_time = time.time()
            
            session_data = {
                'session_id': self.session_id,
                'fingerprint': self.fingerprint,
                'timestamp': current_time,
                'version': self.state_version,
                'page_url': page.url,
                'page_title': page.title(),
                'viewport_size': page.viewport_size,
                'user_agent': page.evaluate("() => navigator.userAgent"),
                'language': page.evaluate("() => navigator.language"),
                'timezone': page.evaluate("() => Intl.DateTimeFormat().resolvedOptions().timeZone"),
                'screen_resolution': page.evaluate("() => `${screen.width}x${screen.height}`"),
                'color_depth': page.evaluate("() => screen.colorDepth"),
                'cookie_enabled': page.evaluate("() => navigator.cookieEnabled"),
                'do_not_track': page.evaluate("() => navigator.doNotTrack"),
                'hardware_concurrency': page.evaluate("() => navigator.hardwareConcurrency"),
                'device_memory': page.evaluate("() => navigator.deviceMemory"),
                'connection_info': page.evaluate("""
                    () => navigator.connection ? {
                        effectiveType: navigator.connection.effectiveType,
                        rtt: navigator.connection.rtt,
                        downlink: navigator.connection.downlink
                    } : null
                """),
                'local_storage_keys': page.evaluate("""
                    () => {
                        const keys = [];
                        for (let i = 0; i < localStorage.length; i++) {
                            keys.push(localStorage.key(i));
                        }
                        return keys;
                    }
                """),
                'session_storage_keys': page.evaluate("""
                    () => {
                        const keys = [];
                        for (let i = 0; i < sessionStorage.length; i++) {
                            keys.push(sessionStorage.key(i));
                        }
                        return keys;
                    }
                """),
                'additional_data': additional_data or {}
            }
            
            # Save to localStorage
            self._save_to_local_storage(page, session_data)
            
            # Save to sessionStorage
            self._save_to_session_storage(page, session_data)
            
            # Save to file
            self._save_to_file(session_data)
            
            # Update tracking
            self.session_data = session_data
            self.last_save_time = current_time
            
            logger.debug("Saved session state", 
                        session_id=self.session_id,
                        fingerprint=self.fingerprint[:16] + "...")
            
        except Exception as e:
            logger.error("Failed to save session state", error=str(e))
    
    def _save_to_local_storage(self, page: Page, session_data: Dict[str, Any]) -> None:
        """Save session data to localStorage."""
        try:
            # Save main session data
            page.evaluate(f"""
                localStorage.setItem('stealth_session_state', JSON.stringify({json.dumps(session_data)}));
                localStorage.setItem('session_timestamp', '{session_data['timestamp']}');
                localStorage.setItem('session_fingerprint', '{session_data['fingerprint']}');
            """)
            
            logger.debug("Saved session state to localStorage")
            
        except Exception as e:
            logger.debug("Could not save to localStorage", error=str(e))
    
    def _save_to_session_storage(self, page: Page, session_data: Dict[str, Any]) -> None:
        """Save session data to sessionStorage."""
        try:
            # Save essential session data
            essential_data = {
                'session_id': session_data['session_id'],
                'fingerprint': session_data['fingerprint'],
                'timestamp': session_data['timestamp'],
                'page_url': session_data['page_url']
            }
            
            page.evaluate(f"""
                sessionStorage.setItem('stealth_session', JSON.stringify({json.dumps(essential_data)}));
                sessionStorage.setItem('session_marker', '{session_data['session_id']}');
            """)
            
            logger.debug("Saved session state to sessionStorage")
            
        except Exception as e:
            logger.debug("Could not save to sessionStorage", error=str(e))
    
    def _save_to_file(self, session_data: Dict[str, Any]) -> None:
        """Save session data to file."""
        try:
            session_file = self.profile_dir / f"session_{self.session_id}.json"
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.debug("Saved session state to file", 
                        file_path=str(session_file))
            
        except Exception as e:
            logger.error("Failed to save session state to file", error=str(e))
    
    def restore_session_state(self, page: Page) -> bool:
        """
        Restore session state from multiple sources.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if session state was restored successfully, False otherwise
        """
        try:
            # Try to restore from localStorage first
            if self._restore_from_local_storage(page):
                logger.info("Restored session state from localStorage")
                return True
            
            # Try to restore from sessionStorage
            if self._restore_from_session_storage(page):
                logger.info("Restored session state from sessionStorage")
                return True
            
            # Try to restore from file
            if self._restore_from_file(page):
                logger.info("Restored session state from file")
                return True
            
            logger.debug("No session state found to restore")
            return False
            
        except Exception as e:
            logger.error("Failed to restore session state", error=str(e))
            return False
    
    def _restore_from_local_storage(self, page: Page) -> bool:
        """Restore session state from localStorage."""
        try:
            session_data = page.evaluate("""
                const data = localStorage.getItem('stealth_session_state');
                return data ? JSON.parse(data) : null;
            """)
            
            if session_data and self._validate_session_data(session_data):
                self.session_data = session_data
                self.session_id = session_data['session_id']
                self.fingerprint = session_data['fingerprint']
                return True
            
            return False
            
        except Exception as e:
            logger.debug("Could not restore from localStorage", error=str(e))
            return False
    
    def _restore_from_session_storage(self, page: Page) -> bool:
        """Restore session state from sessionStorage."""
        try:
            session_data = page.evaluate("""
                const data = sessionStorage.getItem('stealth_session');
                return data ? JSON.parse(data) : null;
            """)
            
            if session_data and self._validate_session_data(session_data):
                self.session_data = session_data
                self.session_id = session_data['session_id']
                self.fingerprint = session_data['fingerprint']
                return True
            
            return False
            
        except Exception as e:
            logger.debug("Could not restore from sessionStorage", error=str(e))
            return False
    
    def _restore_from_file(self, page: Page) -> bool:
        """Restore session state from file."""
        try:
            # Find the most recent session file
            session_files = list(self.profile_dir.glob("session_*.json"))
            if not session_files:
                return False
            
            # Get the most recent session file
            latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                session_data = json.load(f)
            
            if self._validate_session_data(session_data):
                self.session_data = session_data
                self.session_id = session_data['session_id']
                self.fingerprint = session_data['fingerprint']
                return True
            
            return False
            
        except Exception as e:
            logger.debug("Could not restore from file", error=str(e))
            return False
    
    def _validate_session_data(self, session_data: Dict[str, Any]) -> bool:
        """
        Validate session data integrity.
        
        Args:
            session_data: Session data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['session_id', 'fingerprint', 'timestamp']
            for field in required_fields:
                if field not in session_data:
                    return False
            
            # Check timestamp freshness (max 24 hours)
            current_time = time.time()
            session_age = current_time - session_data['timestamp']
            if session_age > 86400:  # 24 hours
                logger.debug("Session data too old", age_hours=session_age / 3600)
                return False
            
            # Check fingerprint consistency
            if self.fingerprint and session_data['fingerprint'] != self.fingerprint:
                logger.debug("Session fingerprint mismatch")
                return False
            
            return True
            
        except Exception as e:
            logger.debug("Could not validate session data", error=str(e))
            return False
    
    def validate_session_state(self, page: Page) -> bool:
        """
        Validate current session state.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if session state is valid, False otherwise
        """
        try:
            # Generate current fingerprint
            current_fingerprint = self.generate_session_fingerprint(page)
            
            # Check if fingerprint matches stored fingerprint
            if self.fingerprint and current_fingerprint != self.fingerprint:
                logger.warning("Session fingerprint mismatch - possible session hijacking")
                return False
            
            # Check if session data exists
            if not self.session_data:
                logger.debug("No session data to validate")
                return False
            
            # Check timestamp freshness
            current_time = time.time()
            session_age = current_time - self.session_data.get('timestamp', 0)
            if session_age > 86400:  # 24 hours
                logger.debug("Session too old", age_hours=session_age / 3600)
                return False
            
            logger.debug("Session state validation passed")
            return True
            
        except Exception as e:
            logger.error("Failed to validate session state", error=str(e))
            return False
    
    def update_session_state(self, page: Page, updates: Dict[str, Any]) -> None:
        """
        Update session state with new information.
        
        Args:
            page: Playwright page object
            updates: Dictionary of updates to apply
        """
        try:
            if not self.session_data:
                self.session_data = {}
            
            # Update session data
            for key, value in updates.items():
                self.session_data[key] = value
            
            # Update timestamp
            self.session_data['timestamp'] = time.time()
            self.session_data['version'] = self.state_version + 1
            self.state_version += 1
            
            # Save updated state
            self.save_session_state(page)
            
            logger.debug("Updated session state", updates=list(updates.keys()))
            
        except Exception as e:
            logger.error("Failed to update session state", error=str(e))
    
    def cleanup_expired_state(self) -> None:
        """Clean up expired session data."""
        try:
            current_time = time.time()
            cleaned_count = 0
            
            # Clean up session files
            session_files = list(self.profile_dir.glob("session_*.json"))
            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session_age = current_time - session_data.get('timestamp', 0)
                    if session_age > 86400:  # 24 hours
                        session_file.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.debug("Could not process session file", 
                               file_path=str(session_file), error=str(e))
            
            if cleaned_count > 0:
                logger.info("Cleaned up expired session files", 
                           cleaned_count=cleaned_count)
            
        except Exception as e:
            logger.error("Failed to cleanup expired state", error=str(e))
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            'session_id': self.session_id,
            'fingerprint': self.fingerprint[:16] + "..." if self.fingerprint else None,
            'state_version': self.state_version,
            'last_save_time': self.last_save_time,
            'session_data_keys': list(self.session_data.keys()) if self.session_data else [],
            'profile_dir': str(self.profile_dir),
            'session_age': time.time() - self.session_data.get('timestamp', 0) if self.session_data else 0
        }
    
    def export_session_state(self) -> Dict[str, Any]:
        """Export current session state for backup or transfer."""
        return {
            'session_id': self.session_id,
            'fingerprint': self.fingerprint,
            'state_version': self.state_version,
            'session_data': self.session_data,
            'export_timestamp': time.time()
        }
    
    def import_session_state(self, exported_state: Dict[str, Any]) -> bool:
        """
        Import session state from backup or transfer.
        
        Args:
            exported_state: Exported session state data
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            # Validate exported state
            required_fields = ['session_id', 'fingerprint', 'session_data']
            for field in required_fields:
                if field not in exported_state:
                    logger.error("Invalid exported state - missing field", field=field)
                    return False
            
            # Import state
            self.session_id = exported_state['session_id']
            self.fingerprint = exported_state['fingerprint']
            self.state_version = exported_state.get('state_version', 1)
            self.session_data = exported_state['session_data']
            
            logger.info("Imported session state", 
                       session_id=self.session_id,
                       state_version=self.state_version)
            
            return True
            
        except Exception as e:
            logger.error("Failed to import session state", error=str(e))
            return False
    
    def reset_session_state(self) -> None:
        """Reset session state for new session."""
        self.session_data = {}
        self.session_id = self._generate_session_id()
        self.fingerprint = None
        self.state_version = 1
        self.last_save_time = time.time()
        
        logger.info("Reset session state", session_id=self.session_id)
