# src/resource_error_handler.py

import logging
import time
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page, Route, Request, Response
import re
import src.config as config

logger = logging.getLogger(__name__)

class ResourceErrorHandler:
    """
    Handles blocked resources and extension-related errors that commonly occur
    during LinkedIn automation, based on the log analysis.
    
    This class provides:
    - Blocked resource detection and handling
    - Extension error suppression
    - Third-party cookie warning handling
    - Network error recovery
    - Resource loading optimization
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.blocked_resources = []
        self.extension_errors = []
        self.cookie_warnings = []
        self.network_errors = []
        self.graphql_errors = []
        
        # Common problematic patterns from the log analysis
        self.blocked_patterns = [
            r'chrome-extension://invalid/',
            r'net::ERR_BLOCKED_BY_CLIENT',
            r'Failed to load resource',
            r'chrome-extension://',
            r'moz-extension://',
            r'safari-extension://',
        ]
        
        # Third-party cookie warning patterns
        self.cookie_warning_patterns = [
            r'Third-party cookie will be blocked',
            r'Privacy Sandbox',
            r'cookie.*blocked',
        ]
        
        # Network error patterns
        self.network_error_patterns = [
            r'ERR_HTTP_RESPONSE_CODE_FAILURE',
            r'ERR_NETWORK_CHANGED',
            r'ERR_INTERNET_DISCONNECTED',
            r'ERR_CONNECTION_RESET',
            r'ERR_CONNECTION_REFUSED',
            r'TypeError: network error',
        ]
        
        # LinkedIn GraphQL error patterns
        self.graphql_error_patterns = [
            r'server responded with an invalid payload',
            r'graphqlinvalidserverresponseerror',
            r'voyager.*\.',
            r'cannot read properties of undefined',
            r'reading \'attributes\'',
        ]
        
        # LinkedIn-specific warning patterns (harmless browser behavior)
        self.linkedin_warning_patterns = [
            r'BooleanExpression with operator "numericGreaterThan" had an expression that evaluated to null',
            r'EventSource\'s response has a Content-Type specifying an unsupported type',
            r'Content contains tags or attributes that are not allowed',
            r'HTML sanitized:',
            r'Attribute \'exception\.tags\' of type \'object\' could not be converted to a proto attribute',
            r'<!--\[if IE \d+\]><span></span><!\[endif\]-->',
            r'TypeError: network error',
        ]
    
    def setup_error_handling(self):
        """
        Set up comprehensive error handling for the page.
        This should be called after creating the page but before navigation.
        """
        try:
            # Set up console message handling
            self.page.on("console", self._handle_console_message)
            
            # Set up page error handling
            self.page.on("pageerror", self._handle_page_error)
            
            # Set up request/response handling
            self.page.route("**/*", self._handle_route)
            
            logger.info("Resource error handling setup completed")
            
        except Exception as e:
            logger.warning(f"Failed to setup error handling: {e}")
    
    def _handle_console_message(self, msg):
        """
        Handle console messages to detect and suppress common errors.
        """
        try:
            message_text = msg.text.lower()
            
            # Check for blocked resource errors
            for pattern in self.blocked_patterns:
                if re.search(pattern, message_text, re.IGNORECASE):
                    self.extension_errors.append({
                        'timestamp': time.time(),
                        'message': msg.text,
                        'type': 'blocked_resource'
                    })
                    logger.debug(f"Suppressed blocked resource error: {msg.text[:100]}...")
                    return  # Don't log these as they're expected
            
            # Check for cookie warnings
            for pattern in self.cookie_warning_patterns:
                if re.search(pattern, message_text, re.IGNORECASE):
                    self.cookie_warnings.append({
                        'timestamp': time.time(),
                        'message': msg.text,
                        'type': 'cookie_warning'
                    })
                    logger.debug(f"Suppressed cookie warning: {msg.text[:100]}...")
                    return  # Don't log these as they're expected
            
            # Check for LinkedIn GraphQL errors
            for pattern in self.graphql_error_patterns:
                if re.search(pattern, message_text, re.IGNORECASE):
                    self.graphql_errors.append({
                        'timestamp': time.time(),
                        'message': msg.text,
                        'type': 'graphql_error'
                    })
                    logger.debug(f"Suppressed LinkedIn GraphQL error: {msg.text[:100]}...")
                    return  # Don't log these as they're expected
            
            # Check for LinkedIn-specific warnings (harmless browser behavior)
            for pattern in self.linkedin_warning_patterns:
                if re.search(pattern, message_text, re.IGNORECASE):
                    if config.SUPPRESS_CONSOLE_WARNINGS:
                        logger.debug(f"Suppressed LinkedIn warning: {msg.text[:100]}...")
                        return  # Don't log these as they're expected LinkedIn frontend behavior
                    else:
                        logger.debug(f"LinkedIn warning (suppression disabled): {msg.text[:100]}...")
                        break  # Continue to normal logging
            
            # Log other console messages normally
            if msg.type == 'error':
                logger.error(f"Console error: {msg.text}")
            elif msg.type == 'warning':
                if config.SUPPRESS_CONSOLE_WARNINGS:
                    logger.debug(f"Console warning (suppressed): {msg.text}")
                else:
                    logger.warning(f"Console warning: {msg.text}")
            else:
                logger.debug(f"Console {msg.type}: {msg.text}")
                
        except Exception as e:
            logger.warning(f"Error handling console message: {e}")
    
    def _handle_page_error(self, error):
        """
        Handle page-level JavaScript errors.
        """
        try:
            # Extract error message from Playwright error object
            # Playwright pageerror events pass Error objects with .message attribute
            if hasattr(error, 'message'):
                error_text = str(error.message).lower()
                error_str = str(error.message)
            elif hasattr(error, 'error'):
                error_text = str(error.error).lower()
                error_str = str(error.error)
            else:
                error_text = str(error).lower()
                error_str = str(error)
            
            # Check if it's a known extension-related error
            for pattern in self.blocked_patterns:
                if re.search(pattern, error_text, re.IGNORECASE):
                    self.extension_errors.append({
                        'timestamp': time.time(),
                        'error': error_str,
                        'type': 'page_error'
                    })
                    logger.debug(f"Suppressed extension-related page error: {error_str[:100]}...")
                    return  # Don't log these as they're expected
            
            # Check for LinkedIn GraphQL errors (common in automation)
            # Check both regex patterns and simple string contains for robustness
            is_graphql_error = False
            for pattern in self.graphql_error_patterns:
                if re.search(pattern, error_text):
                    is_graphql_error = True
                    break
            
            # Also check for common GraphQL error keywords directly
            if not is_graphql_error:
                graphql_keywords = [
                    'server responded with an invalid payload',
                    'graphql',
                    'voyager',
                    'cannot read properties of undefined',
                    'reading \'attributes\'',
                ]
                for keyword in graphql_keywords:
                    if keyword in error_text:
                        is_graphql_error = True
                        break
            
            if is_graphql_error:
                self.graphql_errors.append({
                    'timestamp': time.time(),
                    'error': error_str,
                    'type': 'graphql_error'
                })
                logger.debug(f"Suppressed LinkedIn GraphQL/page error: {error_str[:100]}...")
                return  # Don't log these as they're expected LinkedIn frontend errors
            
            # Check for LinkedIn-specific warnings in page errors
            for pattern in self.linkedin_warning_patterns:
                if re.search(pattern, error_text, re.IGNORECASE):
                    if config.SUPPRESS_CONSOLE_WARNINGS:
                        logger.debug(f"Suppressed LinkedIn page warning: {error_str[:100]}...")
                        return  # Don't log these as they're expected LinkedIn frontend behavior
                    else:
                        logger.debug(f"LinkedIn page warning (suppression disabled): {error_str[:100]}...")
                        break  # Continue to normal logging
            
            # Log other page errors
            logger.error(f"Page error: {error_str}")
            
        except Exception as e:
            logger.warning(f"Error handling page error: {e}")
    
    def _handle_route(self, route: Route, request: Request):
        """
        Handle route requests to block problematic resources.
        """
        try:
            url = request.url.lower()
            
            # Block problematic extensions
            if any(ext in url for ext in [
                'chrome-extension://',
                'moz-extension://',
                'safari-extension://',
                'chrome://',
                'about:',
            ]):
                logger.debug(f"Blocking problematic resource: {request.url}")
                route.abort()
                return
            
            # Block common tracking and analytics
            tracking_domains = [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com/tr',
                'doubleclick.net',
                'googlesyndication.com',
                'amazon-adsystem.com',
                'adsystem.amazon.com',
            ]
            
            if any(domain in url for domain in tracking_domains):
                logger.debug(f"Blocking tracker: {request.url}")
                route.abort()
                return
            
            # Block resource-heavy content types
            if any(content_type in url for content_type in [
                '.mp4', '.avi', '.mov', '.wmv',  # Videos
                '.mp3', '.wav', '.flac',  # Audio
                '.gif', '.png', '.jpg', '.jpeg', '.webp',  # Images (optional)
            ]):
                logger.debug(f"Blocking resource-heavy content: {request.url}")
                route.abort()
                return
            
            # Allow other requests to proceed
            route.continue_()
            
        except Exception as e:
            logger.debug(f"Route handling error: {e}")
            # If route handling fails, continue with the request
            try:
                route.continue_()
            except:
                pass
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors encountered.
        """
        return {
            'blocked_resources': len(self.blocked_resources),
            'extension_errors': len(self.extension_errors),
            'cookie_warnings': len(self.cookie_warnings),
            'network_errors': len(self.network_errors),
            'graphql_errors': len(self.graphql_errors),
            'total_errors': (
                len(self.blocked_resources) + 
                len(self.extension_errors) + 
                len(self.cookie_warnings) + 
                len(self.network_errors) +
                len(self.graphql_errors)
            )
        }
    
    def clear_errors(self):
        """
        Clear all error tracking.
        """
        self.blocked_resources.clear()
        self.extension_errors.clear()
        self.cookie_warnings.clear()
        self.network_errors.clear()
        self.graphql_errors.clear()
    
    def is_healthy(self) -> bool:
        """
        Check if the page is in a healthy state (not too many errors).
        """
        total_errors = (
            len(self.blocked_resources) + 
            len(self.extension_errors) + 
            len(self.cookie_warnings) + 
            len(self.network_errors) +
            len(self.graphql_errors)
        )
        
        # Consider healthy if less than 50 total errors
        return total_errors < 50
    
    def get_recommendations(self) -> List[str]:
        """
        Get recommendations based on the errors encountered.
        """
        recommendations = []
        
        if len(self.extension_errors) > 10:
            recommendations.append("Consider disabling browser extensions")
        
        if len(self.cookie_warnings) > 5:
            recommendations.append("Third-party cookies are being blocked - this is normal")
        
        if len(self.network_errors) > 3:
            recommendations.append("Network issues detected - check internet connection")
        
        if len(self.graphql_errors) > 5:
            recommendations.append("LinkedIn GraphQL errors detected - this is normal for automation")
        
        if not self.is_healthy():
            recommendations.append("High error count detected - consider restarting browser")
        
        return recommendations
