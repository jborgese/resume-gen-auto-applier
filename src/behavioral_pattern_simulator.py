# src/behavioral_pattern_simulator.py

import time
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from playwright.sync_api import Page, Locator
from src.logging_config import get_logger

logger = get_logger(__name__)


class BehavioralPatternSimulator:
    """
    Generates and maintains consistent user behavioral patterns based on personality traits.
    This class simulates realistic human behavior to avoid automation detection.
    """
    
    def __init__(self, personality: Dict[str, Any]):
        """
        Initialize the behavioral pattern simulator.
        
        Args:
            personality: User personality traits from StealthSessionManager
        """
        self.personality = personality
        self.session_fatigue = 0
        self.interaction_history = []
        self.last_interaction_time = time.time()
        
        # Behavioral state tracking
        self.current_focus_level = 1.0
        self.distraction_events = 0
        self.error_count = 0
        self.success_count = 0
        
        logger.debug("BehavioralPatternSimulator initialized", 
                    personality_keys=list(personality.keys()))
    
    def simulate_realistic_typing(self, page: Page, field: Locator, text: str) -> None:
        """
        Type text with personality-based patterns and realistic behavior.
        
        Args:
            page: Playwright page object
            field: Form field to type into
            text: Text to type
        """
        try:
            logger.debug("Starting realistic typing simulation", text_length=len(text))
            
            # Focus field with realistic delay
            field.focus()
            self._simulate_focus_delay()
            
            # Clear existing content with realistic behavior
            field.fill("")
            self._simulate_clearing_delay()
            
            # Type with personality-based patterns
            self._type_with_personality_patterns(field, text)
            
            # Track interaction
            self._track_interaction('typing', len(text))
            
            logger.debug("Completed realistic typing simulation")
            
        except Exception as e:
            logger.error("Failed to simulate realistic typing", error=str(e))
            raise
    
    def _simulate_focus_delay(self) -> None:
        """Simulate realistic delay when focusing on a field."""
        base_delay = self.personality['preferred_click_delay']
        
        # Adjust for interaction style
        if self.personality['interaction_style'] == 'careful':
            delay_multiplier = random.uniform(1.2, 1.8)
        elif self.personality['interaction_style'] == 'quick':
            delay_multiplier = random.uniform(0.6, 1.0)
        else:  # methodical
            delay_multiplier = random.uniform(1.0, 1.4)
        
        # Adjust for fatigue
        fatigue_factor = 1 + (self.session_fatigue * 0.1)
        
        final_delay = base_delay * delay_multiplier * fatigue_factor
        time.sleep(final_delay)
    
    def _simulate_clearing_delay(self) -> None:
        """Simulate realistic delay when clearing field content."""
        delay = random.uniform(0.3, 0.7)
        
        # Adjust for interaction style
        if self.personality['interaction_style'] == 'careful':
            delay *= random.uniform(1.1, 1.5)
        
        time.sleep(delay)
    
    def _type_with_personality_patterns(self, field: Locator, text: str) -> None:
        """
        Type text with sophisticated personality-based patterns.
        
        Args:
            field: Form field to type into
            text: Text to type
        """
        words = text.split()
        
        for word_idx, word in enumerate(words):
            # Pause between words
            if word_idx > 0:
                word_pause = self._calculate_word_pause(word, words[word_idx - 1])
                time.sleep(word_pause)
            
            # Type word character by character
            self._type_word_with_patterns(field, word, word_idx)
            
            # Simulate occasional typo correction
            if random.random() < self.personality['error_rate']:
                self._simulate_typo_correction(field, word)
    
    def _calculate_word_pause(self, current_word: str, previous_word: str) -> float:
        """Calculate realistic pause between words."""
        base_pause = random.uniform(0.15, 0.4)
        
        # Longer pause for longer words
        base_pause += len(current_word) * 0.01
        
        # Adjust for typing speed
        typing_speed_factor = 60 / self.personality['typing_speed_wpm']
        base_pause *= typing_speed_factor
        
        # Adjust for interaction style
        if self.personality['interaction_style'] == 'careful':
            base_pause *= random.uniform(1.1, 1.3)
        elif self.personality['interaction_style'] == 'quick':
            base_pause *= random.uniform(0.7, 0.9)
        
        # Adjust for fatigue
        fatigue_factor = 1 + (self.session_fatigue * 0.05)
        base_pause *= fatigue_factor
        
        return base_pause
    
    def _type_word_with_patterns(self, field: Locator, word: str, word_index: int) -> None:
        """
        Type a single word with realistic character-by-character patterns.
        
        Args:
            field: Form field to type into
            word: Word to type
            word_index: Index of word in the text
        """
        for char_idx, char in enumerate(word):
            # Calculate character-specific delay
            char_delay = self._calculate_character_delay(char, char_idx, word)
            
            # Add occasional longer pauses (thinking, re-reading)
            if random.random() < 0.08:  # 8% chance
                char_delay += random.uniform(0.4, 1.2)
            
            # Type the character
            field.type(char, delay=char_delay)
            
            # Simulate occasional hesitation
            if random.random() < self.personality['hesitation_level']:
                time.sleep(random.uniform(0.1, 0.3))
    
    def _calculate_character_delay(self, char: str, char_index: int, word: str) -> float:
        """Calculate realistic delay for typing a character."""
        # Base delay varies by character type
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
        
        # Adjust for typing speed
        typing_speed_factor = 60 / self.personality['typing_speed_wpm']
        base_delay *= typing_speed_factor
        
        # Faster typing for common patterns
        if char_index > 0:
            bigram = word[char_index-1:char_index+1]
            if bigram in ['th', 'he', 'in', 'er', 'an', 're', 'ed', 'nd', 'on', 'en']:
                base_delay *= 0.7
        
        # Adjust for interaction style
        if self.personality['interaction_style'] == 'careful':
            base_delay *= random.uniform(1.05, 1.15)
        elif self.personality['interaction_style'] == 'quick':
            base_delay *= random.uniform(0.85, 0.95)
        
        # Adjust for fatigue
        fatigue_factor = 1 + (self.session_fatigue * 0.02)
        base_delay *= fatigue_factor
        
        return base_delay
    
    def _simulate_typo_correction(self, field: Locator, word: str) -> None:
        """
        Simulate realistic typo correction based on personality.
        
        Args:
            field: Form field
            word: Word that had a typo
        """
        try:
            # Pause as if noticing the error
            error_notice_delay = random.uniform(0.3, 0.8)
            
            # Adjust for interaction style
            if self.personality['interaction_style'] == 'careful':
                error_notice_delay *= random.uniform(1.1, 1.3)
            
            time.sleep(error_notice_delay)
            
            # Determine correction style based on personality
            correction_style = self.personality['error_correction_style']
            
            if correction_style == 'immediate':
                self._immediate_correction(field, word)
            elif correction_style == 'batch':
                self._batch_correction(field, word)
            else:  # ignore
                # Sometimes ignore the error (human behavior)
                if random.random() < 0.3:
                    return
                self._immediate_correction(field, word)
            
            self.error_count += 1
            
        except Exception as e:
            logger.debug("Could not simulate typo correction", error=str(e))
    
    def _immediate_correction(self, field: Locator, word: str) -> None:
        """Simulate immediate error correction."""
        # Backspace with variable speed
        backspace_count = random.randint(1, min(3, len(word)))
        for _ in range(backspace_count):
            field.press("Backspace")
            time.sleep(random.uniform(0.1, 0.25))
        
        # Retype with slightly faster speed
        retype_text = word[-backspace_count:]
        for char in retype_text:
            field.type(char, delay=random.uniform(0.05, 0.12))
    
    def _batch_correction(self, field: Locator, word: str) -> None:
        """Simulate batch error correction (correct multiple errors at once)."""
        # Clear the entire word
        for _ in range(len(word)):
            field.press("Backspace")
            time.sleep(random.uniform(0.08, 0.15))
        
        # Retype the entire word
        for char in word:
            field.type(char, delay=random.uniform(0.06, 0.12))
    
    def simulate_realistic_scrolling(self, page: Page, target_element: Optional[Locator] = None) -> None:
        """
        Scroll with realistic patterns and micro-movements.
        
        Args:
            page: Playwright page object
            target_element: Optional element to scroll to
        """
        try:
            logger.debug("Starting realistic scrolling simulation")
            
            # Determine scroll pattern based on personality
            scroll_pattern = self._determine_scroll_pattern()
            
            if scroll_pattern == 'smooth':
                self._smooth_scroll(page, target_element)
            elif scroll_pattern == 'jerky':
                self._jerky_scroll(page, target_element)
            else:  # mixed
                self._mixed_scroll(page, target_element)
            
            # Track interaction
            self._track_interaction('scrolling', 1)
            
            logger.debug("Completed realistic scrolling simulation")
            
        except Exception as e:
            logger.error("Failed to simulate realistic scrolling", error=str(e))
            raise
    
    def _determine_scroll_pattern(self) -> str:
        """Determine scroll pattern based on personality."""
        if self.personality['interaction_style'] == 'careful':
            return random.choice(['smooth', 'mixed'])
        elif self.personality['interaction_style'] == 'quick':
            return random.choice(['jerky', 'mixed'])
        else:  # methodical
            return 'smooth'
    
    def _smooth_scroll(self, page: Page, target_element: Optional[Locator]) -> None:
        """Simulate smooth scrolling behavior."""
        scroll_amount = self.personality['preferred_scroll_speed']
        
        # Add jitter
        jitter = random.randint(-50, 50)
        scroll_amount += jitter
        
        # Smooth scroll with micro-movements
        steps = random.randint(3, 8)
        for i in range(steps):
            step_amount = scroll_amount / steps
            page.mouse.wheel(0, step_amount)
            
            # Micro-pause between steps
            time.sleep(random.uniform(0.05, 0.15))
            
            # Occasional micro-movement
            if random.random() < 0.3:
                self._micro_mouse_movement(page)
    
    def _jerky_scroll(self, page: Page, target_element: Optional[Locator]) -> None:
        """Simulate jerky scrolling behavior."""
        scroll_amount = self.personality['preferred_scroll_speed']
        
        # More variable scroll amounts
        scroll_amount *= random.uniform(0.5, 1.5)
        
        # Jerky scroll with irregular timing
        steps = random.randint(2, 5)
        for i in range(steps):
            step_amount = scroll_amount / steps
            page.mouse.wheel(0, step_amount)
            
            # Irregular timing
            time.sleep(random.uniform(0.1, 0.4))
    
    def _mixed_scroll(self, page: Page, target_element: Optional[Locator]) -> None:
        """Simulate mixed scrolling behavior."""
        # Combine smooth and jerky patterns
        if random.random() < 0.6:
            self._smooth_scroll(page, target_element)
        else:
            self._jerky_scroll(page, target_element)
    
    def _micro_mouse_movement(self, page: Page) -> None:
        """Simulate realistic micro-mouse movements."""
        try:
            viewport = page.viewport_size
            if viewport:
                # Small random movement
                current_x = random.randint(0, viewport['width'])
                current_y = random.randint(0, viewport['height'])
                
                # Move to nearby position
                target_x = current_x + random.randint(-20, 20)
                target_y = current_y + random.randint(-20, 20)
                
                # Ensure within viewport
                target_x = max(0, min(viewport['width'], target_x))
                target_y = max(0, min(viewport['height'], target_y))
                
                page.mouse.move(target_x, target_y)
                time.sleep(random.uniform(0.05, 0.15))
                
        except Exception as e:
            logger.debug("Could not perform micro-mouse movement", error=str(e))
    
    def simulate_realistic_clicking(self, page: Page, element: Locator) -> None:
        """
        Click with realistic preparation and accuracy patterns.
        
        Args:
            page: Playwright page object
            element: Element to click
        """
        try:
            logger.debug("Starting realistic clicking simulation")
            
            # Scroll element into view if needed
            element.scroll_into_view_if_needed()
            self._simulate_scroll_delay()
            
            # Simulate mouse movement to element
            self._simulate_mouse_approach(page, element)
            
            # Simulate hover behavior
            self._simulate_hover_behavior(element)
            
            # Click with realistic delay
            self._simulate_realistic_click(element)
            
            # Track interaction
            self._track_interaction('clicking', 1)
            
            logger.debug("Completed realistic clicking simulation")
            
        except Exception as e:
            logger.error("Failed to simulate realistic clicking", error=str(e))
            raise
    
    def _simulate_scroll_delay(self) -> None:
        """Simulate delay after scrolling to element."""
        delay = random.uniform(0.3, 0.7)
        
        # Adjust for interaction style
        if self.personality['interaction_style'] == 'careful':
            delay *= random.uniform(1.1, 1.4)
        
        time.sleep(delay)
    
    def _simulate_mouse_approach(self, page: Page, element: Locator) -> None:
        """Simulate realistic mouse movement to element."""
        try:
            # Get element bounding box
            bbox = element.bounding_box()
            if not bbox:
                return
            
            # Calculate target position with slight offset
            target_x = bbox['x'] + bbox['width'] / 2 + random.randint(-8, 8)
            target_y = bbox['y'] + bbox['height'] / 2 + random.randint(-8, 8)
            
            # Get current mouse position (approximate)
            viewport = page.viewport_size
            if viewport:
                current_x = random.randint(0, viewport['width'])
                current_y = random.randint(0, viewport['height'])
                
                # Create realistic approach path
                self._create_realistic_mouse_path(page, current_x, current_y, target_x, target_y)
            
        except Exception as e:
            logger.debug("Could not simulate mouse approach", error=str(e))
    
    def _create_realistic_mouse_path(self, page: Page, start_x: int, start_y: int, 
                                   target_x: int, target_y: int) -> None:
        """Create realistic mouse movement path."""
        try:
            # Calculate distance
            distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
            
            # Determine number of steps based on distance and personality
            if self.personality['interaction_style'] == 'careful':
                steps = max(5, int(distance / 20))
            elif self.personality['interaction_style'] == 'quick':
                steps = max(3, int(distance / 40))
            else:  # methodical
                steps = max(4, int(distance / 25))
            
            # Create path with slight overshoot and correction
            for i in range(steps):
                t = i / steps
                
                # Add slight overshoot and correction
                overshoot_x = random.randint(-15, 15) if i > steps//2 else 0
                overshoot_y = random.randint(-15, 15) if i > steps//2 else 0
                
                x = int(start_x + (target_x - start_x) * t + overshoot_x)
                y = int(start_y + (target_y - start_y) * t + overshoot_y)
                
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.02, 0.08))
                
        except Exception as e:
            logger.debug("Could not create realistic mouse path", error=str(e))
    
    def _simulate_hover_behavior(self, element: Locator) -> None:
        """Simulate realistic hover behavior."""
        try:
            # Hover over element
            element.hover()
            
            # Hover pause (humans don't click instantly)
            hover_delay = random.uniform(0.2, 0.6)
            
            # Adjust for interaction style
            if self.personality['interaction_style'] == 'careful':
                hover_delay *= random.uniform(1.2, 1.6)
            elif self.personality['interaction_style'] == 'quick':
                hover_delay *= random.uniform(0.6, 0.9)
            
            time.sleep(hover_delay)
            
        except Exception as e:
            logger.debug("Could not simulate hover behavior", error=str(e))
    
    def _simulate_realistic_click(self, element: Locator) -> None:
        """Simulate realistic click with personality-based timing."""
        try:
            # Calculate click delay based on personality
            click_delay = random.randint(80, 200)
            
            # Adjust for interaction style
            if self.personality['interaction_style'] == 'careful':
                click_delay = random.randint(100, 250)
            elif self.personality['interaction_style'] == 'quick':
                click_delay = random.randint(50, 150)
            
            # Click with realistic delay
            element.click(delay=click_delay)
            
            # Post-click pause (humans often pause after clicking)
            post_click_delay = random.uniform(0.1, 0.4)
            time.sleep(post_click_delay)
            
        except Exception as e:
            logger.debug("Could not simulate realistic click", error=str(e))
    
    def simulate_distraction_events(self, page: Page) -> None:
        """
        Occasionally simulate realistic distractions.
        
        Args:
            page: Playwright page object
        """
        try:
            # Check if distraction should occur based on personality
            distraction_probability = self.personality['distraction_level']
            
            if random.random() < distraction_probability:
                distraction_type = random.choice(['mouse_movement', 'scroll', 'pause', 'tab_switch'])
                
                if distraction_type == 'mouse_movement':
                    self._simulate_distraction_mouse_movement(page)
                elif distraction_type == 'scroll':
                    self._simulate_distraction_scroll(page)
                elif distraction_type == 'pause':
                    self._simulate_distraction_pause()
                elif distraction_type == 'tab_switch':
                    self._simulate_distraction_tab_switch(page)
                
                self.distraction_events += 1
                logger.debug("Simulated distraction event", type=distraction_type)
                
        except Exception as e:
            logger.debug("Could not simulate distraction event", error=str(e))
    
    def _simulate_distraction_mouse_movement(self, page: Page) -> None:
        """Simulate distraction through mouse movement."""
        try:
            viewport = page.viewport_size
            if viewport:
                # Move mouse to random position
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.5, 2.0))
                
        except Exception as e:
            logger.debug("Could not simulate distraction mouse movement", error=str(e))
    
    def _simulate_distraction_scroll(self, page: Page) -> None:
        """Simulate distraction through scrolling."""
        try:
            # Small random scroll
            scroll_amount = random.randint(-200, 200)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            logger.debug("Could not simulate distraction scroll", error=str(e))
    
    def _simulate_distraction_pause(self) -> None:
        """Simulate distraction through pause."""
        pause_duration = random.uniform(2.0, 8.0)
        time.sleep(pause_duration)
    
    def _simulate_distraction_tab_switch(self, page: Page) -> None:
        """Simulate distraction through tab switching."""
        try:
            # Simulate Ctrl+Tab (tab switching)
            page.keyboard.press('Control+Tab')
            time.sleep(random.uniform(1.0, 3.0))
            
            # Switch back
            page.keyboard.press('Control+Shift+Tab')
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.debug("Could not simulate distraction tab switch", error=str(e))
    
    def simulate_hesitation_patterns(self, page: Page, context: str) -> None:
        """
        Simulate realistic hesitation based on context.
        
        Args:
            page: Playwright page object
            context: Context of the hesitation (e.g., 'form_field', 'button_click')
        """
        try:
            # Calculate hesitation duration based on context and personality
            base_hesitation = self.personality['hesitation_level']
            
            # Adjust for context
            context_multipliers = {
                'form_field': 1.2,
                'button_click': 1.0,
                'navigation': 0.8,
                'confirmation': 1.5,
                'error_recovery': 2.0
            }
            
            multiplier = context_multipliers.get(context, 1.0)
            hesitation_duration = base_hesitation * multiplier * random.uniform(0.5, 2.0)
            
            # Adjust for interaction style
            if self.personality['interaction_style'] == 'careful':
                hesitation_duration *= random.uniform(1.2, 1.8)
            elif self.personality['interaction_style'] == 'quick':
                hesitation_duration *= random.uniform(0.6, 1.0)
            
            # Adjust for fatigue
            fatigue_factor = 1 + (self.session_fatigue * 0.1)
            hesitation_duration *= fatigue_factor
            
            logger.debug("Simulating hesitation", 
                        context=context, 
                        duration=hesitation_duration)
            
            time.sleep(hesitation_duration)
            
        except Exception as e:
            logger.debug("Could not simulate hesitation pattern", error=str(e))
    
    def _track_interaction(self, interaction_type: str, value: Any) -> None:
        """Track interaction for behavioral analysis."""
        self.interaction_history.append({
            'type': interaction_type,
            'value': value,
            'timestamp': time.time(),
            'fatigue_level': self.session_fatigue,
            'focus_level': self.current_focus_level
        })
        
        # Update session fatigue
        self._update_session_fatigue()
        
        # Update focus level
        self._update_focus_level()
    
    def _update_session_fatigue(self) -> None:
        """Update session fatigue based on activity."""
        time_since_last = time.time() - self.last_interaction_time
        self.last_interaction_time = time.time()
        
        # Increase fatigue over time
        fatigue_increase = time_since_last * self.personality['session_fatigue_rate']
        self.session_fatigue += fatigue_increase
        
        # Cap fatigue at reasonable level
        self.session_fatigue = min(self.session_fatigue, 1.0)
    
    def _update_focus_level(self) -> None:
        """Update focus level based on activity and distractions."""
        # Decrease focus over time
        focus_decrease = random.uniform(0.01, 0.05)
        self.current_focus_level -= focus_decrease
        
        # Increase focus after successful interactions
        if self.success_count > 0:
            focus_increase = min(0.1, self.success_count * 0.02)
            self.current_focus_level += focus_increase
        
        # Cap focus level
        self.current_focus_level = max(0.1, min(1.0, self.current_focus_level))
    
    def get_behavioral_stats(self) -> Dict[str, Any]:
        """Get current behavioral statistics."""
        return {
            'session_fatigue': self.session_fatigue,
            'current_focus_level': self.current_focus_level,
            'interaction_count': len(self.interaction_history),
            'distraction_events': self.distraction_events,
            'error_count': self.error_count,
            'success_count': self.success_count,
            'error_rate': self.error_count / max(1, self.error_count + self.success_count),
            'last_interaction_time': self.last_interaction_time
        }
    
    def reset_session_stats(self) -> None:
        """Reset session statistics for new session."""
        self.session_fatigue = 0
        self.interaction_history = []
        self.last_interaction_time = time.time()
        self.current_focus_level = 1.0
        self.distraction_events = 0
        self.error_count = 0
        self.success_count = 0
        
        logger.debug("Reset behavioral session statistics")
