# Testing Guide for Resume Generator & Auto-Applicator

This document provides comprehensive guidance on testing the resume generator and auto-applicator system.

## Test Structure

The testing framework is organized as follows:

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── unit/                       # Unit tests
│   ├── test_config.py         # Configuration management tests
│   ├── test_keyword_extractor.py  # Keyword extraction tests
│   ├── test_resume_builder.py     # Resume building tests
│   ├── test_llm_summary.py        # LLM integration tests
│   └── test_error_handler.py      # Error handling tests
├── integration/                # Integration tests
│   └── test_integration.py    # End-to-end integration tests
├── fixtures/                   # Test data and fixtures
│   └── test_data.py           # Sample data and mock objects
├── data/                       # Test data files
├── output/                     # Test output directory
└── mock_data/                  # Mock data for testing
```

## Test Categories

### Unit Tests (`pytest.mark.unit`)
- Test individual functions and classes in isolation
- Use mocks to avoid external dependencies
- Fast execution (< 1 second per test)
- High code coverage

### Integration Tests (`pytest.mark.integration`)
- Test interaction between multiple modules
- May use real external services (with caution)
- Moderate execution time (1-10 seconds per test)

### Web Tests (`pytest.mark.web`)
- Test web scraping and browser automation
- Require Playwright and browser setup
- Slower execution (10+ seconds per test)
- May be skipped in CI environments

### API Tests (`pytest.mark.api`)
- Test external API integrations (OpenAI, LinkedIn)
- Require API keys or mocking
- May have rate limits

### Slow Tests (`pytest.mark.slow`)
- Tests that take longer than 5 seconds
- Can be skipped for quick feedback

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py all

# Run only unit tests
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run web tests (requires browser setup)
python run_tests.py web

# Run API tests
python run_tests.py api

# Generate coverage report
python run_tests.py coverage

# Run tests with HTML report
python run_tests.py all --html-report

# Run tests in parallel
python run_tests.py all --parallel 4

# Quick test run (unit tests only, stop on first failure)
python run_tests.py quick
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_config.py

# Run tests with specific marker
pytest -m unit
pytest -m integration
pytest -m web
pytest -m api

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests in parallel
pytest -n 4

# Run tests with HTML report
pytest --html=report.html --self-contained-html

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x

# Run tests with specific pattern
pytest -k "test_config"
```

## Test Configuration

### Environment Variables

Set these environment variables for testing:

```bash
# Required for testing
export TESTING=true
export DEBUG=false
export HEADLESS_MODE=true
export ENABLE_BROWSER_MONITORING=false
export SUPPRESS_CONSOLE_WARNINGS=true

# Optional for API tests
export OPENAI_API_KEY=test-key
export LINKEDIN_EMAIL=test@example.com
export LINKEDIN_PASSWORD=testpass
```

### Pytest Configuration

The `pytest.ini` file contains:
- Test discovery patterns
- Output options
- Markers for test categorization
- Coverage configuration
- Logging settings

## Test Data and Fixtures

### Sample Data

The `tests/fixtures/test_data.py` module provides:
- Sample personal information
- Sample job descriptions
- Sample tech dictionary
- Sample stopwords
- Sample keyword weights
- Sample resume payloads
- Mock Playwright objects

### Fixtures

Common fixtures available in `conftest.py`:
- `temp_dir`: Temporary directory for test isolation
- `sample_personal_info`: Sample personal information
- `sample_job_description`: Sample job description
- `sample_job_data`: Complete job data
- `mock_playwright_page`: Mock Playwright page object
- `mock_openai_client`: Mock OpenAI client
- `mock_weasyprint`: Mock WeasyPrint
- `mock_jinja2`: Mock Jinja2 template engine

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch, Mock
from src.config import validate_config

