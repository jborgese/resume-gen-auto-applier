"""
Unit tests for error handling functionality.

Tests the error_handler.py module for retry logic, error context,
selector fallbacks, and API failure handling.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeout

# Import the module under test
from src.error_handler import (
    retry_with_backoff, ErrorContext, SelectorFallback, 
    APIFailureHandler, LinkedInUIChangeHandler, safe_execute,
    handle_playwright_errors, AutomationError, LinkedInUIError,
    NetworkError, RetryableError, FatalError
)


class TestRetryWithBackoff:
    """Test retry with backoff functionality."""
    
    def test_retry_with_backoff_success_first_attempt(self):
        """Test retry decorator with success on first attempt."""
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_retry_with_backoff_success_after_retry(self):
        """Test retry decorator with success after retry."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("Temporary failure")
            return "success"
        
        with patch('src.error_handler.time.sleep') as mock_sleep:
            result = test_function()
            assert result == "success"
            assert call_count == 2
            mock_sleep.assert_called_once()
    
    def test_retry_with_backoff_max_attempts_exceeded(self):
        """Test retry decorator when max attempts are exceeded."""
        @retry_with_backoff(max_attempts=2, base_delay=0.1)
        def test_function():
            raise RetryableError("Persistent failure")
        
        with patch('src.error_handler.time.sleep') as mock_sleep:
            with pytest.raises(RetryableError, match="Persistent failure"):
                test_function()
            assert mock_sleep.call_count == 1  # Should sleep once before final failure
    
    def test_retry_with_backoff_fatal_error(self):
        """Test retry decorator with fatal error."""
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def test_function():
            raise FatalError("Fatal error")
        
        with pytest.raises(FatalError, match="Fatal error"):
            test_function()
    
    def test_retry_with_backoff_exponential_backoff(self):
        """Test exponential backoff calculation."""
        @retry_with_backoff(max_attempts=4, base_delay=1.0, exponential_base=2.0)
        def test_function():
            raise RetryableError("Temporary failure")
        
        with patch('src.error_handler.time.sleep') as mock_sleep:
            with pytest.raises(RetryableError):
                test_function()
            
            # Should have slept 3 times with increasing delays
            assert mock_sleep.call_count == 3
            calls = mock_sleep.call_args_list
            
            # Delays should increase exponentially (with jitter)
            # Allow for jitter to make delays smaller, but they should generally increase
            assert calls[0][0][0] >= 0.5  # First delay (allowing for jitter)
            assert calls[1][0][0] >= 1.0  # Second delay (allowing for jitter)
            assert calls[2][0][0] >= 2.0  # Third delay (allowing for jitter)
            
            # Verify delays are generally increasing (with some tolerance for jitter)
            assert calls[1][0][0] > calls[0][0][0] * 0.8  # Second > first (with tolerance)
            assert calls[2][0][0] > calls[1][0][0] * 0.8  # Third > second (with tolerance)
    
    def test_retry_with_backoff_jitter(self):
        """Test that jitter is applied to delays."""
        @retry_with_backoff(max_attempts=3, base_delay=1.0, jitter=True)
        def test_function():
            raise RetryableError("Temporary failure")
        
        with patch('src.error_handler.time.sleep') as mock_sleep, \
             patch('src.error_handler.random.random', return_value=0.5):  # Fixed jitter
            with pytest.raises(RetryableError):
                test_function()
            
            # Should have slept with jitter applied
            assert mock_sleep.call_count == 2
            calls = mock_sleep.call_args_list
            
            # With jitter=0.5, delay should be base_delay * 0.75
            assert calls[0][0][0] == 0.75  # 1.0 * 0.75
            assert calls[1][0][0] == 1.5  # 2.0 * 0.75


