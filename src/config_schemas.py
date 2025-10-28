# src/config_schemas.py

"""
Comprehensive type-safe configuration management using Pydantic.
This module defines all configuration schemas for the resume generator application.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings
import os
from datetime import datetime


class Address(BaseModel):
    """Address information schema."""
    street: str
    city: str
    state: str
    zip: str
    country: str = "USA"


class Education(BaseModel):
    """Education information schema."""
    degree: str
    institution: str
    location: str
    graduation_date: str
    
    @field_validator('graduation_date')
    @classmethod
    def validate_graduation_date(cls, v):
        """Validate graduation date format (MM-YYYY)."""
        if not isinstance(v, str):
            raise ValueError('Graduation date must be a string')
        # Check for MM-YYYY format
        import re
        if not re.match(r'^\d{2}-\d{4}$', v):
            raise ValueError('Graduation date must be in MM-YYYY format')
        return v


class JobHistory(BaseModel):
    """Job history entry schema."""
    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    responsibilities: List[str]
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v):
        """Validate end date - can be 'present' or MM-YYYY format."""
        if v.lower() == 'present':
            return v
        if len(v) < 4:
            raise ValueError('End date must be "present" or in MM-YYYY format')
        return v


class ReferenceContact(BaseModel):
    """Reference contact information schema."""
    email: str
    phone: str


class Reference(BaseModel):
    """Reference information schema."""
    name: str
    title: str
    contact: ReferenceContact


class PersonalInfo(BaseModel):
    """Complete personal information schema."""
    first_name: str
    last_name: str
    email: str
    phone: str
    address: Address
    linkedin: str
    github: Optional[str] = None
    job_history: List[JobHistory]
    education: List[Education]
    references: List[Reference]
    questions: Dict[str, str] = Field(default_factory=dict)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('linkedin')
    @classmethod
    def validate_linkedin(cls, v):
        """Validate LinkedIn URL."""
        if not v.startswith('https://www.linkedin.com/'):
            raise ValueError('LinkedIn URL must start with https://www.linkedin.com/')
        return v
    
    @field_validator('github')
    @classmethod
    def validate_github(cls, v):
        """Validate GitHub URL if provided."""
        if v and not v.startswith('https://github.com/'):
            raise ValueError('GitHub URL must start with https://github.com/')
        return v


class TimeoutConfig(BaseModel):
    """Timeout configuration schema."""
    page_load: int = Field(default=30000, ge=1000, le=300000)
    login: int = Field(default=30000, ge=1000, le=300000)
    search_page: int = Field(default=45000, ge=1000, le=300000)
    job_page: int = Field(default=30000, ge=1000, le=300000)
    job_title: int = Field(default=15000, ge=1000, le=300000)
    modal_wait: int = Field(default=20000, ge=1000, le=300000)
    easy_apply_click: int = Field(default=5000, ge=1000, le=300000)
    login_success: int = Field(default=5000, ge=1000, le=300000)
    job_list: int = Field(default=10000, ge=1000, le=300000)
    job_cards: int = Field(default=10000, ge=1000, le=300000)
    total_jobs: int = Field(default=5000, ge=1000, le=300000)
    dom_refresh: int = Field(default=3000, ge=1000, le=300000)
    radio_click: int = Field(default=3000, ge=1000, le=300000)


class RetryConfig(BaseModel):
    """Retry configuration schema."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    max_scroll_passes: int = Field(default=15, ge=1, le=50)
    max_steps: int = Field(default=10, ge=1, le=20)


class ScrollConfig(BaseModel):
    """Scroll configuration schema."""
    base_speed: int = Field(default=350, ge=50, le=1000)
    min_speed: int = Field(default=150, ge=50, le=500)
    max_speed: int = Field(default=500, ge=100, le=1000)
    pause_between: float = Field(default=1.0, ge=0.1, le=5.0)
    jitter_range: int = Field(default=20, ge=0, le=100)
    upward_scroll_frequency: int = Field(default=4, ge=1, le=10)
    upward_scroll_range: Tuple[int, int] = Field(default=(50, 150))


class DelayConfig(BaseModel):
    """Delay configuration schema."""
    login_processing: float = Field(default=3.0, ge=0.1, le=10.0)
    ui_stability: float = Field(default=0.2, ge=0.1, le=2.0)
    easy_apply_hover: float = Field(default=0.5, ge=0.1, le=2.0)
    easy_apply_click: Tuple[float, float] = Field(default=(0.4, 0.8))
    modal_wait: float = Field(default=1.2, ge=0.1, le=5.0)
    step_processing: float = Field(default=1.0, ge=0.1, le=5.0)
    dom_refresh: float = Field(default=3.0, ge=0.1, le=10.0)
    between_jobs: Tuple[float, float] = Field(default=(5.0, 10.0))
    rate_limit_wait: Tuple[float, float] = Field(default=(15.0, 25.0))
    graphql_failure_wait: Tuple[float, float] = Field(default=(12.0, 20.0))
    session_recovery_wait: Tuple[float, float] = Field(default=(3.0, 5.0))


