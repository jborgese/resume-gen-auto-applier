# src/human_behavior.py
"""
Human behavior simulation for LinkedIn automation.
Mimics natural human interactions to avoid bot detection.
"""

import time
import random
import math
from typing import Optional, Tuple
from playwright.sync_api import Page, Locator


class HumanBehavior:
    """Simulates human-like behavior for web automation."""
    
    # Configuration for human-like delays
    READING_SPEED_WPM = 200  # Words per minute for reading
    TYPING_SPEED_WPM = 40   # Words per minute for typing
    MIN_READ_TIME = 0.5      # Minimum time to read (seconds)
    MAX_READ_TIME = 3.0      # Maximum time to read (seconds)
    
    @staticmethod
    def random_mouse_movement(page: Page, element_bbox: Optional[dict] = None) -> None:
        """
        Perform random mouse movements before interacting with elements.
        Simulates human checking/interacting with the page.
        
        Args:
            page: Playwright page object
            element_bbox: Optional bounding box of target element
        """
        if random.random() < 0.3:  # 30% chance to do random movement
            viewport = page.viewport_size
            if viewport:
                # Small random movement within viewport
                x = random.randint(50, viewport['width'] - 50)
                y = random.randint(50, viewport['height'] - 50)
                page.mouse.move(x, y, steps=random.randint(5, 15))
                time.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    def simulate_reading(text: str, min_time: Optional[float] = None, max_time: Optional[float] = None) -> None:
        """
        Simulate reading time based on text length.
        
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
        reading_time = (words / HumanBehavior.READING_SPEED_WPM) * 60
        
        # Add randomness
        reading_time = reading_time * random.uniform(0.7, 1.3)
        reading_time = max(min_time, min(max_time, reading_time))
        
        time.sleep(reading_time)
    
    @staticmethod
    def simulate_typing(page: Page, locator: Locator, text: str, error_rate: float = 0.05) -> None:
        """
        Simulate human-like typing with variable speeds and occasional errors.
        
        Args:
            page: Playwright page object
            locator: Locator for the input field
            text: Text to type
            error_rate: Probability of making a typo (default: 5%)
        """
        # Focus the input first
        locator.focus()
        time.sleep(random.uniform(0.1, 0.3))
        
        # Clear existing content with human-like delay
        locator.fill("")
        time.sleep(random.uniform(0.2, 0.5))
        
        # Type character by character with variable delays
        words = text.split()
        for word_idx, word in enumerate(words):
            # Small pause between words
            if word_idx > 0:
                time.sleep(random.uniform(0.1, 0.3))
            
            # Type word character by character
            for char in word:
                # Variable typing speed (faster for common patterns)
                if char in 'aeiou':
                    delay = random.uniform(0.05, 0.15)
                else:
                    delay = random.uniform(0.08, 0.2)
                
                # Occasional longer pause (thinking, re-reading)
                if random.random() < 0.1:  # 10% chance
                    delay += random.uniform(0.3, 0.8)
                
                locator.type(char, delay=delay)
            
            # Simulate occasional typo correction
            if random.random() < error_rate:
                # Backspace a few characters
                for _ in range(random.randint(1, 3)):
                    locator.press("Backspace")
                    time.sleep(random.uniform(0.1, 0.2))
                # Retype
                locator.type(word[-3:], delay=random.uniform(0.05, 0.15))
        
        # Final pause before moving on
        time.sleep(random.uniform(0.2, 0.5))
    
    @staticmethod
    def human_like_click(page: Page, locator: Locator, move_to_element: bool = True) -> None:
        """
        Perform human-like click with mouse movement and delays.
        
        Args:
            page: Playwright page object
            locator: Locator for element to click
            move_to_element: Whether to move mouse to element before clicking
        """
        if move_to_element:
            # Scroll element into view (if needed)
            locator.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.2, 0.5))
            
            # Hover before clicking (humans don't click instantly)
            try:
                bbox = locator.bounding_box()
                if bbox:
                    # Move mouse to element with slight randomness
                    x = bbox['x'] + bbox['width'] / 2 + random.randint(-5, 5)
                    y = bbox['y'] + bbox['height'] / 2 + random.randint(-5, 5)
                    page.mouse.move(x, y, steps=random.randint(3, 8))
                    time.sleep(random.uniform(0.15, 0.4))  # Pause before clicking
            except Exception:
                # Fallback to simple hover
                locator.hover()
                time.sleep(random.uniform(0.15, 0.4))
        
        # Click with slight delay
        locator.click(delay=random.randint(50, 150))
    
    @staticmethod
    def simulate_hesitation(min_delay: float = 0.3, max_delay: float = 1.5) -> None:
        """
        Simulate human hesitation or thinking time.
        
        Args:
            min_delay: Minimum hesitation time
            max_delay: Maximum hesitation time
        """
        # Occasionally add longer hesitation (checking details, re-reading)
        if random.random() < 0.2:  # 20% chance for longer pause
            delay = random.uniform(max_delay, max_delay * 2)
        else:
            delay = random.uniform(min_delay, max_delay)
        
        time.sleep(delay)
    
    @staticmethod
    def simulate_viewport_movement(page: Page) -> None:
        """
        Simulate user moving viewport (scrolling, looking around).
        
        Args:
            page: Playwright page object
        """
        if random.random() < 0.25:  # 25% chance
            # Small random scroll
            scroll_amount = random.randint(-200, 200)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.3, 0.8))
    
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
        HumanBehavior.simulate_reading(content, min_time=0.5, max_time=2.0)
        
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