class TestErrorContext:
    """Test error context functionality."""
    
    def test_error_context_success(self):
        """Test error context with successful operation."""
        with ErrorContext("test operation") as context:
            context.add_context("key1", "value1")
            context.add_context("key2", "value2")
            # Operation succeeds
        
        # Context should complete successfully
        assert context.operation == "test operation"
        assert context.context["key1"] == "value1"
        assert context.context["key2"] == "value2"
    
    def test_error_context_failure(self):
        """Test error context with failed operation."""
        with pytest.raises(ValueError):
            with ErrorContext("test operation") as context:
                context.add_context("key1", "value1")
                raise ValueError("Test error")
    
    def test_error_context_with_page(self, mock_playwright_page):
        """Test error context with page object."""
        with pytest.raises(ValueError):
            with ErrorContext("test operation", mock_playwright_page) as context:
                context.add_context("key1", "value1")
                raise ValueError("Test error")
    
    def test_error_context_duration(self):
        """Test error context duration tracking."""
        with ErrorContext("test operation") as context:
            time.sleep(0.1)  # Simulate some work
        
        # Duration should be tracked
        assert context.start_time > 0
        assert time.time() - context.start_time >= 0.1


class TestSelectorFallback:
    """Test selector fallback functionality."""
    
    def test_find_element_with_fallback_success(self, mock_playwright_page):
        """Test finding element with fallback selectors."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock successful element finding
        mock_playwright_page.locator.return_value.count.return_value = 1
        
        result = fallback.find_element_with_fallback(
            ["selector1", "selector2"], 
            "test operation"
        )
        
        assert result is not None
        mock_playwright_page.locator.assert_called_with("selector1")
    
    def test_find_element_with_fallback_all_fail(self, mock_playwright_page):
        """Test finding element when all selectors fail."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock all selectors failing
        mock_playwright_page.locator.return_value.count.return_value = 0
        
        result = fallback.find_element_with_fallback(
            ["selector1", "selector2"], 
            "test operation"
        )
        
        assert result is None
    
    def test_safe_click_success(self, mock_playwright_page):
        """Test safe click functionality."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock successful click
        mock_locator = Mock()
        mock_locator.scroll_into_view_if_needed.return_value = None
        mock_locator.click.return_value = None
        mock_playwright_page.locator.return_value = mock_locator
        mock_playwright_page.locator.return_value.count.return_value = 1
        
        result = fallback.safe_click(["selector1"], "test click")
        
        assert result is True
        mock_locator.scroll_into_view_if_needed.assert_called_once()
        mock_locator.click.assert_called_once()
    
    def test_safe_click_failure(self, mock_playwright_page):
        """Test safe click functionality with failure."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock click failure
        mock_playwright_page.locator.return_value.count.return_value = 0
        
        result = fallback.safe_click(["selector1"], "test click")
        
        assert result is False
    
    def test_safe_fill_success(self, mock_playwright_page):
        """Test safe fill functionality."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock successful fill
        mock_locator = Mock()
        mock_locator.clear.return_value = None
        mock_locator.fill.return_value = None
        mock_playwright_page.locator.return_value = mock_locator
        mock_playwright_page.locator.return_value.count.return_value = 1
        
        result = fallback.safe_fill(["selector1"], "test value", "test fill")
        
        assert result is True
        mock_locator.clear.assert_called_once()
        mock_locator.fill.assert_called_once_with("test value")
    
    def test_safe_fill_failure(self, mock_playwright_page):
        """Test safe fill functionality with failure."""
        fallback = SelectorFallback(mock_playwright_page)
        
        # Mock fill failure
        mock_playwright_page.locator.return_value.count.return_value = 0
        
        result = fallback.safe_fill(["selector1"], "test value", "test fill")
        
        assert result is False


class TestAPIFailureHandler:
    """Test API failure handler functionality."""
    
    def test_handle_openai_failure_success(self):
        """Test OpenAI failure handler with success."""
        def test_function():
            return '{"summary": "test", "keywords": "test"}'
        
        result = APIFailureHandler.handle_openai_failure(test_function)
        
        assert result == '{"summary": "test", "keywords": "test"}'
    
    def test_handle_openai_failure_with_exception(self):
        """Test OpenAI failure handler with exception."""
        def test_function():
            raise Exception("API error")
        
        result = APIFailureHandler.handle_openai_failure(test_function)
        
        # Should return fallback JSON
        assert isinstance(result, str)
        import json
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
    
    def test_handle_weasyprint_failure_success(self):
        """Test WeasyPrint failure handler with success."""
        with patch('weasyprint.HTML') as mock_html:
            mock_instance = Mock()
            mock_instance.write_pdf.return_value = None
            mock_html.return_value = mock_instance
            
            result = APIFailureHandler.handle_weasyprint_failure(
                "<html><body>Test</body></html>",
                "test.pdf"
            )
            
            assert result is True
            mock_instance.write_pdf.assert_called_once_with("test.pdf")
    
    def test_handle_weasyprint_failure_with_exception(self):
        """Test WeasyPrint failure handler with exception."""
        with patch('weasyprint.HTML') as mock_html, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_html.side_effect = Exception("WeasyPrint error")
            
            result = APIFailureHandler.handle_weasyprint_failure(
                "<html><body>Test</body></html>",
                "test.pdf"
            )
            
            # Should fallback to HTML file
            assert result is True
            mock_file.assert_called_with("test.html", 'w', encoding='utf-8')
    
    def test_handle_weasyprint_failure_html_fallback_fails(self):
        """Test WeasyPrint failure handler when HTML fallback also fails."""
        with patch('weasyprint.HTML') as mock_html, \
             patch('builtins.open') as mock_file:
            
            mock_html.side_effect = Exception("WeasyPrint error")
            mock_file.side_effect = Exception("File write error")
            
            result = APIFailureHandler.handle_weasyprint_failure(
                "<html><body>Test</body></html>",
                "test.pdf"
            )
            
            assert result is False


class TestLinkedInUIChangeHandler:
    """Test LinkedIn UI change handler functionality."""
    
    def test_detect_ui_changes_no_changes(self, mock_playwright_page):
        """Test UI change detection with no changes."""
        handler = LinkedInUIChangeHandler(mock_playwright_page)
        
        # Mock all selectors working
        mock_playwright_page.locator.return_value.count.return_value = 1
        
        changes = handler.detect_ui_changes("general")
        
        assert changes["login_page_changed"] is False
        assert changes["job_search_changed"] is False
        assert changes["easy_apply_changed"] is False
        assert changes["selectors_broken"] is False
    
    def test_detect_ui_changes_login_changed(self, mock_playwright_page):
        """Test UI change detection with login changes."""
        handler = LinkedInUIChangeHandler(mock_playwright_page)
        
        # Mock login selectors failing
        def mock_locator(selector):
            # Check for actual login selector patterns including fallbacks
            login_patterns = [
                'input[id="username"]', 'input[id="password"]', 'button[type="submit"]',
                'input[name="session_key"]', 'input[name="session_password"]',
                'input[type="email"]', 'input[type="password"]'
            ]
            if any(pattern in selector for pattern in login_patterns):
                mock = Mock()
                mock.count.return_value = 0
                return mock
            else:
                mock = Mock()
                mock.count.return_value = 1
                return mock
        
        mock_playwright_page.locator.side_effect = mock_locator
        
        changes = handler.detect_ui_changes("login")
        
        assert changes["login_page_changed"] is True
        assert changes["selectors_broken"] is True
    
    def test_detect_ui_changes_job_search_changed(self, mock_playwright_page):
        """Test UI change detection with job search changes."""
        handler = LinkedInUIChangeHandler(mock_playwright_page)
        
        # Mock job search selectors failing
        def mock_locator(selector):
            # Check for actual job search selector patterns including fallbacks
            job_search_patterns = [
                'div.scaffold-layout__list.jobs-semantic-search-list', 'ul.semantic-search-results-list',
                'div[data-test-id="job-search-results"]', 'ul.jobs-search__results-list',
                'div.jobs-search-results', 'main[role="main"] ul li', 'div.scaffold-layout__content ul li'
            ]
            if any(pattern in selector for pattern in job_search_patterns):
                mock = Mock()
                mock.count.return_value = 0
                return mock
            else:
                mock = Mock()
                mock.count.return_value = 1
                return mock
        
        mock_playwright_page.locator.side_effect = mock_locator
        
        changes = handler.detect_ui_changes("job_search")
        
        assert changes["job_search_changed"] is True
        assert changes["selectors_broken"] is True
    
    def test_adapt_to_changes_success(self, mock_playwright_page):
        """Test UI change adaptation with success."""
        handler = LinkedInUIChangeHandler(mock_playwright_page)
        
        # Mock generic selectors working
        mock_playwright_page.locator.return_value.count.return_value = 1
        
        changes = {
            "login_page_changed": True,
            "job_search_changed": False,
            "easy_apply_changed": False,
            "selectors_broken": True
        }
        
        result = handler.adapt_to_changes(changes)
        
        assert result is True
    
    def test_adapt_to_changes_failure(self, mock_playwright_page):
        """Test UI change adaptation with failure."""
        handler = LinkedInUIChangeHandler(mock_playwright_page)
        
        # Mock all selectors failing
        mock_playwright_page.locator.return_value.count.return_value = 0
        
        changes = {
            "login_page_changed": True,
            "job_search_changed": True,
            "easy_apply_changed": True,
            "selectors_broken": True
        }
        
        result = handler.adapt_to_changes(changes)
        
        # Should still return True (graceful degradation)
        assert result is True


class TestSafeExecute:
    """Test safe execute functionality."""
    
    def test_safe_execute_success(self):
        """Test safe execute with successful function."""
        def test_function():
            return "success"
        
        result = safe_execute("test operation", test_function)
        
        assert result == "success"
    
    def test_safe_execute_failure(self):
        """Test safe execute with failed function."""
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            safe_execute("test operation", test_function)


class TestHandlePlaywrightErrors:
    """Test Playwright error handling."""
    
    def test_handle_playwright_errors_timeout(self):
        """Test handling of Playwright timeout errors."""
        @handle_playwright_errors
        def test_function():
            raise PlaywrightTimeout("Timeout error")
        
        with pytest.raises(RetryableError, match="Timeout in test_function"):
            test_function()
    
    def test_handle_playwright_errors_target_closed(self):
        """Test handling of target closed errors."""
        @handle_playwright_errors
        def test_function():
            raise Exception("Target closed")
        
        with pytest.raises(Exception, match="Target closed"):
            test_function()
    
    def test_handle_playwright_errors_success(self):
        """Test handling of successful function."""
        @handle_playwright_errors
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_automation_error(self):
        """Test AutomationError exception."""
        error = AutomationError("Test automation error")
        assert str(error) == "Test automation error"
        assert isinstance(error, Exception)
    
    def test_linkedin_ui_error(self):
        """Test LinkedInUIError exception."""
        error = LinkedInUIError("Test UI error")
        assert str(error) == "Test UI error"
        assert isinstance(error, AutomationError)
    
    def test_network_error(self):
        """Test NetworkError exception."""
        error = NetworkError("Test network error")
        assert str(error) == "Test network error"
        assert isinstance(error, AutomationError)
    
    def test_retryable_error(self):
        """Test RetryableError exception."""
        error = RetryableError("Test retryable error")
        assert str(error) == "Test retryable error"
        assert isinstance(error, AutomationError)
    
    def test_fatal_error(self):
        """Test FatalError exception."""
        error = FatalError("Test fatal error")
        assert str(error) == "Test fatal error"
        assert isinstance(error, AutomationError)


@pytest.mark.unit
class TestErrorHandlerIntegration:
    """Integration tests for error handler."""
    
    def test_error_handler_import_success(self):
        """Test that error handler module imports successfully."""
        import src.error_handler as error_handler
        assert error_handler is not None
        assert hasattr(error_handler, 'retry_with_backoff')
        assert hasattr(error_handler, 'ErrorContext')
        assert hasattr(error_handler, 'SelectorFallback')
        assert hasattr(error_handler, 'APIFailureHandler')
    
    def test_error_handler_exception_hierarchy(self):
        """Test exception hierarchy."""
        # Test inheritance
        assert issubclass(LinkedInUIError, AutomationError)
        assert issubclass(NetworkError, AutomationError)
        assert issubclass(RetryableError, AutomationError)
        assert issubclass(FatalError, AutomationError)
        
        # Test that all are exceptions
        assert issubclass(AutomationError, Exception)
        assert issubclass(LinkedInUIError, Exception)
        assert issubclass(NetworkError, Exception)
        assert issubclass(RetryableError, Exception)
        assert issubclass(FatalError, Exception)
