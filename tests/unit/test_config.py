"""
Unit tests for configuration management.

Tests the config.py module for proper configuration loading,
validation, and environment variable handling.
"""

import os
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
import tempfile
import shutil

# Import the module under test
import src.config as config


class TestConfigValidation:
    """Test configuration validation functionality."""
    
    def test_validate_config_success(self, temp_dir):
        """Test successful configuration validation."""
        # Create required directories
        resumes_dir = temp_dir / "output" / "resumes"
        templates_dir = temp_dir / "templates"
        resumes_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)
        
        with patch('src.config.RESUMES_DIR', resumes_dir), \
             patch('src.config.TEMPLATES_DIR', templates_dir), \
             patch('src.config.LINKEDIN_EMAIL', 'test@example.com'), \
             patch('src.config.LINKEDIN_PASSWORD', 'testpass'):
            
            result = config.validate_config()
            assert result is True
    
    def test_validate_config_missing_email(self, temp_dir):
        """Test configuration validation with missing email."""
        resumes_dir = temp_dir / "output" / "resumes"
        templates_dir = temp_dir / "templates"
        resumes_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)
        
        with patch('src.config.RESUMES_DIR', resumes_dir), \
             patch('src.config.TEMPLATES_DIR', templates_dir), \
             patch('src.config.LINKEDIN_EMAIL', None), \
             patch('src.config.LINKEDIN_PASSWORD', 'testpass'):
            
            with pytest.raises(ValueError, match="LINKEDIN_EMAIL is required"):
                config.validate_config()
    
    def test_validate_config_missing_password(self, temp_dir):
        """Test configuration validation with missing password."""
        resumes_dir = temp_dir / "output" / "resumes"
        templates_dir = temp_dir / "templates"
        resumes_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)
        
        with patch('src.config.RESUMES_DIR', resumes_dir), \
             patch('src.config.TEMPLATES_DIR', templates_dir), \
             patch('src.config.LINKEDIN_EMAIL', 'test@example.com'), \
             patch('src.config.LINKEDIN_PASSWORD', None):
            
            with pytest.raises(ValueError, match="LINKEDIN_PASSWORD is required"):
                config.validate_config()
    
    def test_validate_config_creates_directories(self, temp_dir):
        """Test that validation creates missing directories."""
        resumes_dir = temp_dir / "output" / "resumes"
        templates_dir = temp_dir / "templates"
        
        with patch('src.config.RESUMES_DIR', resumes_dir), \
             patch('src.config.TEMPLATES_DIR', templates_dir), \
             patch('src.config.LINKEDIN_EMAIL', 'test@example.com'), \
             patch('src.config.LINKEDIN_PASSWORD', 'testpass'):
            
            # Directories don't exist initially
            assert not resumes_dir.exists()
            assert not templates_dir.exists()
            
            result = config.validate_config()
            
            # Directories should be created
            assert resumes_dir.exists()
            assert templates_dir.exists()
            assert result is True


