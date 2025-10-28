"""
Unit tests for LLM summary functionality.

Tests the llm_summary.py module for OpenAI API integration,
JSON parsing, error handling, and fallback mechanisms.
"""

import pytest
from unittest.mock import patch, Mock
import json

# Import the module under test
from src.llm_summary import generate_resume_summary, _create_fallback_json
from tests.fixtures.test_data import get_sample_job_data


class TestLLMSummaryGeneration:
    """Test LLM summary generation functionality."""
    
    def test_generate_resume_summary_success(self, sample_job_data, mock_openai_client):
        """Test successful resume summary generation."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should return JSON string
            assert isinstance(result, str)
            
            # Should be valid JSON
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
            assert isinstance(parsed_result["summary"], str)
            assert isinstance(parsed_result["keywords"], str)
    
    def test_generate_resume_summary_missing_api_key(self, sample_job_data):
        """Test resume summary generation with missing API key."""
        with patch('src.llm_summary.OPENAI_API_KEY', None):
            with pytest.raises(Exception, match="OPENAI_API_KEY is missing"):
                generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
    
    def test_generate_resume_summary_missing_parameters(self, mock_openai_client):
        """Test resume summary generation with missing parameters."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            # Missing job_title
            with pytest.raises(ValueError, match="Missing required parameters"):
                generate_resume_summary("", "Company", "Description")
            
            # Missing company
            with pytest.raises(ValueError, match="Missing required parameters"):
                generate_resume_summary("Title", "", "Description")
            
            # Missing description
            with pytest.raises(ValueError, match="Missing required parameters"):
                generate_resume_summary("Title", "Company", "")
    
    def test_generate_resume_summary_long_description(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with long description."""
        # Create a very long description
        long_description = "This is a very long job description. " * 1000
        
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                long_description
            )
            
            # Should still work and return valid JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
    
    def test_generate_resume_summary_empty_response(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with empty API response."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock empty response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = ""
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should create fallback JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
    
    def test_generate_resume_summary_code_fences(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with code fences in response."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock response with code fences
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '```json\n{"summary": "Test summary", "keywords": "Python, React"}\n```'
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should remove code fences and return valid JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
            assert parsed_result["summary"] == "Test summary"
    
    def test_generate_resume_summary_truncated_json(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with truncated JSON response."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock truncated response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test summary", "keywords": "Python, React"'
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should fix truncated JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
    
    def test_generate_resume_summary_malformed_json(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with malformed JSON response."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock malformed response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test summary", "keywords": "Python, React"'
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should create fallback JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
    
    def test_generate_resume_summary_non_json_response(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with non-JSON response."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock non-JSON response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "This is not JSON at all"
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should create fallback JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result


class TestFallbackJSONCreation:
    """Test fallback JSON creation functionality."""
    
    def test_create_fallback_json_valid_content(self):
        """Test fallback JSON creation with valid content."""
        content = '{"summary": "Test summary", "keywords": "Python, React"}'
        result = _create_fallback_json(content, "Software Engineer", "Tech Corp")
        
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
        assert parsed_result["summary"] == "Test summary"
        assert parsed_result["keywords"] == "Python, React"
    
    def test_create_fallback_json_partial_content(self):
        """Test fallback JSON creation with partial content."""
        content = '{"summary": "Test summary"'
        result = _create_fallback_json(content, "Software Engineer", "Tech Corp")
        
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
        assert parsed_result["summary"] == "Test summary"
    
    def test_create_fallback_json_empty_content(self):
        """Test fallback JSON creation with empty content."""
        result = _create_fallback_json("", "Software Engineer", "Tech Corp")
        
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
        assert "software engineer" in parsed_result["summary"].lower()
    
    def test_create_fallback_json_with_job_info(self):
        """Test fallback JSON creation with job information."""
        result = _create_fallback_json("", "Senior Software Engineer", "Google")
        
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
        assert "senior software engineer" in parsed_result["summary"].lower()
    
    def test_create_fallback_json_escaped_content(self):
        """Test fallback JSON creation with escaped content."""
        content = '{"summary": "Test \\"quoted\\" summary", "keywords": "Python, React"}'
        result = _create_fallback_json(content, "Software Engineer", "Tech Corp")
        
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "summary" in parsed_result
        assert "keywords" in parsed_result
        assert "Test" in parsed_result["summary"]


class TestLLMSummaryRetryLogic:
    """Test retry logic in LLM summary generation."""
    
    def test_generate_resume_summary_retry_on_rate_limit(self, sample_job_data):
        """Test retry logic on rate limit error."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client, \
             patch('time.sleep') as mock_sleep:
            
            # Mock rate limit error on first attempt, success on second
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test summary", "keywords": "Python, React"}'
            
            mock_client.chat.completions.create.side_effect = [
                Exception("Rate limit exceeded"),
                mock_response
            ]
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should retry and succeed
            assert isinstance(result, str)
            assert mock_client.chat.completions.create.call_count == 2
            mock_sleep.assert_called()  # Should have slept between retries
    
    def test_generate_resume_summary_retry_on_timeout(self, sample_job_data):
        """Test retry logic on timeout error."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client, \
             patch('time.sleep') as mock_sleep:
            
            # Mock timeout error on first attempt, success on second
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test summary", "keywords": "Python, React"}'
            
            mock_client.chat.completions.create.side_effect = [
                Exception("Request timeout"),
                mock_response
            ]
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should retry and succeed
            assert isinstance(result, str)
            assert mock_client.chat.completions.create.call_count == 2
            mock_sleep.assert_called()
    
    def test_generate_resume_summary_max_retries_exceeded(self, sample_job_data):
        """Test behavior when max retries are exceeded."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
    
            # Mock persistent retryable error with keywords that trigger retry logic
            from src.error_handler import RetryableError
            mock_client.chat.completions.create.side_effect = RetryableError("Rate limit exceeded")
    
            with pytest.raises(RetryableError, match="Rate limit exceeded"):
                generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
    
            # Should have retried the maximum number of times
            assert mock_client.chat.completions.create.call_count == 3  # Default max attempts


class TestLLMSummaryErrorHandling:
    """Test error handling in LLM summary generation."""
    
    def test_generate_resume_summary_fatal_error(self, sample_job_data):
        """Test handling of fatal errors."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock fatal error
            mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
            
            with pytest.raises(Exception, match="Invalid API key"):
                generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
    
    def test_generate_resume_summary_network_error(self, sample_job_data):
        """Test handling of network errors."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client, \
             patch('time.sleep') as mock_sleep:
            
            # Mock network error
            mock_client.chat.completions.create.side_effect = Exception("Network connection failed")
            
            with pytest.raises(Exception, match="Network connection failed"):
                generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
    
    def test_generate_resume_summary_json_error(self, sample_job_data, mock_openai_client):
        """Test handling of JSON parsing errors."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock response that causes JSON error
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test", "keywords": "Python"'  # Missing closing brace
            mock_client.chat.completions.create.return_value = mock_response
            
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should handle JSON error gracefully
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result


@pytest.mark.unit
@pytest.mark.api
class TestLLMSummaryIntegration:
    """Integration tests for LLM summary functionality."""
    
    def test_generate_resume_summary_with_real_prompt(self, sample_job_data, mock_openai_client):
        """Test resume summary generation with realistic prompt."""
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"],
                max_tokens=300
            )
            
            # Should return valid JSON
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
            
            # Summary should be reasonable length
            assert len(parsed_result["summary"]) > 50
            assert len(parsed_result["summary"]) < 500
            
            # Keywords should be comma-separated
            assert "," in parsed_result["keywords"]
    
    def test_generate_resume_summary_different_job_types(self, mock_openai_client):
        """Test resume summary generation for different job types."""
        job_types = ["senior_software_engineer", "frontend_developer", "devops_engineer"]
        
        for job_type in job_types:
            job_data = get_sample_job_data(job_type)
            
            with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
                result = generate_resume_summary(
                    job_data["title"],
                    job_data["company"],
                    job_data["description"]
                )
                
                # Should return valid JSON for each job type
                assert isinstance(result, str)
                parsed_result = json.loads(result)
                assert "summary" in parsed_result
                assert "keywords" in parsed_result
                
                # Summary should mention the job title
                assert job_data["title"].lower() in parsed_result["summary"].lower()
    
    def test_generate_resume_summary_performance(self, sample_job_data, mock_openai_client):
        """Test performance of resume summary generation."""
        import time
        
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            start_time = time.time()
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            end_time = time.time()
            
            # Should complete in reasonable time (less than 10 seconds for mocked call)
            assert end_time - start_time < 10.0
            
            # Should return valid result
            assert isinstance(result, str)
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
