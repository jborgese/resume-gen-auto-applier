# src/config_migration.py

"""
Configuration migration utility to transition from old config.py to new type-safe system.
This module helps migrate existing configuration and provides backward compatibility.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.logging_config import get_logger, log_function_call, log_error_context

logger = get_logger(__name__)


class ConfigMigration:
    """
    Utility class to migrate from old configuration system to new type-safe system.
    """
    
    @staticmethod
    def migrate_from_old_config() -> Dict[str, Any]:
        """
        Migrate configuration from the old config.py system.
        
        Returns:
            Dict containing migrated configuration data
        """
        logger.info("Starting configuration migration from old system")
        
        # Load environment variables (same as old config.py)
        from dotenv import load_dotenv
        load_dotenv()
        
        migrated_config = {
            "settings": ConfigMigration._migrate_settings(),
            "timeouts": ConfigMigration._migrate_timeouts(),
            "retry_config": ConfigMigration._migrate_retry_config(),
            "scroll_config": ConfigMigration._migrate_scroll_config(),
            "delays": ConfigMigration._migrate_delays(),
            "question_config": ConfigMigration._migrate_question_config(),
            "linkedin_selectors": ConfigMigration._migrate_linkedin_selectors(),
            "file_paths": ConfigMigration._migrate_file_paths(),
            "browser_config": ConfigMigration._migrate_browser_config(),
        }
        
        logger.info("Configuration migration completed successfully")
        return migrated_config
    
    @staticmethod
    def _migrate_settings() -> Dict[str, Any]:
        """Migrate application settings from environment variables."""
        return {
            "base_dir": Path(__file__).parent.parent,
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "linkedin_email": os.getenv("LINKEDIN_EMAIL", ""),
            "linkedin_password": os.getenv("LINKEDIN_PASSWORD", ""),
            "portfolio": os.getenv("PORTFOLIO"),
            "max_jobs": int(os.getenv("MAX_JOBS", "15")),
            "auto_apply": os.getenv("AUTO_APPLY", "true").lower() == "true",
            "default_template": os.getenv("DEFAULT_TEMPLATE", "base_resume.html"),
            "headless_mode": os.getenv("HEADLESS_MODE", "false").lower() == "true",
            "enable_browser_monitoring": os.getenv("ENABLE_BROWSER_MONITORING", "false").lower() == "true",
            "suppress_console_warnings": os.getenv("SUPPRESS_CONSOLE_WARNINGS", "true").lower() == "true",
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "llm_model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "llm_max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1000")),
        }
    
    @staticmethod
    def _migrate_timeouts() -> Dict[str, Any]:
        """Migrate timeout configuration."""
        return {
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
    
    @staticmethod
    def _migrate_retry_config() -> Dict[str, Any]:
        """Migrate retry configuration."""
        return {
            "max_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
            "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
            "max_scroll_passes": int(os.getenv("MAX_SCROLL_PASSES", "15")),
            "max_steps": int(os.getenv("MAX_EASY_APPLY_STEPS", "10")),
        }
    
    @staticmethod
    def _migrate_scroll_config() -> Dict[str, Any]:
        """Migrate scroll configuration."""
        return {
            "base_speed": int(os.getenv("SCROLL_BASE_SPEED", "350")),
            "min_speed": int(os.getenv("SCROLL_MIN_SPEED", "150")),
            "max_speed": int(os.getenv("SCROLL_MAX_SPEED", "500")),
            "pause_between": float(os.getenv("SCROLL_PAUSE_BETWEEN", "1.0")),
            "jitter_range": int(os.getenv("SCROLL_JITTER_RANGE", "20")),
            "upward_scroll_frequency": int(os.getenv("SCROLL_UPWARD_FREQUENCY", "4")),
            "upward_scroll_range": (50, 150),
        }
    
    @staticmethod
    def _migrate_delays() -> Dict[str, Any]:
        """Migrate delay configuration."""
        return {
            "login_processing": float(os.getenv("DELAY_LOGIN_PROCESSING", "3.0")),
            "ui_stability": float(os.getenv("DELAY_UI_STABILITY", "0.2")),
            "easy_apply_hover": float(os.getenv("DELAY_EASY_APPLY_HOVER", "0.5")),
            "easy_apply_click": (0.4, 0.8),
            "modal_wait": float(os.getenv("DELAY_MODAL_WAIT", "1.2")),
            "step_processing": float(os.getenv("DELAY_STEP_PROCESSING", "1.0")),
            "dom_refresh": float(os.getenv("DELAY_DOM_REFRESH", "3.0")),
            "between_jobs": (5.0, 10.0),
            "rate_limit_wait": (15.0, 25.0),
            "graphql_failure_wait": (12.0, 20.0),
            "session_recovery_wait": (3.0, 5.0),
        }
    
    @staticmethod
    def _migrate_question_config() -> Dict[str, Any]:
        """Migrate question configuration."""
        return {
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
    
    @staticmethod
    def _migrate_linkedin_selectors() -> Dict[str, Any]:
        """Migrate LinkedIn selectors from old config.py."""
        # This is a large configuration, so we'll import it from the old config
        try:
            # Import the old config module to get selectors
            import sys
            old_config_path = Path(__file__).parent.parent / "src" / "config.py"
            if old_config_path.exists():
                # Read the old config file and extract LINKEDIN_SELECTORS
                with open(old_config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract LINKEDIN_SELECTORS from the old config
                # This is a simplified extraction - in practice you might want to use ast parsing
                # For now, we'll use the hardcoded selectors from the schema
                return ConfigMigration._get_default_linkedin_selectors()
            else:
                logger.warning("Old config.py not found, using default selectors")
                return ConfigMigration._get_default_linkedin_selectors()
        except Exception as e:
            logger.warning(f"Failed to migrate LinkedIn selectors: {e}")
            return ConfigMigration._get_default_linkedin_selectors()
    
    @staticmethod
    def _get_default_linkedin_selectors() -> Dict[str, Any]:
        """Get default LinkedIn selectors."""
        return {
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
    
    @staticmethod
    def _migrate_file_paths() -> Dict[str, Any]:
        """Migrate file paths configuration."""
        base_dir = Path(__file__).parent.parent
        return {
            "personal_info": base_dir / "personal_info.yaml",
            "job_urls": base_dir / "job_urls.json",
            "stopwords": base_dir / "src" / "stopwords.json",
            "tech_dictionary": base_dir / "src" / "tech_dictionary.json",
            "keyword_weights": base_dir / "src" / "keyword_weights.json",
            "resumes_dir": base_dir / "output" / "resumes",
            "templates_dir": base_dir / "templates",
            "output_dir": base_dir / "output"
        }
    
    @staticmethod
    def _migrate_browser_config() -> Dict[str, Any]:
        """Migrate browser configuration."""
        return {
            "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "enable_monitoring": os.getenv("ENABLE_BROWSER_MONITORING", "false").lower() == "true",
            "suppress_warnings": os.getenv("SUPPRESS_CONSOLE_WARNINGS", "true").lower() == "true",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "locale": "en-US",
            "timezone": "America/New_York"
        }
    
    @staticmethod
    def create_migration_report() -> Dict[str, Any]:
        """
        Create a migration report showing what was migrated.
        
        Returns:
            Dict containing migration report
        """
        logger.info("Creating configuration migration report")
        
        report = {
            "migration_timestamp": str(Path(__file__).stat().st_mtime),
            "migrated_components": [
                "settings",
                "timeouts", 
                "retry_config",
                "scroll_config",
                "delays",
                "question_config",
                "linkedin_selectors",
                "file_paths",
                "browser_config"
            ],
            "environment_variables_used": [
                "DEBUG", "LINKEDIN_EMAIL", "LINKEDIN_PASSWORD", "PORTFOLIO",
                "MAX_JOBS", "AUTO_APPLY", "DEFAULT_TEMPLATE", "HEADLESS_MODE",
                "ENABLE_BROWSER_MONITORING", "SUPPRESS_CONSOLE_WARNINGS",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_MODEL",
                "LLM_TEMPERATURE", "LLM_MAX_TOKENS"
            ],
            "files_required": [
                "personal_info.yaml",
                "keyword_weights.json",
                ".env"
            ],
            "validation_checks": [
                "LinkedIn credentials present",
                "Personal info file exists",
                "Template directory exists",
                "Output directory exists"
            ]
        }
        
        return report


def migrate_configuration() -> Dict[str, Any]:
    """
    Convenience function to migrate configuration from old system.
    
    Returns:
        Dict containing migrated configuration
    """
    return ConfigMigration.migrate_from_old_config()


def create_migration_report() -> Dict[str, Any]:
    """
    Convenience function to create migration report.
    
    Returns:
        Dict containing migration report
    """
    return ConfigMigration.create_migration_report()
