from dotenv import load_dotenv
import os
import yaml
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# ===== Base Configuration =====
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
RESUMES_DIR = OUTPUT_DIR / "resumes"
TEMPLATES_DIR = BASE_DIR / "templates"

# ===== Login Info =====
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# ===== Optional Links =====
PORTFOLIO = os.getenv("PORTFOLIO", None)

# ===== Job Search Settings =====
MAX_JOBS = int(os.getenv("MAX_JOBS", "15"))  # Default max jobs to scrape
AUTO_APPLY = os.getenv("AUTO_APPLY", "true").lower() == "true"  # LinkedIn Easy Apply automation
DEFAULT_TEMPLATE = os.getenv("DEFAULT_TEMPLATE", "base_resume.html")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"  # Debug mode

# ===== Timeout Configuration =====
TIMEOUTS = {
    "page_load": int(os.getenv("TIMEOUT_PAGE_LOAD", "30000")),
    "login": int(os.getenv("TIMEOUT_LOGIN", "30000")),
    "search_page": int(os.getenv("TIMEOUT_SEARCH_PAGE", "45000")),
    "job_page": int(os.getenv("TIMEOUT_JOB_PAGE", "30000")),
    "job_title": int(os.getenv("TIMEOUT_JOB_TITLE", "15000")),
    "modal_wait": int(os.getenv("TIMEOUT_MODAL_WAIT", "20000")),
    "easy_apply_click": int(os.getenv("TIMEOUT_EASY_APPLY_CLICK", "5000")),
    "login_success": int(os.getenv("TIMEOUT_LOGIN_SUCCESS", "5000")),
    "job_list": int(os.getenv("TIMEOUT_JOB_LIST", "10000")),
    "job_cards": int(os.getenv("TIMEOUT_JOB_CARDS", "10000")),
    "total_jobs": int(os.getenv("TIMEOUT_TOTAL_JOBS", "5000")),
    "dom_refresh": int(os.getenv("TIMEOUT_DOM_REFRESH", "3000")),
    "radio_click": int(os.getenv("TIMEOUT_RADIO_CLICK", "3000")),
}

# ===== Retry Configuration =====
RETRY_CONFIG = {
    "max_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
    "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
    "max_scroll_passes": int(os.getenv("MAX_SCROLL_PASSES", "15")),
    "max_steps": int(os.getenv("MAX_EASY_APPLY_STEPS", "10")),
}

# ===== LinkedIn Selectors =====
LINKEDIN_SELECTORS = {
    # Login page selectors
    "login": {
        "username": 'input[id="username"]',
        "password": 'input[id="password"]',
        "submit": 'button[type="submit"]',
    },
    
    # Login success detection
    "login_success": [
        'nav[aria-label="Primary"]',
        'div[data-test-id="feed-identity-module"]',
        '.feed-shared-update-v2',
        '.global-nav',
        'main[role="main"]',
        '.application-outlet'
    ],
    
    # Job search page selectors
    "job_search": {
        "job_list": "div.scaffold-layout__list.jobs-semantic-search-list",
        "total_jobs": "div.t-black--light.pv4.text-body-small.mr2",
        "job_cards": "ul.semantic-search-results-list > li",
        "job_wrapper": "div.job-card-job-posting-card-wrapper, div.base-card",
    },
    
    # Job detail page selectors
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
        "description": 'div.jobs-description__content',
        "unavailable": "div.jobs-unavailable",
    },
    
    # Easy Apply selectors
    "easy_apply": {
        "button": 'div.jobs-apply-button--top-card button.jobs-apply-button',
        "modal": 'div.jobs-easy-apply-modal[role="dialog"], div.artdeco-modal.jobs-easy-apply-modal',
        "submit": 'button[aria-label="Submit application"]',
        "review": 'button[aria-label="Review your application"]',
        "next": 'button[aria-label="Continue to next step"]',
        "follow_checkbox": "input#follow-company-checkbox",
        "follow_label": "label[for='follow-company-checkbox']",
        "dismiss": 'button[aria-label="Dismiss"]',
    },
    
    # Resume upload selectors
    "resume_upload": {
        "upload_button": 'label.jobs-document-upload__upload-button',
        "file_input": "div.js-jobs-document-upload__container input[type='file'][id*='upload-resume']",
    },
    
    # Application status selectors
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
    
    # Form field selectors
    "form_fields": {
        "radio_fieldset": "fieldset[data-test-form-builder-radio-button-form-component='true']",
        "radio_input": "input[type='radio']",
        "dropdown": "select.fb-dash-form-element__select-dropdown",
        "dropdown_label": "xpath=preceding-sibling::label[1]",
    }
}

