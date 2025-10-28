# src/human_behavior.py
"""
Enhanced human behavior simulation for LinkedIn automation.
Mimics natural human interactions to avoid bot detection.
"""

import time
import random
import math
from typing import Optional, Tuple, List
from playwright.sync_api import Page, Locator
from src.logging_config import get_logger, debug_checkpoint

logger = get_logger(__name__)


class HumanBehavior:
    """Enhanced human behavior simulation for web automation."""
    
    # Configuration for human-like delays
    READING_SPEED_WPM = 200  # Words per minute for reading
    TYPING_SPEED_WPM = 40   # Words per minute for typing
    MIN_READ_TIME = 0.5      # Minimum time to read (seconds)
    MAX_READ_TIME = 3.0      # Maximum time to read (seconds)
    
    # Enhanced timing patterns
    MOUSE_MOVEMENT_CHANCE = 0.4  # 40% chance for random mouse movement
    HESITATION_CHANCE = 0.25     # 25% chance for hesitation
    SCROLL_CHANCE = 0.3          # 30% chance for scrolling
    REVIEW_CHANCE = 0.2          # 20% chance for form review
    
    @staticmethod
    def enhanced_mouse_movement(page: Page, element_bbox: Optional[dict] = None) -> None:
        """
        Enhanced mouse movement simulation with more realistic patterns.
        
        Args:
            page: Playwright page object
            element_bbox: Optional bounding box of target element
        """
        if random.random() < HumanBehavior.MOUSE_MOVEMENT_CHANCE:
            viewport = page.viewport_size
            if viewport:
                # Create more natural mouse path
                current_x, current_y = 0, 0
                try:
                    # Get current mouse position (approximate)
                    current_x = viewport['width'] // 2
                    current_y = viewport['height'] // 2
                except:
                    pass
                
                # Generate target position
                target_x = random.randint(50, viewport['width'] - 50)
                target_y = random.randint(50, viewport['height'] - 50)
                
                # Create curved path (more human-like)
                steps = random.randint(8, 20)
                for i in range(steps):
                    # Bezier-like curve for more natural movement
                    t = i / steps
                    # Add some randomness to the curve
                    curve_offset_x = random.randint(-30, 30)
                    curve_offset_y = random.randint(-30, 30)
                    
                    x = int(current_x + (target_x - current_x) * t + curve_offset_x * math.sin(t * math.pi))
                    y = int(current_y + (target_y - current_y) * t + curve_offset_y * math.cos(t * math.pi))
                    
                    # Ensure coordinates are within viewport
                    x = max(0, min(viewport['width'], x))
                    y = max(0, min(viewport['height'], y))
                    
                    page.mouse.move(x, y)
                    time.sleep(random.uniform(0.01, 0.05))  # Small delays between movements
                
                # Final pause at target
                time.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    def simulate_realistic_typing(page: Page, locator: Locator, text: str, error_rate: float = 0.03) -> None:
        """
        Enhanced typing simulation with more realistic patterns.
        
        Args:
            page: Playwright page object
            locator: Locator for the input field
            text: Text to type
            error_rate: Probability of making a typo (reduced to 3%)
        """
        # Focus the input first with human-like delay
        locator.focus()
        time.sleep(random.uniform(0.2, 0.5))
        
        # Clear existing content with human-like delay
        locator.fill("")
        time.sleep(random.uniform(0.3, 0.7))
        
        # Type with more realistic patterns
        words = text.split()
        for word_idx, word in enumerate(words):
            # Pause between words (longer for longer words)
            if word_idx > 0:
                word_pause = random.uniform(0.15, 0.4) + (len(word) * 0.01)
                time.sleep(word_pause)
            
            # Type word character by character with variable delays
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
                
                # Add occasional longer pauses (thinking, re-reading)
                if random.random() < 0.08:  # 8% chance
                    base_delay += random.uniform(0.4, 1.2)
                
                # Faster typing for common patterns
                if char_idx > 0 and word[char_idx-1:char_idx+1] in ['th', 'he', 'in', 'er', 'an']:
                    base_delay *= 0.7
                
                locator.type(char, delay=base_delay)
            
            # Simulate occasional typo correction (more realistic)
            if random.random() < error_rate:
                # Pause as if noticing the error
                time.sleep(random.uniform(0.3, 0.8))
                
                # Backspace with variable speed
                backspace_count = random.randint(1, min(3, len(word)))
                for _ in range(backspace_count):
                    locator.press("Backspace")
                    time.sleep(random.uniform(0.1, 0.25))
                
                # Retype with slightly faster speed
                retype_text = word[-backspace_count:]
                for char in retype_text:
                    locator.type(char, delay=random.uniform(0.05, 0.12))
        
        # Final pause before moving on (longer for longer text)
        final_pause = random.uniform(0.3, 0.8) + (len(text) * 0.01)
        time.sleep(final_pause)
    
    @staticmethod
    def enhanced_click_simulation(page: Page, locator: Locator, move_to_element: bool = True) -> None:
        """
        Enhanced click simulation with more realistic behavior.
        
        Args:
            page: Playwright page object
            locator: Locator for element to click
            move_to_element: Whether to move mouse to element before clicking
        """
        if move_to_element:
            # Scroll element into view with human-like behavior
            locator.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Enhanced mouse movement to element
            try:
                bbox = locator.bounding_box()
                if bbox:
                    # Move mouse to element with realistic approach
                    target_x = bbox['x'] + bbox['width'] / 2 + random.randint(-8, 8)
                    target_y = bbox['y'] + bbox['height'] / 2 + random.randint(-8, 8)
                    
                    # Create realistic approach path
                    viewport = page.viewport_size
                    if viewport:
                        current_x = random.randint(0, viewport['width'])
                        current_y = random.randint(0, viewport['height'])
                        
                        # Move in steps with slight overshoot and correction
                        steps = random.randint(5, 12)
                        for i in range(steps):
                            t = i / steps
                            # Add slight overshoot and correction
                            overshoot_x = random.randint(-15, 15) if i > steps//2 else 0
                            overshoot_y = random.randint(-15, 15) if i > steps//2 else 0
                            
                            x = int(current_x + (target_x - current_x) * t + overshoot_x)
                            y = int(current_y + (target_y - current_y) * t + overshoot_y)
                            
                            page.mouse.move(x, y)
                            time.sleep(random.uniform(0.02, 0.08))
                    
                    # Hover pause (humans don't click instantly)
                    time.sleep(random.uniform(0.2, 0.6))
                    
            except Exception:
                # Fallback to simple hover
                locator.hover()
                time.sleep(random.uniform(0.2, 0.5))
        
        # Click with realistic delay
        locator.click(delay=random.randint(80, 200))
        
        # Post-click pause (humans often pause after clicking)
        time.sleep(random.uniform(0.1, 0.4))
    
    @staticmethod
    def simulate_enhanced_hesitation(min_delay: float = 0.5, max_delay: float = 2.0) -> None:
        """
        Enhanced hesitation simulation with more realistic patterns.
        
        Args:
            min_delay: Minimum hesitation time
            max_delay: Maximum hesitation time
        """
        # Debug checkpoint for enhanced hesitation
        debug_checkpoint("simulate_enhanced_hesitation", 
                        min_delay=min_delay,
                        max_delay=max_delay)
        
        # Different types of hesitation
        hesitation_type = random.choice(['quick', 'normal', 'long', 'very_long'])
        
        if hesitation_type == 'quick':
            delay = random.uniform(min_delay, min_delay * 1.5)
        elif hesitation_type == 'normal':
            delay = random.uniform(min_delay, max_delay)
        elif hesitation_type == 'long':
            delay = random.uniform(max_delay, max_delay * 1.5)
        else:  # very_long
            delay = random.uniform(max_delay * 1.5, max_delay * 2.5)
        
        time.sleep(delay)
        
        # Debug checkpoint after hesitation
        debug_checkpoint("enhanced_hesitation_complete", 
                        hesitation_type=hesitation_type,
                        actual_delay=delay)
    
    @staticmethod
    def simulate_natural_viewport_interaction(page: Page) -> None:
        """
        Simulate natural viewport interactions (scrolling, looking around).
        
        Args:
            page: Playwright page object
        """
        interactions = []
        
        # Random scroll
        if random.random() < HumanBehavior.SCROLL_CHANCE:
            scroll_amount = random.randint(-300, 300)
            page.mouse.wheel(0, scroll_amount)
            interactions.append(f"scrolled {scroll_amount}px")
            time.sleep(random.uniform(0.4, 1.0))
        
        # Random mouse movement
        if random.random() < HumanBehavior.MOUSE_MOVEMENT_CHANCE:
            HumanBehavior.enhanced_mouse_movement(page)
            interactions.append("moved mouse")
        
        # Occasional page interaction simulation
        if random.random() < 0.1:  # 10% chance
            # Simulate checking something on the page
            viewport = page.viewport_size
            if viewport:
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.5, 1.5))
                interactions.append("checked page content")
        
        if interactions:
            # Log interactions for debugging
            pass  # Could add logging here if needed
    
    @staticmethod
    def simulate_form_interaction_sequence(page: Page, locators: List[Locator], values: List[str]) -> None:
        """
        Simulate realistic form filling sequence.
        
        Args:
            page: Playwright page object
            locators: List of form field locators
            values: List of values to fill
        """
        for i, (locator, value) in enumerate(zip(locators, values)):
            # Scroll to field
            locator.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Enhanced mouse movement to field
            HumanBehavior.enhanced_mouse_movement(page)
            
            # Fill field with realistic typing
            HumanBehavior.simulate_realistic_typing(page, locator, value)
            
            # Occasional field review
            if random.random() < HumanBehavior.REVIEW_CHANCE:
                time.sleep(random.uniform(0.5, 1.5))
                # Simulate re-reading the field
                locator.focus()
                time.sleep(random.uniform(0.2, 0.6))
            
            # Pause between fields
            if i < len(locators) - 1:
                HumanBehavior.simulate_enhanced_hesitation(0.3, 1.0)
    
    @staticmethod
    def simulate_page_reading(page: Page, content_selector: str = "body") -> None:
        """
        Simulate realistic page reading behavior.
        
        Args:
            page: Playwright page object
            content_selector: Selector for content to "read"
        """
        try:
            # Get page content
            content = page.inner_text(content_selector)
            if content:
                # Simulate reading time
                HumanBehavior.simulate_reading(content)
                
                # Occasional scrolling while reading
                if random.random() < 0.3:
                    scroll_amount = random.randint(-200, 200)
                    page.mouse.wheel(0, scroll_amount)
                    time.sleep(random.uniform(0.5, 1.0))
                
                # Occasional mouse movement while reading
                if random.random() < 0.2:
                    HumanBehavior.enhanced_mouse_movement(page)
                    
        except Exception:
            # Fallback to generic reading time
            time.sleep(random.uniform(1.0, 3.0))
    
    @staticmethod
    def simulate_realistic_reading(text: str, min_time: Optional[float] = None, max_time: Optional[float] = None) -> None:
        """
        Enhanced reading simulation with more realistic patterns.
        
        Args:
            text: Text content to simulate reading
            min_time: Minimum reading time (overrides calculation)
            max_time: Maximum reading time (overrides calculation)
        """
        if min_time is None:
            min_time = HumanBehavior.MIN_READ_TIME
        if max_time is None:
            max_time = HumanBehavior.MAX_READ_TIME
        
        # Calculate reading time based on word count
        words = len(text.split())
        base_reading_time = (words / HumanBehavior.READING_SPEED_WPM) * 60
        
        # Add realistic variance
        reading_speed_variance = random.uniform(0.6, 1.4)  # People read at different speeds
        complexity_factor = 1.0
        
        # Adjust for text complexity
        if any(word in text.lower() for word in ['technical', 'complex', 'detailed', 'analysis']):
            complexity_factor = random.uniform(1.2, 1.8)
        
        reading_time = base_reading_time * reading_speed_variance * complexity_factor
        reading_time = max(min_time, min(max_time, reading_time))
        
        # Add occasional pauses (re-reading, thinking)
        pause_count = random.randint(0, 3)
        for _ in range(pause_count):
            pause_time = random.uniform(0.5, 1.5)
            reading_time += pause_time
        
        time.sleep(reading_time)
    
    # Legacy methods for backward compatibility
    @staticmethod
    def random_mouse_movement(page: Page, element_bbox: Optional[dict] = None) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.enhanced_mouse_movement(page, element_bbox)
    
    @staticmethod
    def simulate_typing(page: Page, locator: Locator, text: str, error_rate: float = 0.05) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.simulate_realistic_typing(page, locator, text, error_rate)
    
    @staticmethod
    def human_like_click(page: Page, locator: Locator, move_to_element: bool = True) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.enhanced_click_simulation(page, locator, move_to_element)
    
    @staticmethod
    def simulate_hesitation(min_delay: float = 0.3, max_delay: float = 1.5) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.simulate_enhanced_hesitation(min_delay, max_delay)
    
    @staticmethod
    def simulate_viewport_movement(page: Page) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.simulate_natural_viewport_interaction(page)
    
    @staticmethod
    def simulate_reading(text: str, min_time: Optional[float] = None, max_time: Optional[float] = None) -> None:
        """Legacy method - redirects to enhanced version."""
        HumanBehavior.simulate_realistic_reading(text, min_time, max_time)
    
    @staticmethod
    def natural_delay(base_time: float, variance: float = 0.3) -> None:
        """
        Add natural delay with variance.
        
        Args:
            base_time: Base delay time
            variance: Variance multiplier (0.3 = ±30%)
        """
        delay = base_time * random.uniform(1 - variance, 1 + variance)
        time.sleep(delay)
    
    @staticmethod
    def simulate_form_review(locator: Locator, content: str) -> None:
        """
        Simulate reviewing form content before submission.
        
        Args:
            locator: Locator for form/container
            content: Content being reviewed
        """
        # Scroll to see the content
        locator.scroll_into_view_if_needed()
        time.sleep(random.uniform(0.3, 0.7))
        
        # Simulate reading review
        HumanBehavior.simulate_realistic_reading(content, min_time=0.5, max_time=2.0)
        
        # Occasional viewport adjustment
        if random.random() < 0.3:
            # Small scroll to "check something"
            try:
                page = locator.page
                scroll_amount = random.randint(-100, 100)
                page.mouse.wheel(0, scroll_amount)
                time.sleep(random.uniform(0.2, 0.5))
            except Exception:
                pass  # Skip if page access fails