class QuestionConfig(BaseModel):
    """Question answering configuration schema."""
    skip_questions: List[str] = Field(default_factory=lambda: [
        "email address", "phone country code", "mobile phone number",
        "first name", "last name", "city", "address"
    ])
    ignore_keywords: List[str] = Field(default_factory=lambda: [
        "phone", "email address", "country code"
    ])
    default_answers: Dict[str, str] = Field(default_factory=lambda: {
        "sponsorship": "No",
        "onsite_work": "Yes",
        "relocate": "Yes",
        "authorized_work": "Yes",
        "experience_years": "Yes",
        "background_check": "Yes",
        "convicted": "No",
        "default": "Yes"
    })


class LinkedInSelectors(BaseModel):
    """LinkedIn CSS selectors configuration schema."""
    login: Dict[str, str]
    login_fallbacks: List[str]
    login_success: List[str]
    job_search: Dict[str, str]
    job_detail: Dict[str, Union[str, List[str]]]
    easy_apply: Dict[str, Union[str, List[str]]]
    easy_apply_fallbacks: List[str]
    resume_upload: Dict[str, str]
    application_status: Dict[str, Union[str, List[str]]]
    form_fields: Dict[str, str]


class FilePaths(BaseModel):
    """File paths configuration schema."""
    personal_info: Path
    job_urls: Path
    stopwords: Path
    tech_dictionary: Path
    keyword_weights: Path
    resumes_dir: Path
    templates_dir: Path
    output_dir: Path
    
    @model_validator(mode='before')
    @classmethod
    def convert_to_path(cls, values):
        """Convert string paths to Path objects."""
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, str):
                    values[key] = Path(value)
        return values


class KeywordWeights(BaseModel):
    """Keyword weights configuration schema."""
    tech: List[str] = Field(default_factory=list)
    methodology: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class BrowserConfig(BaseModel):
    """Browser configuration schema."""
    headless: bool = Field(default=False)
    debug: bool = Field(default=False)
    enable_monitoring: bool = Field(default=False)
    suppress_warnings: bool = Field(default=True)
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    viewport_width: int = Field(default=1920, ge=800, le=3840)
    viewport_height: int = Field(default=1080, ge=600, le=2160)
    locale: str = Field(default="en-US")
    timezone: str = Field(default="America/New_York")


class AppSettings(BaseSettings):
    """Main application settings schema using Pydantic Settings."""
    
    # Base Configuration
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    debug: bool = Field(default=False)
    
    # LinkedIn Credentials
    linkedin_email: str = Field(..., description="LinkedIn email address")
    linkedin_password: str = Field(..., description="LinkedIn password")
    
    # Optional Links
    portfolio: Optional[str] = Field(default=None, description="Portfolio website URL")
    
    # Job Search Settings
    max_jobs: int = Field(default=15, ge=1, le=100, description="Maximum jobs to scrape")
    auto_apply: bool = Field(default=True, description="Enable LinkedIn Easy Apply automation")
    default_template: str = Field(default="base_resume.html", description="Default resume template")
    
    # Browser Configuration
    headless_mode: bool = Field(default=False, description="Run browser in headless mode")
    enable_browser_monitoring: bool = Field(default=False, description="Monitor browser connection")
    suppress_console_warnings: bool = Field(default=True, description="Suppress harmless browser warnings")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    llm_model: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for LLM responses")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore"  # Ignore extra environment variables
    )


