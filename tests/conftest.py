"""
Pytest configuration and shared fixtures for resume-generator-auto-applier.

This module provides common fixtures, test utilities, and configuration
for all test modules in the project.
"""

import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
import pytest
from playwright.sync_api import sync_playwright

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_OUTPUT_DIR = Path(__file__).parent / "output"
MOCK_DATA_DIR = Path(__file__).parent / "mock_data"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True)
MOCK_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return TEST_DATA_DIR


@pytest.fixture(scope="session")
def test_output_dir():
    """Provide path to test output directory."""
    return TEST_OUTPUT_DIR


@pytest.fixture(scope="session")
def mock_data_dir():
    """Provide path to mock data directory."""
    return MOCK_DATA_DIR


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_personal_info():
    """Provide sample personal information for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
        "address": "123 Main St, Anytown, ST 12345",
        "job_history": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01",
                "end_date": "Present",
                "responsibilities": [
                    "Developed scalable web applications",
                    "Led team of 5 engineers",
                    "Implemented CI/CD pipelines"
                ]
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "start_date": "2018-06",
                "end_date": "2019-12",
                "responsibilities": [
                    "Built REST APIs",
                    "Optimized database queries",
                    "Collaborated with product team"
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "school": "University of Technology",
                "year": "2018"
            }
        ],
        "references": [
            {
                "name": "Jane Smith",
                "title": "Engineering Manager",
                "company": "Tech Corp",
                "email": "jane.smith@techcorp.com"
            }
        ]
    }


@pytest.fixture
def sample_job_description():
    """Provide sample job description for testing."""
    return """
    We are looking for a Senior Software Engineer to join our dynamic team.
    
    Requirements:
    - 5+ years of experience in Python development
    - Strong knowledge of React and JavaScript
    - Experience with AWS cloud services
    - Familiarity with Docker and Kubernetes
    - Knowledge of SQL databases
    - Experience with CI/CD pipelines
    - Strong problem-solving skills
    - Excellent communication skills
    
    Responsibilities:
    - Design and develop scalable web applications
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Participate in code reviews
    - Contribute to architectural decisions
    
    Nice to have:
    - Experience with machine learning
    - Knowledge of GraphQL
    - Previous startup experience
    """


@pytest.fixture
def sample_job_data():
    """Provide sample job data for testing."""
    return {
        "title": "Senior Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "url": "https://linkedin.com/jobs/view/123456789",
        "description": sample_job_description(),
        "keywords": ["Python", "React", "AWS", "Docker", "Kubernetes", "SQL"],
        "matched_keywords": ["Python", "React", "AWS", "Docker"]
    }


@pytest.fixture
def mock_openai_response():
    """Provide mock OpenAI API response."""
    return {
        "summary": "Experienced software engineer with 5+ years of expertise in Python development, React, and cloud technologies. Proven track record of building scalable applications and leading technical initiatives.",
        "keywords": "Python, React, AWS, Docker, Kubernetes, SQL, CI/CD"
    }


@pytest.fixture
def mock_playwright_page():
    """Provide a mock Playwright page object."""
    page = Mock()
    page.url = "https://linkedin.com/jobs/view/123456789"
    page.title.return_value = "Senior Software Engineer - Tech Corp | LinkedIn"
    page.locator.return_value.count.return_value = 1
    page.locator.return_value.inner_text.return_value = "Sample text"
    page.locator.return_value.click.return_value = None
    page.locator.return_value.fill.return_value = None
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    page.wait_for_timeout.return_value = None
    page.hover.return_value = None
    page.mouse.wheel.return_value = None
    page.inner_text.return_value = "Page content"
    return page


@pytest.fixture
def mock_playwright_context():
    """Provide a mock Playwright context object."""
    context = Mock()
    context.new_page.return_value = mock_playwright_page()
    context.add_cookies.return_value = None
    context.cookies.return_value = []
    return context


@pytest.fixture
def mock_playwright_browser():
    """Provide a mock Playwright browser object."""
    browser = Mock()
    browser.contexts = [mock_playwright_context()]
    browser.close.return_value = None
    return browser


@pytest.fixture
def mock_playwright():
    """Provide a mock Playwright instance."""
    playwright = Mock()
    playwright.chromium.launch.return_value = mock_playwright_browser()
    playwright.chromium.launch_persistent_context.return_value = mock_playwright_context()
    return playwright


@pytest.fixture
def mock_file_handler():
    """Provide mock file handler for testing file operations."""
    handler = Mock()
    handler.load_json.return_value = []
    handler.save_json.return_value = True
    handler.load_yaml.return_value = {}
    handler.save_yaml.return_value = True
    return handler


@pytest.fixture
def mock_cookie_manager():
    """Provide mock cookie manager for testing."""
    manager = Mock()
    manager.load_cookies.return_value = []
    manager.save_cookies.return_value = True
    manager.delete_cookies.return_value = True
    manager.prepare_cookies_for_playwright.return_value = []
    manager.refresh_cookies_if_needed.return_value = True
    return manager


@pytest.fixture
def mock_error_handler():
    """Provide mock error handler for testing."""
    handler = Mock()
    handler.handle_openai_failure.return_value = '{"summary": "test", "keywords": "test"}'
    handler.handle_weasyprint_failure.return_value = True
    return handler


@pytest.fixture
def sample_resume_payload():
    """Provide sample resume payload for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
        "address": "123 Main St, Anytown, ST 12345",
        "summary": "Experienced software engineer with 5+ years of expertise in Python development.",
        "skills": ["Python", "React", "AWS", "Docker", "Kubernetes"],
        "matched_keywords": ["Python", "React", "AWS"],
        "experiences": [
            {
                "role": "Senior Software Engineer",
                "company": "Tech Corp",
                "years": "2020-01 - Present",
                "responsibilities": ["Developed scalable web applications", "Led team of 5 engineers"]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "school": "University of Technology",
                "year": "2018"
            }
        ],
        "references": [
            {
                "name": "Jane Smith",
                "title": "Engineering Manager",
                "company": "Tech Corp",
                "email": "jane.smith@techcorp.com"
            }
        ],
        "title": "Senior Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "description": "Job description here..."
    }


