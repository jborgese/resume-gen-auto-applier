# src/stealth_integration.py

import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import BrowserContext, Page
from src.logging_config import get_logger
from src.stealth_session_manager import StealthSessionManager
from src.behavioral_pattern_simulator import BehavioralPatternSimulator
from src.persistent_profile_manager import PersistentProfileManager
from src.session_state_manager import SessionStateManager

logger = get_logger(__name__)


class StealthIntegration:
    """
    Integrates all stealth components seamlessly to provide comprehensive
    automation detection avoidance and realistic human behavior simulation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the stealth integration system.
        
        Args:
            config: Configuration dictionary for stealth components
        """
        self.config = config
        self.profile_dir = Path(config.get('profile_dir', 'stealth_profiles'))
        
        # Initialize components
        self.session_manager = StealthSessionManager(str(self.profile_dir))
        self.behavioral_simulator = None  # Will be initialized with personality
        self.profile_manager = PersistentProfileManager(self.profile_dir)
        self.state_manager = SessionStateManager(self.profile_dir)
        
        # Integration state
        self.initialized = False
        self.session_active = False
        self.last_activity_time = time.time()
        
        logger.info("StealthIntegration initialized", 
                   profile_dir=str(self.profile_dir),
                   config_keys=list(config.keys()))
    
    def initialize_stealth_session(self, context: BrowserContext) -> None:
        """
        Initialize complete stealth session with all components.
        
        Args:
            context: Browser context to initialize stealth session with
        """
        try:
            logger.info("Initializing complete stealth session")
            
            # Initialize behavioral simulator with personality
            self.behavioral_simulator = BehavioralPatternSimulator(
                self.session_manager.user_personality
            )
            
            # Create realistic browser profile
            self.profile_manager.create_realistic_profile()
            
            # Inject profile data into browser context
            self.profile_manager.inject_profile_data(context)
            
            # Defer session fingerprint generation until we have a proper page
            # This will be done in maintain_stealth_continuity when we have a real page
            
            # Mark as initialized
            self.initialized = True
            self.session_active = True
            
            logger.info("Stealth session initialized successfully",
                       session_id=self.session_manager.session_id,
                       profile_id=self.profile_manager.profile_id)
            
        except Exception as e:
            logger.error("Failed to initialize stealth session", error=str(e))
            raise
    
    def maintain_stealth_continuity(self, page: Page) -> None:
        """
        Maintain stealth continuity throughout the session.
        
        Args:
            page: Playwright page object
        """
        try:
            if not self.initialized:
                logger.warning("Stealth session not initialized")
                return
            
            # Update activity time
            self.last_activity_time = time.time()
            
            # Generate session fingerprint if not already done
            if not self.state_manager.fingerprint:
                try:
                    self.state_manager.generate_session_fingerprint(page)
                    logger.debug("Generated session fingerprint")
                except Exception as e:
                    logger.debug("Could not generate session fingerprint", error=str(e))
            
            # Maintain session continuity
            self.session_manager.maintain_session_continuity(page)
            
            # Simulate realistic behavioral patterns
            self._simulate_realistic_behavior(page)
            
            # Update session state
            self._update_session_state(page)
            
            # Handle stealth errors
            self._handle_stealth_errors(page)
            
            logger.debug("Maintained stealth continuity")
            
        except Exception as e:
            logger.error("Failed to maintain stealth continuity", error=str(e))
    
    def _simulate_realistic_behavior(self, page: Page) -> None:
        """Simulate realistic behavioral patterns."""
        try:
            if not self.behavioral_simulator:
                return
            
            # Simulate occasional distractions
            self.behavioral_simulator.simulate_distraction_events(page)
            
            # Simulate micro-interactions
            if random.random() < 0.1:  # 10% chance
                self._simulate_micro_interaction(page)
            
            # Simulate page checking behavior
            if random.random() < 0.05:  # 5% chance
                self._simulate_page_checking(page)
                
        except Exception as e:
            logger.debug("Could not simulate realistic behavior", error=str(e))
    
    def _simulate_micro_interaction(self, page: Page) -> None:
        """Simulate realistic micro-interactions."""
        try:
            viewport = page.viewport_size
            if viewport:
                # Small mouse movement
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
    
    def _update_session_state(self, page: Page) -> None:
        """Update session state with current information."""
        try:
            # Check if it's time to save session state
            current_time = time.time()
            if current_time - self.state_manager.last_save_time > self.state_manager.save_interval:
                # Collect additional data
                additional_data = {
                    'behavioral_stats': self.behavioral_simulator.get_behavioral_stats() if self.behavioral_simulator else {},
                    'session_stats': self.session_manager.get_session_stats(),
                    'profile_stats': self.profile_manager.get_profile_stats(),
                    'activity_time': self.last_activity_time
                }
                
                # Save session state
                self.state_manager.save_session_state(page, additional_data)
                
        except Exception as e:
            logger.debug("Could not update session state", error=str(e))
    
    def _handle_stealth_errors(self, page: Page) -> None:
        """Handle stealth-related errors gracefully."""
        try:
            # Check for common stealth-related errors
            page_content = page.inner_text("body").lower()
            
            # Check for automation detection messages
            detection_keywords = [
                'automated', 'bot', 'robot', 'suspicious activity',
                'unusual activity', 'security check', 'verification required'
            ]
            
            for keyword in detection_keywords:
                if keyword in page_content:
                    logger.warning("Potential automation detection detected", keyword=keyword)
                    self._handle_automation_detection(page)
                    break
                    
        except Exception as e:
            logger.debug("Could not handle stealth errors", error=str(e))
    
    def _handle_automation_detection(self, page: Page) -> None:
        """Handle potential automation detection."""
        try:
            logger.warning("Handling potential automation detection")
            
            # Simulate human-like response to detection
            if self.behavioral_simulator:
                # Simulate hesitation
                self.behavioral_simulator.simulate_hesitation_patterns(page, 'error_recovery')
                
                # Simulate distraction
                self.behavioral_simulator.simulate_distraction_events(page)
            
            # Update session state to reflect detection
            self.state_manager.update_session_state(page, {
                'detection_events': self.state_manager.session_data.get('detection_events', 0) + 1,
                'last_detection_time': time.time()
            })
            
        except Exception as e:
            logger.error("Failed to handle automation detection", error=str(e))
    
    def simulate_realistic_login_flow(self, page: Page, email: str, password: str) -> bool:
        """
        Simulate realistic login flow with all stealth components.
        
        Args:
            page: Playwright page object
            email: Email address for login
            password: Password for login
            
        Returns:
            True if login flow was simulated successfully, False otherwise
        """
        try:
            logger.info("Starting realistic login flow with stealth integration")
            
            # Use session manager for login simulation
            success = self.session_manager.simulate_realistic_login_flow(page, email, password)
            
            if success:
                # Update session state
                self.state_manager.update_session_state(page, {
                    'login_attempts': self.state_manager.session_data.get('login_attempts', 0) + 1,
                    'last_login_time': time.time(),
                    'login_success': True
                })
                
                logger.info("Realistic login flow completed successfully")
            
            return success
            
        except Exception as e:
            logger.error("Failed to simulate realistic login flow", error=str(e))
            return False
    
    def restore_session_state(self, page: Page) -> bool:
        """
        Restore session state from multiple sources.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if session state was restored successfully, False otherwise
        """
        try:
            logger.info("Attempting to restore session state")
            
            # Try to restore from session manager
            if self.session_manager.restore_session_state(page):
                logger.info("Restored session state from session manager")
                
                # Reinitialize behavioral simulator with restored personality
                self.behavioral_simulator = BehavioralPatternSimulator(
                    self.session_manager.user_personality
                )
                
                # Restore state manager
                if self.state_manager.restore_session_state(page):
                    logger.info("Restored state manager session")
                
                # Mark session as active
                self.session_active = True
                
                return True
            
            # Try to restore from state manager
            if self.state_manager.restore_session_state(page):
                logger.info("Restored session state from state manager")
                
                # Try to restore profile
                profile_data = self.profile_manager.load_profile_from_file()
                if profile_data:
                    logger.info("Restored profile data")
                
                self.session_active = True
                return True
            
            logger.info("No session state found to restore")
            return False
            
        except Exception as e:
            logger.error("Failed to restore session state", error=str(e))
            return False
    
    def save_session_state(self, page: Page) -> None:
        """
        Save session state using all available mechanisms.
        
        Args:
            page: Playwright page object
        """
        try:
            logger.info("Saving session state")
            
            # Save session manager state
            self.session_manager.save_session_state(page)
            
            # Save state manager state
            additional_data = {
                'behavioral_stats': self.behavioral_simulator.get_behavioral_stats() if self.behavioral_simulator else {},
                'session_stats': self.session_manager.get_session_stats(),
                'profile_stats': self.profile_manager.get_profile_stats(),
                'integration_stats': self.get_integration_stats()
            }
            
            self.state_manager.save_session_state(page, additional_data)
            
            # Update profile data
            self.profile_manager.update_profile_data({
                'last_session_end': time.time(),
                'session_duration': time.time() - self.last_activity_time,
                'total_sessions': self.profile_manager.profile_data.get('total_sessions', 0) + 1
            })
            
            logger.info("Session state saved successfully")
            
        except Exception as e:
            logger.error("Failed to save session state", error=str(e))
    
    def handle_stealth_errors(self, error: Exception) -> bool:
        """
        Handle stealth-related errors gracefully.
        
        Args:
            error: Exception to handle
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            error_type = type(error).__name__
            error_message = str(error)
            
            logger.warning("Handling stealth error", 
                          error_type=error_type,
                          error_message=error_message)
            
            # Handle specific error types
            if 'timeout' in error_message.lower():
                return self._handle_timeout_error(error)
            elif 'navigation' in error_message.lower():
                return self._handle_navigation_error(error)
            elif 'element' in error_message.lower():
                return self._handle_element_error(error)
            else:
                return self._handle_generic_error(error)
                
        except Exception as e:
            logger.error("Failed to handle stealth error", error=str(e))
            return False
    
    def _handle_timeout_error(self, error: Exception) -> bool:
        """Handle timeout errors."""
        try:
            logger.info("Handling timeout error")
            
            # Simulate human-like response to timeout
            if self.behavioral_simulator:
                # Simulate hesitation
                time.sleep(random.uniform(1, 3))
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle timeout error", error=str(e))
            return False
    
    def _handle_navigation_error(self, error: Exception) -> bool:
        """Handle navigation errors."""
        try:
            logger.info("Handling navigation error")
            
            # Simulate human-like response to navigation error
            if self.behavioral_simulator:
                # Simulate distraction
                time.sleep(random.uniform(2, 5))
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle navigation error", error=str(e))
            return False
    
    def _handle_element_error(self, error: Exception) -> bool:
        """Handle element interaction errors."""
        try:
            logger.info("Handling element error")
            
            # Simulate human-like response to element error
            if self.behavioral_simulator:
                # Simulate hesitation and retry
                time.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle element error", error=str(e))
            return False
    
    def _handle_generic_error(self, error: Exception) -> bool:
        """Handle generic errors."""
        try:
            logger.info("Handling generic error")
            
            # Simulate human-like response to generic error
            if self.behavioral_simulator:
                # Simulate confusion and pause
                time.sleep(random.uniform(1, 4))
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle generic error", error=str(e))
            return False
    
    def cleanup_stealth_session(self) -> None:
        """Clean up stealth session resources."""
        try:
            logger.info("Cleaning up stealth session")
            
            # Clean up session manager
            self.session_manager.cleanup_session()
            
            # Clean up state manager
            self.state_manager.cleanup_expired_state()
            
            # Clean up profile manager
            self.profile_manager.cleanup_old_profiles()
            
            # Reset integration state
            self.initialized = False
            self.session_active = False
            
            logger.info("Stealth session cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup stealth session", error=str(e))
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get current integration statistics."""
        return {
            'initialized': self.initialized,
            'session_active': self.session_active,
            'last_activity_time': self.last_activity_time,
            'session_manager_stats': self.session_manager.get_session_stats(),
            'behavioral_stats': self.behavioral_simulator.get_behavioral_stats() if self.behavioral_simulator else {},
            'profile_stats': self.profile_manager.get_profile_stats(),
            'state_manager_stats': self.state_manager.get_session_stats(),
            'config': self.config
        }
    
    def reset_integration(self) -> None:
        """Reset integration for new session."""
        try:
            logger.info("Resetting stealth integration")
            
            # Reset all components
            self.session_manager = StealthSessionManager(str(self.profile_dir))
            self.behavioral_simulator = None
            self.profile_manager = PersistentProfileManager(self.profile_dir)
            self.state_manager = SessionStateManager(self.profile_dir)
            
            # Reset integration state
            self.initialized = False
            self.session_active = False
            self.last_activity_time = time.time()
            
            logger.info("Stealth integration reset completed")
            
        except Exception as e:
            logger.error("Failed to reset stealth integration", error=str(e))
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_stealth_session()