class AppConfig(BaseModel):
    """Complete application configuration schema."""
    
    # Core settings
    settings: AppSettings
    
    # Personal information
    personal_info: PersonalInfo
    
    # Configuration objects
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    scroll_config: ScrollConfig = Field(default_factory=ScrollConfig)
    delays: DelayConfig = Field(default_factory=DelayConfig)
    question_config: QuestionConfig = Field(default_factory=QuestionConfig)
    linkedin_selectors: LinkedInSelectors
    file_paths: FilePaths
    keyword_weights: KeywordWeights = Field(default_factory=KeywordWeights)
    browser_config: BrowserConfig = Field(default_factory=BrowserConfig)
    
    @model_validator(mode='after')
    @classmethod
    def validate_configuration(cls, model):
        """Validate the complete configuration."""
        settings = model.settings
        file_paths = model.file_paths
        
        if not settings:
            raise ValueError("Settings are required")
        
        if not file_paths:
            raise ValueError("File paths are required")
        
        # Ensure directories exist
        for dir_name, dir_path in [
            ("resumes", file_paths.resumes_dir),
            ("templates", file_paths.templates_dir),
            ("output", file_paths.output_dir)
        ]:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"[INFO] Created {dir_name} directory: {dir_path}")
                except Exception as e:
                    raise ValueError(f"Cannot create {dir_name} directory {dir_path}: {e}")
        
        return model
    
    @classmethod
    def load_from_files(
        cls,
        personal_info_path: Optional[Path] = None,
        keyword_weights_path: Optional[Path] = None,
        linkedin_selectors_path: Optional[Path] = None,
        env_file: Optional[Path] = None
    ) -> "AppConfig":
        """
        Load configuration from files.
        
        Args:
            personal_info_path: Path to personal_info.yaml
            keyword_weights_path: Path to keyword_weights.json
            linkedin_selectors_path: Path to linkedin_selectors.json (optional)
            env_file: Path to .env file
            
        Returns:
            AppConfig: Complete configuration object
        """
        import yaml
        import json
        
        # Load settings from environment
        settings = AppSettings(_env_file=env_file)
        
        # Set default paths if not provided
        if personal_info_path is None:
            personal_info_path = settings.base_dir / "personal_info.yaml"
        if keyword_weights_path is None:
            keyword_weights_path = settings.base_dir / "src" / "keyword_weights.json"
        
        # Load personal information
        try:
            with open(personal_info_path, 'r', encoding='utf-8') as f:
                personal_data = yaml.safe_load(f)
            personal_info = PersonalInfo(**personal_data)
        except Exception as e:
            raise ValueError(f"Failed to load personal info from {personal_info_path}: {e}")
        
        # Load keyword weights
        try:
            with open(keyword_weights_path, 'r', encoding='utf-8') as f:
                keyword_data = json.load(f)
            keyword_weights = KeywordWeights(**keyword_data)
        except Exception as e:
            print(f"[WARNING] Failed to load keyword weights from {keyword_weights_path}: {e}")
            keyword_weights = KeywordWeights()
        
        # Load LinkedIn selectors (from config.py)
        linkedin_selectors = cls._load_linkedin_selectors()
        
        # Create file paths
        file_paths = FilePaths(
            personal_info=personal_info_path,
            job_urls=settings.base_dir / "job_urls.json",
            stopwords=settings.base_dir / "src" / "stopwords.json",
            tech_dictionary=settings.base_dir / "src" / "tech_dictionary.json",
            keyword_weights=keyword_weights_path,
            resumes_dir=settings.base_dir / "output" / "resumes",
            templates_dir=settings.base_dir / "templates",
            output_dir=settings.base_dir / "output"
        )
        
        return cls(
            settings=settings,
            personal_info=personal_info,
            linkedin_selectors=linkedin_selectors,
            file_paths=file_paths,
            keyword_weights=keyword_weights
        )
    
    @staticmethod
    def _load_linkedin_selectors() -> LinkedInSelectors:
        """Load LinkedIn selectors from the existing config.py structure."""
        # This would typically load from a JSON file, but for now we'll use the existing structure
        # In a real implementation, you might want to move these to a separate JSON file
        selectors_data = {
            "login": {
                "username": 'input[id="username"]',
                "password": 'input[id="password"]',
                "submit": 'button[type="submit"]',
            },
            "login_fallbacks": [
                'input[name="session_key"]',
                'input[name="session_password"]',
                'input[type="email"]',
                'input[type="password"]',
                'button:has-text("Sign in")',
                'button:has-text("Log in")'
            ],
            "login_success": [
                'nav[aria-label="Primary"]',
                'div[data-test-id="feed-identity-module"]',
                '.feed-shared-update-v2',
                '.global-nav',
                'main[role="main"]',
                '.application-outlet'
            ],
            "job_search": {
                "job_list": "div.scaffold-layout__list.jobs-semantic-search-list",
                "total_jobs": "div.t-black--light.pv4.text-body-small.mr2",
                "job_cards": "ul.semantic-search-results-list > li",
                "job_wrapper": "div.job-card-job-posting-card-wrapper, div.base-card",
            },
            "job_detail": {
                "title": [
                    'h1.t-24.t-bold.inline',
                    'h1.jobs-unified-top-card__job-title',
                    'h1.top-card-layout__title'
                ],
                "company": [
                    'div.job-details-jobs-unified-top-card__company-name a',
                    'a.topcard__org-name-link'
                ],
                "location": 'span.tvm__text.tvm__text--low-emphasis',
                "description": [
                    'div.jobs-description__content',
                    'div.jobs-description-content__text',
                    'div.jobs-box__html-content',
                    'div.jobs-unified-top-card__job-description',
                    'div.jobs-details__main-content',
                    'div[data-test-id="job-description"]',
                    'div.jobs-box__html-content div',
                    'div.jobs-description div',
                    'div.jobs-unified-top-card__content--main div',
                    'div.jobs-details__main-content div'
                ],
                "unavailable": "div.jobs-unavailable",
            },
            "easy_apply": {
                "button": [
                    'div.jobs-apply-button--top-card button.jobs-apply-button',
                    'button[data-test-id="apply-button"]',
                    'button:has-text("Easy Apply")',
                    'button:has-text("Apply")',
                    'button[aria-label*="Apply"]',
                    'div.jobs-apply-button button',
                    'button.jobs-apply-button'
                ],
                "modal": [
                    'div.jobs-easy-apply-modal[role="dialog"]',
                    'div.artdeco-modal.jobs-easy-apply-modal',
                    'div[role="dialog"]',
                    'div.artdeco-modal',
                    'div.jobs-easy-apply-modal'
                ],
                "submit": [
                    'button[aria-label="Submit application"]',
                    'button:has-text("Submit application")',
                    'button:has-text("Submit")',
                    'button[data-test-id="submit-button"]'
                ],
                "review": [
                    'button[aria-label="Review your application"]',
                    'button:has-text("Review your application")',
                    'button:has-text("Review")',
                    'button[data-test-id="review-button"]'
                ],
                "next": [
                    'button[aria-label="Continue to next step"]',
                    'button:has-text("Continue to next step")',
                    'button:has-text("Next")',
                    'button:has-text("Continue")',
                    'button[data-test-id="next-button"]'
                ],
                "follow_checkbox": [
                    "input#follow-company-checkbox",
                    "input[name='follow-company']",
                    "input[type='checkbox'][id*='follow']"
                ],
                "follow_label": [
                    "label[for='follow-company-checkbox']",
                    "label[for*='follow']"
                ],
                "dismiss": [
                    'button[aria-label="Dismiss"]',
                    'button:has-text("Dismiss")',
                    'button:has-text("Close")',
                    'button[data-test-id="dismiss-button"]'
                ],
            },
            "easy_apply_fallbacks": [
                'button:has-text("Easy Apply")',
                'button:has-text("Apply")',
                'button[aria-label*="Apply"]',
                'button[data-test-id*="apply"]',
                'div[role="dialog"]',
                'div.artdeco-modal',
                'button:has-text("Submit")',
                'button:has-text("Next")',
                'button:has-text("Continue")'
            ],
            "resume_upload": {
                "upload_button": 'label.jobs-document-upload__upload-button',
                "file_input": "div.js-jobs-document-upload__container input[type='file'][id*='upload-resume']",
            },
            "application_status": {
                "applied_banner": "div.post-apply-timeline__content",
                "applied_text": "Application submitted",
                "no_longer_accepting": [
                    "div:has-text('No longer accepting applications')",
                    "span:has-text('No longer accepting applications')",
                    "p:has-text('No longer accepting applications')",
                    "[data-test-id*='no-longer-accepting']",
                    ".jobs-apply-button--disabled:has-text('No longer accepting')"
                ],
                "confirmation": [
                    'div.jobs-apply-confirmation',
                    'div.post-apply-timeline__content',
                    'a[aria-label="Download your submitted resume"]',
                    'button.jobs-apply-button[aria-label*="Applied"]'
                ]
            },
            "form_fields": {
                "radio_fieldset": "fieldset[data-test-form-builder-radio-button-form-component='true']",
                "radio_input": "input[type='radio']",
                "dropdown": "select.fb-dash-form-element__select-dropdown",
                "dropdown_label": "xpath=preceding-sibling::label[1]",
            }
        }
        
        return LinkedInSelectors(**selectors_data)
    
    def save_personal_info(self, path: Optional[Path] = None) -> None:
        """Save personal information to YAML file."""
        import yaml
        
        if path is None:
            path = self.file_paths.personal_info
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.personal_info.dict(), f, default_flow_style=False, allow_unicode=True)
    
    def save_keyword_weights(self, path: Optional[Path] = None) -> None:
        """Save keyword weights to JSON file."""
        import json
        
        if path is None:
            path = self.file_paths.keyword_weights
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.keyword_weights.dict(), f, indent=2)
    
    def validate_linkedin_credentials(self) -> bool:
        """Validate that LinkedIn credentials are present."""
        return bool(self.settings.linkedin_email and self.settings.linkedin_password)
    
    def get_resume_template_path(self) -> Path:
        """Get the path to the resume template."""
        return self.file_paths.templates_dir / self.settings.default_template
    
    def get_output_resume_path(self, job_title: str, company: str) -> Path:
        """Generate output resume path for a specific job."""
        import re
        
        # Sanitize job title and company for filename
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '', job_title.replace(" ", "_"))
        safe_company = re.sub(r'[^a-zA-Z0-9_-]', '', company.replace(" ", "_"))
        
        filename = f"{safe_title}_{safe_company}_resume.pdf"
        return self.file_paths.resumes_dir / filename