@pytest.fixture
def mock_env_vars():
    """Provide mock environment variables for testing."""
    return {
        "LINKEDIN_EMAIL": "test@example.com",
        "LINKEDIN_PASSWORD": "testpassword",
        "OPENAI_API_KEY": "test-api-key",
        "DEBUG": "false",
        "HEADLESS_MODE": "true",
        "MAX_JOBS": "5",
        "AUTO_APPLY": "false"
    }


@pytest.fixture(autouse=True)
def setup_test_env(mock_env_vars):
    """Automatically set up test environment variables."""
    with patch.dict(os.environ, mock_env_vars):
        yield


@pytest.fixture
def mock_weasyprint():
    """Provide mock WeasyPrint for testing PDF generation."""
    with patch('weasyprint.HTML') as mock_html:
        mock_instance = Mock()
        mock_instance.write_pdf.return_value = None
        mock_html.return_value = mock_instance
        yield mock_html


@pytest.fixture
def mock_jinja2():
    """Provide mock Jinja2 for testing template rendering."""
    with patch('jinja2.Environment') as mock_env:
        mock_template = Mock()
        mock_template.render.return_value = "<html><body>Test Resume</body></html>"
        mock_env.return_value.get_template.return_value = mock_template
        yield mock_env


@pytest.fixture
def mock_spacy():
    """Provide mock spaCy for testing NLP functionality."""
    with patch('spacy.load') as mock_load:
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_token = Mock()
        mock_token.pos_ = "NOUN"
        mock_token.text = "Python"
        mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp
        yield mock_load


@pytest.fixture
def mock_openai_client():
    """Provide mock OpenAI client for testing."""
    with patch('openai.OpenAI') as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"summary": "test", "keywords": "test"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_tech_dictionary():
    """Provide sample tech dictionary for testing."""
    return {
        "programming_languages": ["Python", "JavaScript", "Java", "C++", "Go"],
        "frameworks": ["React", "Django", "Flask", "Express", "Spring"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
        "cloud_platforms": ["AWS", "Azure", "GCP", "Docker", "Kubernetes"],
        "tools": ["Git", "Jenkins", "Terraform", "Ansible"]
    }


@pytest.fixture
def sample_stopwords():
    """Provide sample stopwords for testing."""
    return {
        "stopwords": [
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during"
        ]
    }


@pytest.fixture
def sample_keyword_weights():
    """Provide sample keyword weights for testing."""
    return {
        "Python": 1.0,
        "React": 0.9,
        "AWS": 0.8,
        "Docker": 0.7,
        "Kubernetes": 0.6,
        "SQL": 0.5
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = ".txt") -> Path:
        """Create a temporary file with given content."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)
    
    @staticmethod
    def create_temp_yaml(data: Dict[str, Any]) -> Path:
        """Create a temporary YAML file with given data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(data, temp_file)
        temp_file.close()
        return Path(temp_file.name)
    
    @staticmethod
    def create_temp_json(data: Dict[str, Any]) -> Path:
        """Create a temporary JSON file with given data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, temp_file)
        temp_file.close()
        return Path(temp_file.name)


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "web: Web scraping tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "mock: Mock tests")
    config.addinivalue_line("markers", "skip_ci: Skip in CI")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "web" in item.nodeid:
            item.add_marker(pytest.mark.web)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        # Add slow marker for tests that might take time
        if any(keyword in item.nodeid.lower() for keyword in ["scrape", "browser", "playwright"]):
            item.add_marker(pytest.mark.slow)


# Cleanup hooks
def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    # Clean up any temporary files created during tests
    import tempfile
    tempfile.tempdir = None
