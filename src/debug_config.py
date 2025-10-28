# src/debug_config.py

"""
Debug mode configuration to optimize performance and reduce slowdowns.
This module provides settings specifically for debug mode to improve
asset rendering and reduce GraphQL-related issues.
"""

import os
from typing import Dict, Any, Optional
from src.logging_config import get_logger

logger = get_logger(__name__)

class DebugConfig:
    """
    Configuration for debug mode optimizations.
    Provides settings to reduce slowdowns and improve asset rendering.
    """
    
    def __init__(self):
        self.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        self.enable_graphql_debugging = os.getenv('ENABLE_GRAPHQL_DEBUG', 'false').lower() == 'true'
        self.reduce_debug_pauses = os.getenv('REDUCE_DEBUG_PAUSES', 'false').lower() == 'true'
        
    def get_debug_browser_args(self) -> list:
        """
        Get browser arguments optimized for debug mode.
        Reduces resource blocking that can cause GraphQL issues.
        """
        if not self.debug_mode:
            return []
            
        debug_args = [
            # Reduce aggressive resource blocking in debug mode
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            
            # Allow more resources for debugging
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            
            # Enable better debugging
            '--enable-logging',
            '--log-level=0',
            '--v=1',
            
            # Reduce memory pressure
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            
            # Allow debugging tools
            '--remote-debugging-port=9222',
            '--disable-dev-shm-usage',
        ]
        
        logger.info(f"Debug mode: Using {len(debug_args)} debug-optimized browser arguments")
        return debug_args
    
    def get_debug_timeouts(self) -> Dict[str, float]:
        """
        Get timeout settings optimized for debug mode.
        Longer timeouts to handle GraphQL loading issues.
        """
        if not self.debug_mode:
            return {}
            
        return {
            'page_load': 30.0,  # Increased from default
            'element_wait': 15.0,  # Increased for GraphQL hydration
            'network_idle': 10.0,  # Allow more time for GraphQL requests
            'easy_apply_click': 20.0,  # Longer timeout for debug mode
        }
    
    def get_debug_delays(self) -> Dict[str, float]:
        """
        Get delay settings optimized for debug mode.
        Reduced delays when REDUCE_DEBUG_PAUSES is enabled.
        """
        base_delays = {
            'ui_stability': 1.0,
            'human_behavior': 0.5,
            'page_transition': 2.0,
            'graphql_wait': 3.0,  # Extra time for GraphQL hydration
        }
        
        if self.reduce_debug_pauses:
            # Reduce delays by 50% when REDUCE_DEBUG_PAUSES is enabled
            return {k: v * 0.5 for k, v in base_delays.items()}
        
        return base_delays
    
    def should_skip_debug_stops(self) -> bool:
        """
        Determine if debug stops should be skipped.
        Useful for reducing interruptions during debugging.
        """
        return self.reduce_debug_pauses or os.getenv('SKIP_DEBUG_STOPS', 'false').lower() == 'true'
    
    def get_graphql_error_handling(self) -> Dict[str, Any]:
        """
        Get GraphQL error handling configuration for debug mode.
        """
        return {
            'max_retries': 3,
            'retry_delay': 2.0,
            'ignore_common_errors': True,
            'log_graphql_errors': self.enable_graphql_debugging,
            'fallback_to_static_content': True,
        }
    
    def get_debug_route_handling(self) -> Dict[str, Any]:
        """
        Get route handling configuration for debug mode.
        Less aggressive blocking to prevent GraphQL issues.
        """
        return {
            'block_extensions': True,
            'block_trackers': False,  # Don't block trackers in debug mode
            'block_images': False,   # Don't block images in debug mode
            'allow_all_linkedin': True,  # Allow all LinkedIn resources
            'log_blocked_requests': self.enable_graphql_debugging,
        }

# Global debug config instance
debug_config = DebugConfig()

def get_debug_config() -> DebugConfig:
    """Get the global debug configuration instance."""
    return debug_config

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return debug_config.debug_mode

def should_reduce_debug_pauses() -> bool:
    """Check if debug pauses should be reduced."""
    return debug_config.reduce_debug_pauses

def get_debug_browser_args() -> list:
    """Get debug-optimized browser arguments."""
    return debug_config.get_debug_browser_args()

def get_debug_timeouts() -> Dict[str, float]:
    """Get debug-optimized timeout settings."""
    return debug_config.get_debug_timeouts()

def get_debug_delays() -> Dict[str, float]:
    """Get debug-optimized delay settings."""
    return debug_config.get_debug_delays()

def should_skip_debug_stops() -> bool:
    """Check if debug stops should be skipped."""
    return debug_config.should_skip_debug_stops()

def get_graphql_error_handling() -> Dict[str, Any]:
    """Get GraphQL error handling configuration."""
    return debug_config.get_graphql_error_handling()

def get_debug_route_handling() -> Dict[str, Any]:
    """Get debug route handling configuration."""
    return debug_config.get_debug_route_handling()