class TestConfigConstants:
    """Test configuration constants and their values."""
    
    def test_base_directory_structure(self):
        """Test that base directory structure is correct."""
        assert isinstance(config.BASE_DIR, Path)
        assert config.BASE_DIR.exists()
        assert config.OUTPUT_DIR == config.BASE_DIR / "output"
        assert config.RESUMES_DIR == config.OUTPUT_DIR / "resumes"
        assert config.TEMPLATES_DIR == config.BASE_DIR / "templates"
    
    def test_timeout_configuration(self):
        """Test timeout configuration values."""
        assert isinstance(config.TIMEOUTS, dict)
        assert "page_load" in config.TIMEOUTS
        assert "login" in config.TIMEOUTS
        assert "search_page" in config.TIMEOUTS
        assert "job_page" in config.TIMEOUTS
        
        # All timeouts should be positive integers
        for timeout_name, timeout_value in config.TIMEOUTS.items():
            assert isinstance(timeout_value, int)
            assert timeout_value > 0
    
    def test_retry_configuration(self):
        """Test retry configuration values."""
        assert isinstance(config.RETRY_CONFIG, dict)
        assert "max_attempts" in config.RETRY_CONFIG
        assert "retry_delay" in config.RETRY_CONFIG
        assert "max_scroll_passes" in config.RETRY_CONFIG
        assert "max_steps" in config.RETRY_CONFIG
        
        # All retry values should be positive
        assert config.RETRY_CONFIG["max_attempts"] > 0
        assert config.RETRY_CONFIG["retry_delay"] > 0
        assert config.RETRY_CONFIG["max_scroll_passes"] > 0
        assert config.RETRY_CONFIG["max_steps"] > 0
    
    def test_linkedin_selectors_structure(self):
        """Test LinkedIn selectors configuration structure."""
        assert isinstance(config.LINKEDIN_SELECTORS, dict)
        
        # Check main sections exist
        assert "login" in config.LINKEDIN_SELECTORS
        assert "job_search" in config.LINKEDIN_SELECTORS
        assert "job_detail" in config.LINKEDIN_SELECTORS
        assert "easy_apply" in config.LINKEDIN_SELECTORS
        
        # Check login selectors
        login_selectors = config.LINKEDIN_SELECTORS["login"]
        assert "username" in login_selectors
        assert "password" in login_selectors
        assert "submit" in login_selectors
        
        # Check job search selectors
        job_search_selectors = config.LINKEDIN_SELECTORS["job_search"]
        assert "job_list" in job_search_selectors
        assert "job_cards" in job_search_selectors
        assert "job_wrapper" in job_search_selectors
    
    def test_file_paths_configuration(self):
        """Test file paths configuration."""
        assert isinstance(config.FILE_PATHS, dict)
        
        # Check required file paths exist
        assert "personal_info" in config.FILE_PATHS
        assert "job_urls" in config.FILE_PATHS
        assert "stopwords" in config.FILE_PATHS
        assert "tech_dictionary" in config.FILE_PATHS
        assert "keyword_weights" in config.FILE_PATHS
        
        # All paths should be Path objects
        for path_name, path_value in config.FILE_PATHS.items():
            assert isinstance(path_value, Path)
    
    def test_scroll_configuration(self):
        """Test scroll configuration values."""
        assert isinstance(config.SCROLL_CONFIG, dict)
        assert "base_speed" in config.SCROLL_CONFIG
        assert "min_speed" in config.SCROLL_CONFIG
        assert "max_speed" in config.SCROLL_CONFIG
        assert "pause_between" in config.SCROLL_CONFIG
        
        # Speed values should be positive
        assert config.SCROLL_CONFIG["base_speed"] > 0
        assert config.SCROLL_CONFIG["min_speed"] > 0
        assert config.SCROLL_CONFIG["max_speed"] > 0
        assert config.SCROLL_CONFIG["pause_between"] > 0
        
        # Min speed should be less than max speed
        assert config.SCROLL_CONFIG["min_speed"] <= config.SCROLL_CONFIG["max_speed"]
    
    def test_question_configuration(self):
        """Test question answering configuration."""
        assert isinstance(config.QUESTION_CONFIG, dict)
        assert "skip_questions" in config.QUESTION_CONFIG
        assert "ignore_keywords" in config.QUESTION_CONFIG
        assert "default_answers" in config.QUESTION_CONFIG
        
        # Check skip questions is a list
        assert isinstance(config.QUESTION_CONFIG["skip_questions"], list)
        
        # Check default answers is a dict
        assert isinstance(config.QUESTION_CONFIG["default_answers"], dict)
    
    def test_delay_configuration(self):
        """Test delay configuration values."""
        assert isinstance(config.DELAYS, dict)
        
        # Check required delays exist
        assert "login_processing" in config.DELAYS
        assert "ui_stability" in config.DELAYS
        assert "easy_apply_hover" in config.DELAYS
        assert "modal_wait" in config.DELAYS
        assert "step_processing" in config.DELAYS
        
        # All delays should be positive
        for delay_name, delay_value in config.DELAYS.items():
            if isinstance(delay_value, (int, float)):
                assert delay_value > 0
            elif isinstance(delay_value, tuple):
                assert len(delay_value) == 2
                assert delay_value[0] > 0
                assert delay_value[1] > delay_value[0]


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_linkedin_credentials_from_env(self):
        """Test LinkedIn credentials are loaded from environment."""
        with patch.dict(os.environ, {
            'LINKEDIN_EMAIL': 'test@example.com',
            'LINKEDIN_PASSWORD': 'testpass'
        }):
            # Reload config to pick up new env vars
            import importlib
            importlib.reload(config)
            
            assert config.LINKEDIN_EMAIL == 'test@example.com'
            assert config.LINKEDIN_PASSWORD == 'testpass'
    
    def test_optional_links_from_env(self):
        """Test optional links are loaded from environment."""
        with patch.dict(os.environ, {
            'PORTFOLIO': 'https://example.com/portfolio'
        }):
            import importlib
            importlib.reload(config)
            
            assert config.PORTFOLIO == 'https://example.com/portfolio'
    
    def test_job_search_settings_from_env(self):
        """Test job search settings are loaded from environment."""
        with patch.dict(os.environ, {
            'MAX_JOBS': '25',
            'AUTO_APPLY': 'false',
            'DEFAULT_TEMPLATE': 'custom_resume.html'
        }):
            import importlib
            importlib.reload(config)
            
            assert config.MAX_JOBS == 25
            assert config.AUTO_APPLY is False
            assert config.DEFAULT_TEMPLATE == 'custom_resume.html'
    
    def test_browser_configuration_from_env(self):
        """Test browser configuration is loaded from environment."""
        with patch.dict(os.environ, {
            'HEADLESS_MODE': 'true',
            'ENABLE_BROWSER_MONITORING': 'true',
            'SUPPRESS_CONSOLE_WARNINGS': 'false'
        }):
            import importlib
            importlib.reload(config)
            
            assert config.HEADLESS_MODE is True
            assert config.ENABLE_BROWSER_MONITORING is True
            assert config.SUPPRESS_CONSOLE_WARNINGS is False
    
    def test_debug_mode_from_env(self):
        """Test debug mode is loaded from environment."""
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            import importlib
            importlib.reload(config)
            
            assert config.DEBUG is True
    
    def test_timeout_values_from_env(self):
        """Test timeout values are loaded from environment."""
        with patch.dict(os.environ, {
            'TIMEOUT_PAGE_LOAD': '60000',
            'TIMEOUT_LOGIN': '45000',
            'TIMEOUT_SEARCH_PAGE': '60000'
        }):
            import importlib
            importlib.reload(config)
            
            assert config.TIMEOUTS["page_load"] == 60000
            assert config.TIMEOUTS["login"] == 45000
            assert config.TIMEOUTS["search_page"] == 60000
    
    def test_retry_values_from_env(self):
        """Test retry values are loaded from environment."""
        with patch.dict(os.environ, {
            'MAX_RETRY_ATTEMPTS': '5',
            'RETRY_DELAY': '2.0',
            'MAX_SCROLL_PASSES': '20'
        }):
            import importlib
            importlib.reload(config)
            
            assert config.RETRY_CONFIG["max_attempts"] == 5
            assert config.RETRY_CONFIG["retry_delay"] == 2.0
            assert config.RETRY_CONFIG["max_scroll_passes"] == 20


class TestConfigDefaults:
    """Test default configuration values."""
    
    def test_default_max_jobs(self):
        """Test default MAX_JOBS value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.MAX_JOBS == 15  # Default value
    
    def test_default_auto_apply(self):
        """Test default AUTO_APPLY value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.AUTO_APPLY is True  # Default value
    
    def test_default_template(self):
        """Test default template value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.DEFAULT_TEMPLATE == "base_resume.html"
    
    def test_default_debug_mode(self):
        """Test default debug mode value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.DEBUG is False  # Default value
    
    def test_default_headless_mode(self):
        """Test default headless mode value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            
            assert config.HEADLESS_MODE is False  # Default value


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for configuration module."""
    
    def test_config_import_success(self):
        """Test that config module imports successfully."""
        import src.config as config_module
        assert config_module is not None
        assert hasattr(config_module, 'BASE_DIR')
        assert hasattr(config_module, 'TIMEOUTS')
        assert hasattr(config_module, 'LINKEDIN_SELECTORS')
    
    def test_config_validation_on_import(self):
        """Test that validation runs on import."""
        # This test ensures that validate_config() is called on import
        # If it fails, the import would fail
        import src.config as config_module
        assert config_module is not None