# ===== File Paths =====
FILE_PATHS = {
    "personal_info": BASE_DIR / "personal_info.yaml",
    "job_urls": BASE_DIR / "job_urls.json",
    "stopwords": BASE_DIR / "src" / "stopwords.json",
    "tech_dictionary": BASE_DIR / "src" / "tech_dictionary.json",
    "keyword_weights": BASE_DIR / "src" / "keyword_weights.json",
    "resumes_dir": RESUMES_DIR,
    "templates_dir": TEMPLATES_DIR,
    "output_dir": OUTPUT_DIR,
}

# ===== Scroll Configuration =====
SCROLL_CONFIG = {
    "base_speed": int(os.getenv("SCROLL_BASE_SPEED", "350")),
    "min_speed": int(os.getenv("SCROLL_MIN_SPEED", "150")),
    "max_speed": int(os.getenv("SCROLL_MAX_SPEED", "500")),
    "pause_between": float(os.getenv("SCROLL_PAUSE_BETWEEN", "1.0")),
    "jitter_range": int(os.getenv("SCROLL_JITTER_RANGE", "20")),
    "upward_scroll_frequency": int(os.getenv("SCROLL_UPWARD_FREQUENCY", "4")),
    "upward_scroll_range": (50, 150),
}

# ===== Question Answering Configuration =====
QUESTION_CONFIG = {
    "skip_questions": [
        "email address",
        "phone country code",
        "mobile phone number",
        "first name",
        "last name",
        "city",
        "address"
    ],
    "ignore_keywords": ["phone", "email address", "country code"],
    "default_answers": {
        "sponsorship": "No",
        "onsite_work": "Yes",
        "relocate": "Yes",
        "authorized_work": "Yes",
        "experience_years": "Yes",
        "background_check": "Yes",
        "convicted": "No",
        "default": "Yes"
    }
}

# ===== Delay Configuration =====
DELAYS = {
    "login_processing": float(os.getenv("DELAY_LOGIN_PROCESSING", "3.0")),
    "ui_stability": float(os.getenv("DELAY_UI_STABILITY", "0.2")),
    "easy_apply_hover": float(os.getenv("DELAY_EASY_APPLY_HOVER", "0.5")),
    "easy_apply_click": (0.4, 0.8),  # Random range
    "modal_wait": float(os.getenv("DELAY_MODAL_WAIT", "1.2")),
    "step_processing": float(os.getenv("DELAY_STEP_PROCESSING", "1.0")),
    "dom_refresh": float(os.getenv("DELAY_DOM_REFRESH", "3.0")),
}

# ===== Validation =====
def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not LINKEDIN_EMAIL:
        errors.append("LINKEDIN_EMAIL is required")
    if not LINKEDIN_PASSWORD:
        errors.append("LINKEDIN_PASSWORD is required")
    
    # Ensure directories exist
    for dir_name, dir_path in [("resumes", RESUMES_DIR), ("templates", TEMPLATES_DIR)]:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[INFO] Created {dir_name} directory: {dir_path}")
            except Exception as e:
                errors.append(f"Cannot create {dir_name} directory {dir_path}: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))
    
    return True

# Validate configuration on import
validate_config()