class TestConfigValidation:
    def test_validate_config_success(self, temp_dir):
        """Test successful configuration validation."""
        # Arrange
        resumes_dir = temp_dir / "output" / "resumes"
        templates_dir = temp_dir / "templates"
        resumes_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)
        
        # Act
        with patch('src.config.RESUMES_DIR', resumes_dir), \
             patch('src.config.TEMPLATES_DIR', templates_dir), \
             patch('src.config.LINKEDIN_EMAIL', 'test@example.com'), \
             patch('src.config.LINKEDIN_PASSWORD', 'testpass'):
            
            result = validate_config()
        
        # Assert
        assert result is True
```

### Integration Test Example

```python
import pytest
from unittest.mock import patch, Mock
from src.scraper import scrape_jobs_from_search

@pytest.mark.integration
class TestScraperIntegration:
    def test_scraper_initialization(self, mock_playwright, mock_playwright_browser):
        """Test scraper initialization with mocked Playwright."""
        with patch('src.scraper.sync_playwright', return_value=mock_playwright):
            # Test scraper initialization
            result = scrape_jobs_from_search(
                "https://linkedin.com/jobs/search/",
                "test@example.com",
                "testpass",
                max_jobs=1
            )
            assert result == []
```

## Test Coverage

### Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **Overall**: 85%+ coverage

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Generate XML coverage report (for CI)
pytest --cov=src --cov-report=xml

# Generate terminal coverage report
pytest --cov=src --cov-report=term-missing
```

Coverage reports are generated in the `htmlcov/` directory.

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python -m spacy download en_core_web_sm
    
    - name: Run unit tests
      run: |
        python run_tests.py unit --coverage-report
    
    - name: Run integration tests
      run: |
        python run_tests.py integration
      env:
        TESTING: true
        DEBUG: false
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Debugging Tests

### Running Specific Tests

```bash
# Run specific test method
pytest tests/unit/test_config.py::TestConfigValidation::test_validate_config_success

# Run tests matching pattern
pytest -k "test_config"

# Run tests with debugging
pytest --pdb

# Run tests with verbose output
pytest -v -s
```

### Test Debugging Tips

1. **Use `pytest --pdb`** to drop into debugger on failures
2. **Add `print()` statements** for debugging (remove before committing)
3. **Use `pytest -s`** to see print output
4. **Check test isolation** - ensure tests don't depend on each other
5. **Use temporary directories** for file operations
6. **Mock external dependencies** to avoid side effects

## Best Practices

### Test Organization

1. **One test class per module** being tested
2. **Descriptive test names** that explain what is being tested
3. **Arrange-Act-Assert** pattern for test structure
4. **Use fixtures** for common setup/teardown
5. **Mock external dependencies** in unit tests

### Test Data

1. **Use realistic test data** that matches production scenarios
2. **Create reusable fixtures** for common data
3. **Use temporary directories** for file operations
4. **Clean up after tests** to avoid side effects

### Error Testing

1. **Test both success and failure cases**
2. **Test edge cases** and boundary conditions
3. **Test error handling** and recovery mechanisms
4. **Use appropriate exception types** in tests

### Performance Testing

1. **Mark slow tests** with `@pytest.mark.slow`
2. **Use parallel execution** for independent tests
3. **Profile test execution** to identify bottlenecks
4. **Mock expensive operations** in unit tests

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `src/` is in Python path
2. **Missing dependencies**: Install all requirements
3. **Browser issues**: Install Playwright browsers
4. **API key issues**: Set test environment variables
5. **File permission issues**: Use temporary directories

### Test Failures

1. **Check test isolation** - ensure tests don't interfere
2. **Verify mock setup** - ensure mocks are configured correctly
3. **Check test data** - ensure test data is valid
4. **Review error messages** - look for specific failure reasons
5. **Run tests individually** to isolate issues

## Contributing

When adding new tests:

1. **Follow naming conventions** (`test_*.py`, `Test*` classes)
2. **Add appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Write descriptive docstrings** for test methods
4. **Use existing fixtures** when possible
5. **Update this guide** if adding new test categories or patterns
