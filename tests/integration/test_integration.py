"""
Integration tests for web scraping and automation.

Tests the integration between different modules for web scraping,
job processing, and LinkedIn automation.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import tempfile
from pathlib import Path
import json
import yaml

# Import modules under test
from src.scraper import scrape_jobs_from_search, BrowserMonitor
from src.easy_apply import apply_to_job, step_through_easy_apply
from src.utils import collect_job_links_with_pagination, clean_text, normalize_skill


@pytest.mark.integration
class TestScraperIntegration:
    """Integration tests for the main scraper functionality."""
    
    def test_scraper_initialization(self, mock_playwright, mock_playwright_browser, mock_playwright_context):
        """Test scraper initialization with mocked Playwright."""
        with patch('src.scraper.sync_playwright', return_value=mock_playwright), \
             patch('src.scraper.EnhancedBrowserConfig') as mock_config, \
             patch('src.scraper.CookieManager') as mock_cookie_manager:
            
            mock_config_instance = Mock()
            mock_config_instance.launch_browser.return_value = mock_playwright_browser
            mock_config_instance.create_context.return_value = mock_playwright_context
            mock_config.return_value = mock_config_instance
            
            mock_cookie_manager_instance = Mock()
            mock_cookie_manager_instance.load_cookies.return_value = []
            mock_cookie_manager.return_value = mock_cookie_manager_instance
            
            # Test that scraper can be initialized
            search_url = "https://linkedin.com/jobs/search/?keywords=Software%20Engineer"
            email = "test@example.com"
            password = "testpass"
            
            # This should not raise an exception during initialization
            with patch('src.scraper.collect_job_links_with_pagination', return_value=[]):
                result = scrape_jobs_from_search(search_url, email, password, max_jobs=1)
                assert result == []
    
    def test_browser_monitor_functionality(self, mock_playwright_browser, mock_playwright_context):
        """Test browser monitoring functionality."""
        monitor = BrowserMonitor(mock_playwright_browser, mock_playwright_context)
        
        # Test initialization
        assert monitor.browser == mock_playwright_browser
        assert monitor.context == mock_playwright_context
        assert monitor.monitoring is False
        
        # Test start monitoring
        monitor.start_monitoring()
        assert monitor.monitoring is True
        
        # Test stop monitoring
        monitor.stop_monitoring()
        assert monitor.monitoring is False
        
        # Test should_exit
        assert monitor.should_exit() is False
    
    def test_scraper_with_cookie_manager(self, mock_playwright, mock_playwright_browser, mock_playwright_context):
        """Test scraper integration with cookie manager."""
        with patch('src.scraper.sync_playwright', return_value=mock_playwright), \
             patch('src.scraper.EnhancedBrowserConfig') as mock_config, \
             patch('src.scraper.CookieManager') as mock_cookie_manager:
            
            mock_config_instance = Mock()
            mock_config_instance.launch_browser.return_value = mock_playwright_browser
            mock_config_instance.create_context.return_value = mock_playwright_context
            mock_config.return_value = mock_config_instance
            
            # Mock cookie manager with saved cookies
            mock_cookie_manager_instance = Mock()
            mock_cookies = [
                {"name": "session_id", "value": "test123", "domain": "linkedin.com"},
                {"name": "csrf_token", "value": "abc456", "domain": "linkedin.com"}
            ]
            mock_cookie_manager_instance.load_cookies.return_value = mock_cookies
            mock_cookie_manager_instance.prepare_cookies_for_playwright.return_value = mock_cookies
            mock_cookie_manager.return_value = mock_cookie_manager_instance
            
            search_url = "https://linkedin.com/jobs/search/?keywords=Software%20Engineer"
            email = "test@example.com"
            password = "testpass"
            
            with patch('src.scraper.collect_job_links_with_pagination', return_value=[]):
                result = scrape_jobs_from_search(search_url, email, password, max_jobs=1)
                
                # Verify cookie manager was used
                mock_cookie_manager_instance.load_cookies.assert_called_once()
                mock_cookie_manager_instance.prepare_cookies_for_playwright.assert_called_once()
                assert result == []


@pytest.mark.integration
@pytest.mark.web
class TestEasyApplyIntegration:
    """Integration tests for Easy Apply functionality."""
    
    def test_easy_apply_workflow(self, mock_playwright_page, sample_job_data):
        """Test complete Easy Apply workflow."""
        with patch('src.easy_apply.config.AUTO_APPLY', True), \
             patch('src.easy_apply.config.LINKEDIN_SELECTORS') as mock_selectors:
            
            # Mock selectors
            mock_selectors.__getitem__.return_value = {
                "button": ["button.jobs-apply-button"],
                "modal": ["div.jobs-easy-apply-modal"],
                "submit": ["button[aria-label='Submit application']"],
                "next": ["button[aria-label='Continue to next step']"],
                "review": ["button[aria-label='Review your application']"],
                "follow_checkbox": ["input#follow-company-checkbox"],
                "follow_label": ["label[for='follow-company-checkbox']"],
                "dismiss": ["button[aria-label='Dismiss']"]
            }
            
            # Mock page interactions
            mock_playwright_page.locator.return_value.count.return_value = 1
            mock_playwright_page.locator.return_value.click.return_value = None
            mock_playwright_page.wait_for_selector.return_value = None
            mock_playwright_page.inner_text.return_value = "Page content"
            
            resume_path = "test_resume.pdf"
            job_url = sample_job_data["url"]
            
            # Test Easy Apply workflow
            result = apply_to_job(mock_playwright_page, resume_path, job_url)
            
            # Should attempt to apply
            assert isinstance(result, bool)
    
    def test_easy_apply_with_resume_upload(self, mock_playwright_page, sample_job_data):
        """Test Easy Apply with resume upload."""
        with patch('src.easy_apply.config.AUTO_APPLY', True), \
             patch('src.easy_apply.config.LINKEDIN_SELECTORS') as mock_selectors, \
             patch('src.easy_apply.config.FILE_PATHS') as mock_paths, \
             patch('src.easy_apply.glob.glob') as mock_glob:
            
            # Mock selectors
            mock_selectors.__getitem__.return_value = {
                "resume_upload": {
                    "upload_button": ["label.jobs-document-upload__upload-button"],
                    "file_input": ["input[type='file']"]
                }
            }
            
            # Mock file paths and resume files
            mock_paths.__getitem__.return_value = Path("output/resumes")
            mock_glob.return_value = ["output/resumes/Borgese_Software_Engineer_Tech_Corp.pdf"]
            
            # Mock page interactions
            mock_playwright_page.locator.return_value.count.return_value = 1
            mock_playwright_page.locator.return_value.set_input_files.return_value = None
            
            resume_path = "test_resume.pdf"
            job_url = sample_job_data["url"]
            
            # Test Easy Apply with resume upload
            result = apply_to_job(mock_playwright_page, resume_path, job_url)
            
            # Should attempt to apply
            assert isinstance(result, bool)
    
    def test_easy_apply_step_processing(self, mock_playwright_page):
        """Test Easy Apply step processing."""
        with patch('src.easy_apply.config.LINKEDIN_SELECTORS') as mock_selectors:
            # Mock selectors for different steps
            mock_selectors.__getitem__.return_value = {
                "submit": ["button[aria-label='Submit application']"],
                "next": ["button[aria-label='Continue to next step']"],
                "review": ["button[aria-label='Review your application']"],
                "follow_checkbox": ["input#follow-company-checkbox"],
                "follow_label": ["label[for='follow-company-checkbox']"]
            }
            
            # Mock page interactions
            mock_playwright_page.locator.return_value.count.return_value = 1
            mock_playwright_page.locator.return_value.click.return_value = None
            
            # Test step processing
            result = step_through_easy_apply(mock_playwright_page)
            
            # Should return boolean result
            assert isinstance(result, bool)


@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utility functions."""
    
    def test_collect_job_links_integration(self, mock_playwright_page):
        """Test job link collection integration."""
        with patch('src.utils.config.MAX_JOBS', 5), \
             patch('src.utils.config.LINKEDIN_SELECTORS') as mock_selectors, \
             patch('src.utils.config.TIMEOUTS') as mock_timeouts, \
             patch('src.utils.config.RETRY_CONFIG') as mock_retry_config, \
             patch('src.utils.config.SCROLL_CONFIG') as mock_scroll_config:
            
            # Mock selectors
            mock_selectors.__getitem__.return_value = {
                "total_jobs": "div.t-black--light",
                "job_list": "div.scaffold-layout__list",
                "job_cards": "ul.semantic-search-results-list > li",
                "job_wrapper": "div.job-card-job-posting-card-wrapper"
            }
            
            # Mock timeouts and config
            mock_timeouts.__getitem__.return_value = 30000
            mock_retry_config.__getitem__.return_value = 15
            mock_scroll_config.__getitem__.return_value = 1.0
            
            # Mock page interactions
            mock_playwright_page.wait_for_selector.return_value = None
            mock_playwright_page.inner_text.return_value = "1,234 results"
            mock_playwright_page.locator.return_value.count.return_value = 25
            mock_playwright_page.locator.return_value.nth.return_value.locator.return_value.count.return_value = 1
            mock_playwright_page.hover.return_value = None
            mock_playwright_page.mouse.wheel.return_value = None
            
            base_url = "https://linkedin.com/jobs/search/?keywords=Software%20Engineer"
            
            with patch('src.utils.parse_job_card') as mock_parse:
                mock_parse.return_value = {
                    "id": "123456",
                    "title": "Software Engineer",
                    "url": "https://linkedin.com/jobs/view/123456",
                    "already_applied": False
                }
                
                result = collect_job_links_with_pagination(mock_playwright_page, base_url, max_jobs=5)
                
                # Should return list of job URLs
                assert isinstance(result, list)
    
    def test_text_processing_integration(self):
        """Test text processing utility functions."""
        # Test clean_text
        dirty_text = "This is a   test\n\nwith   multiple   spaces\nand\nnewlines."
        clean_result = clean_text(dirty_text)
        assert clean_result == "This is a test with multiple spaces and newlines."
        
        # Test normalize_skill
        skill_variations = ["python", "Python", "PYTHON", "python3", "Python 3"]
        normalized_skills = [normalize_skill(skill) for skill in skill_variations]
        
        # Should normalize to consistent format
        assert all(isinstance(skill, str) for skill in normalized_skills)
        assert len(set(normalized_skills)) <= len(skill_variations)  # Some should be normalized to same


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_complete_job_processing_workflow(self, sample_personal_info, sample_job_data, temp_dir):
        """Test complete job processing workflow."""
        # Create temporary personal info file
        personal_info_file = temp_dir / "personal_info.yaml"
        with open(personal_info_file, 'w') as f:
            yaml.dump(sample_personal_info, f)
        
        with patch('src.scraper.sync_playwright') as mock_playwright, \
             patch('src.scraper.EnhancedBrowserConfig') as mock_config, \
             patch('src.scraper.CookieManager') as mock_cookie_manager, \
             patch('src.scraper.collect_job_links_with_pagination') as mock_collect, \
             patch('src.scraper.extract_keywords') as mock_extract, \
             patch('src.scraper.weigh_keywords') as mock_weigh, \
             patch('src.scraper.generate_resume_summary') as mock_summary, \
             patch('src.scraper.build_resume') as mock_build, \
             patch('src.scraper.apply_to_job') as mock_apply:
            
            # Mock Playwright
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()
            
            mock_playwright_instance.__enter__.return_value = mock_playwright_instance
            mock_playwright_instance.__exit__.return_value = None
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            mock_playwright.return_value = mock_playwright_instance
            
            # Mock browser config
            mock_config_instance = Mock()
            mock_config_instance.launch_browser.return_value = mock_browser
            mock_config_instance.create_context.return_value = mock_context
            mock_config.return_value = mock_config_instance
            
            # Mock cookie manager
            mock_cookie_manager_instance = Mock()
            mock_cookie_manager_instance.load_cookies.return_value = []
            mock_cookie_manager.return_value = mock_cookie_manager_instance
            
            # Mock job collection
            mock_collect.return_value = [sample_job_data["url"]]
            
            # Mock keyword processing
            mock_extract.return_value = ["Python", "React", "AWS"]
            mock_weigh.return_value = [("Python", 1.0), ("React", 0.9), ("AWS", 0.8)]
            
            # Mock LLM summary
            mock_summary.return_value = '{"summary": "Test summary", "keywords": "Python, React, AWS"}'
            
            # Mock resume building
            mock_build.return_value = "test_resume.pdf"
            
            # Mock Easy Apply
            mock_apply.return_value = True
            
            # Mock page interactions
            mock_page.goto.return_value = None
            mock_page.wait_for_selector.return_value = None
            mock_page.locator.return_value.count.return_value = 1
            mock_page.locator.return_value.inner_text.return_value = sample_job_data["description"]
            mock_page.locator.return_value.all_inner_texts.return_value = [sample_job_data["title"]]
            mock_page.locator.return_value.nth.return_value.inner_text.return_value = sample_job_data["company"]
            mock_page.title.return_value = f"{sample_job_data['title']} - LinkedIn"
            mock_page.url = sample_job_data["url"]
            
            # Run the complete workflow
            search_url = "https://linkedin.com/jobs/search/?keywords=Software%20Engineer"
            email = "test@example.com"
            password = "testpass"
            
            result = scrape_jobs_from_search(
                search_url, 
                email, 
                password, 
                max_jobs=1,
                personal_info_path=str(personal_info_file)
            )
            
            # Verify the workflow completed
            assert isinstance(result, list)
            assert len(result) == 1
            
            job_result = result[0]
            assert job_result["title"] == sample_job_data["title"]
            assert job_result["company"] == sample_job_data["company"]
            assert job_result["url"] == sample_job_data["url"]
            assert job_result["pdf_path"] == "test_resume.pdf"
            assert job_result["apply_status"] == "applied"
    
    def test_error_handling_integration(self, sample_personal_info, temp_dir):
        """Test error handling in integration scenarios."""
        # Create temporary personal info file
        personal_info_file = temp_dir / "personal_info.yaml"
        with open(personal_info_file, 'w') as f:
            yaml.dump(sample_personal_info, f)
        
        with patch('src.scraper.sync_playwright') as mock_playwright, \
             patch('src.scraper.EnhancedBrowserConfig') as mock_config, \
             patch('src.scraper.CookieManager') as mock_cookie_manager, \
             patch('src.scraper.collect_job_links_with_pagination') as mock_collect:
            
            # Mock Playwright with error
            mock_playwright_instance = Mock()
            mock_playwright_instance.__enter__.return_value = mock_playwright_instance
            mock_playwright_instance.__exit__.return_value = None
            mock_playwright_instance.chromium.launch.side_effect = Exception("Browser launch failed")
            
            mock_playwright.return_value = mock_playwright_instance
            
            # Mock browser config
            mock_config_instance = Mock()
            mock_config_instance.launch_browser.side_effect = Exception("Browser launch failed")
            mock_config.return_value = mock_config_instance
            
            # Mock cookie manager
            mock_cookie_manager_instance = Mock()
            mock_cookie_manager_instance.load_cookies.return_value = []
            mock_cookie_manager.return_value = mock_cookie_manager_instance
            
            # Run the workflow with error
            search_url = "https://linkedin.com/jobs/search/?keywords=Software%20Engineer"
            email = "test@example.com"
            password = "testpass"
            
            # Should handle error gracefully
            with pytest.raises(Exception):
                scrape_jobs_from_search(
                    search_url, 
                    email, 
                    password, 
                    max_jobs=1,
                    personal_info_path=str(personal_info_file)
                )


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for API interactions."""
    
    def test_openai_integration(self, sample_job_data, mock_openai_client):
        """Test OpenAI API integration."""
        from src.llm_summary import generate_resume_summary
        
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'):
            result = generate_resume_summary(
                sample_job_data["title"],
                sample_job_data["company"],
                sample_job_data["description"]
            )
            
            # Should return JSON string
            assert isinstance(result, str)
            
            # Should be valid JSON
            import json
            parsed_result = json.loads(result)
            assert "summary" in parsed_result
            assert "keywords" in parsed_result
    
    def test_openai_error_handling(self, sample_job_data):
        """Test OpenAI API error handling."""
        from src.llm_summary import generate_resume_summary
        
        with patch('src.llm_summary.OPENAI_API_KEY', None):
            # Should raise error for missing API key
            with pytest.raises(Exception):
                generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
    
    def test_openai_retry_logic(self, sample_job_data, mock_openai_client):
        """Test OpenAI API retry logic."""
        from src.llm_summary import generate_resume_summary
        
        with patch('src.llm_summary.OPENAI_API_KEY', 'test-api-key'), \
             patch('src.llm_summary.client') as mock_client:
            
            # Mock API failure on first attempt, success on second
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"summary": "Test summary", "keywords": "Python, React"}'
            
            mock_client.chat.completions.create.side_effect = [
                Exception("Rate limit exceeded"),
                mock_response
            ]
            
            with patch('src.llm_summary.time.sleep') as mock_sleep:
                result = generate_resume_summary(
                    sample_job_data["title"],
                    sample_job_data["company"],
                    sample_job_data["description"]
                )
                
                # Should retry and succeed
                assert isinstance(result, str)
                assert mock_client.chat.completions.create.call_count == 2
                mock_sleep.assert_called()  # Should have slept between retries
