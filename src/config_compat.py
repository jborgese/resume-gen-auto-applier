# src/config_compat.py

"""
Backward compatibility layer for the old config.py system.
This module provides the same interface as the old config.py but uses the new type-safe system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .config_manager import get_config_manager, ConfigManager
from .config_schemas import AppConfig

logger = logging.getLogger(__name__)

# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def _get_config_manager() -> ConfigManager:
    """Get or initialize the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = get_config_manager()
    return _config_manager


# ===== Backward Compatibility Constants =====
# These provide the same interface as the old config.py

def _get_base_dir() -> Path:
    """Get base directory."""
    return _get_config_manager().settings.base_dir


def _get_output_dir() -> Path:
    """Get output directory."""
    return _get_config_manager().file_paths.output_dir


def _get_resumes_dir() -> Path:
    """Get resumes directory."""
    return _get_config_manager().file_paths.resumes_dir


def _get_templates_dir() -> Path:
    """Get templates directory."""
    return _get_config_manager().file_paths.templates_dir


# Base Configuration (same as old config.py) - Lazy loading
def _get_base_dir() -> Path:
    """Get base directory."""
    return _get_config_manager().settings.base_dir


def _get_output_dir() -> Path:
    """Get output directory."""
    return _get_config_manager().file_paths.output_dir


def _get_resumes_dir() -> Path:
    """Get resumes directory."""
    return _get_config_manager().file_paths.resumes_dir


def _get_templates_dir() -> Path:
    """Get templates directory."""
    return _get_config_manager().file_paths.templates_dir


# Login Info
def _get_linkedin_email() -> str:
    """Get LinkedIn email."""
    return _get_config_manager().linkedin_email


def _get_linkedin_password() -> str:
    """Get LinkedIn password."""
    return _get_config_manager().linkedin_password


# Optional Links
def _get_portfolio() -> Optional[str]:
    """Get portfolio URL."""
    return _get_config_manager().settings.portfolio


# Job Search Settings
def _get_max_jobs() -> int:
    """Get maximum jobs to scrape."""
    return _get_config_manager().max_jobs


def _get_auto_apply() -> bool:
    """Get auto-apply setting."""
    return _get_config_manager().auto_apply


def _get_default_template() -> str:
    """Get default template."""
    return _get_config_manager().settings.default_template


def _get_debug() -> bool:
    """Get debug mode."""
    return _get_config_manager().debug


# Browser Configuration
def _get_headless_mode() -> bool:
    """Get headless mode."""
    return _get_config_manager().headless_mode


def _get_enable_browser_monitoring() -> bool:
    """Get browser monitoring setting."""
    return _get_config_manager().settings.enable_browser_monitoring


def _get_suppress_console_warnings() -> bool:
    """Get suppress console warnings setting."""
    return _get_config_manager().settings.suppress_console_warnings


# Timeout Configuration
def _get_timeouts() -> Dict[str, int]:
    """Get timeout configuration."""
    return _get_config_manager().timeouts.dict()


# Retry Configuration
def _get_retry_config() -> Dict[str, Any]:
    """Get retry configuration."""
    return _get_config_manager().retry_config.dict()


# LinkedIn Selectors
def _get_linkedin_selectors() -> Dict[str, Any]:
    """Get LinkedIn selectors."""
    return _get_config_manager().linkedin_selectors.dict()


# File Paths
def _get_file_paths() -> Dict[str, Path]:
    """Get file paths."""
    return _get_config_manager().file_paths.dict()


# Scroll Configuration
def _get_scroll_config() -> Dict[str, Any]:
    """Get scroll configuration."""
    return _get_config_manager().scroll_config.dict()


# Question Answering Configuration
def _get_question_config() -> Dict[str, Any]:
    """Get question configuration."""
    return _get_config_manager().question_config.dict()


# Delay Configuration
def _get_delays() -> Dict[str, Any]:
    """Get delay configuration."""
    return _get_config_manager().delays.dict()


# Lazy-loaded constants (same interface as old config.py)
class LazyConfig:
    """Lazy-loaded configuration constants."""
    
    @property
    def BASE_DIR(self) -> Path:
        return _get_base_dir()
    
    @property
    def OUTPUT_DIR(self) -> Path:
        return _get_output_dir()
    
    @property
    def RESUMES_DIR(self) -> Path:
        return _get_resumes_dir()
    
    @property
    def TEMPLATES_DIR(self) -> Path:
        return _get_templates_dir()
    
    @property
    def LINKEDIN_EMAIL(self) -> str:
        return _get_linkedin_email()
    
    @property
    def LINKEDIN_PASSWORD(self) -> str:
        return _get_linkedin_password()
    
    @property
    def PORTFOLIO(self) -> Optional[str]:
        return _get_portfolio()
    
    @property
    def MAX_JOBS(self) -> int:
        return _get_max_jobs()
    
    @property
    def AUTO_APPLY(self) -> bool:
        return _get_auto_apply()
    
    @property
    def DEFAULT_TEMPLATE(self) -> str:
        return _get_default_template()
    
    @property
    def DEBUG(self) -> bool:
        return _get_debug()
    
    @property
    def HEADLESS_MODE(self) -> bool:
        return _get_headless_mode()
    
    @property
    def ENABLE_BROWSER_MONITORING(self) -> bool:
        return _get_enable_browser_monitoring()
    
    @property
    def SUPPRESS_CONSOLE_WARNINGS(self) -> bool:
        return _get_suppress_console_warnings()
    
    @property
    def TIMEOUTS(self) -> Dict[str, int]:
        return _get_timeouts()
    
    @property
    def RETRY_CONFIG(self) -> Dict[str, Any]:
        return _get_retry_config()
    
    @property
    def LINKEDIN_SELECTORS(self) -> Dict[str, Any]:
        return _get_linkedin_selectors()
    
    @property
    def FILE_PATHS(self) -> Dict[str, Path]:
        return _get_file_paths()
    
    @property
    def SCROLL_CONFIG(self) -> Dict[str, Any]:
        return _get_scroll_config()
    
    @property
    def QUESTION_CONFIG(self) -> Dict[str, Any]:
        return _get_question_config()
    
    @property
    def DELAYS(self) -> Dict[str, Any]:
        return _get_delays()


# Create lazy config instance
_lazy_config = LazyConfig()

# Export constants for backward compatibility (lazy access)
class LazyConstant:
    """Lazy constant that only loads when accessed."""
    def __init__(self, getter_func):
        self._getter_func = getter_func
        self._value = None
        self._loaded = False
    
    def __getattr__(self, name):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}")
                # Return default values for backward compatibility
                if 'BASE_DIR' in str(self._getter_func):
                    self._value = Path(__file__).parent.parent
                elif 'MAX_JOBS' in str(self._getter_func):
                    self._value = 15
                elif 'DEBUG' in str(self._getter_func):
                    self._value = False
                elif 'AUTO_APPLY' in str(self._getter_func):
                    self._value = True
                elif 'HEADLESS_MODE' in str(self._getter_func):
                    self._value = False
                elif 'LINKEDIN_EMAIL' in str(self._getter_func):
                    self._value = ""
                elif 'LINKEDIN_PASSWORD' in str(self._getter_func):
                    self._value = ""
                else:
                    self._value = None
                self._loaded = True
        return getattr(self._value, name)
    
    def __str__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = ""
                self._loaded = True
        return str(self._value)
    
    def __bool__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = False
                self._loaded = True
        return bool(self._value)
    
    def __int__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = 0
                self._loaded = True
        return int(self._value)
    
    def __float__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = 0.0
                self._loaded = True
        return float(self._value)
    
    def __len__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return len(self._value)
    
    def __getitem__(self, key):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return self._value[key]
    
    def __iter__(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return iter(self._value)
    
    def keys(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return self._value.keys()
    
    def values(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return self._value.values()
    
    def items(self):
        if not self._loaded:
            try:
                self._value = self._getter_func()
                self._loaded = True
            except Exception:
                self._value = {}
                self._loaded = True
        return self._value.items()

# Create lazy constants
BASE_DIR = LazyConstant(_get_base_dir)
OUTPUT_DIR = LazyConstant(_get_output_dir)
RESUMES_DIR = LazyConstant(_get_resumes_dir)
TEMPLATES_DIR = LazyConstant(_get_templates_dir)
LINKEDIN_EMAIL = LazyConstant(_get_linkedin_email)
LINKEDIN_PASSWORD = LazyConstant(_get_linkedin_password)
PORTFOLIO = LazyConstant(_get_portfolio)
MAX_JOBS = LazyConstant(_get_max_jobs)
AUTO_APPLY = LazyConstant(_get_auto_apply)
DEFAULT_TEMPLATE = LazyConstant(_get_default_template)
DEBUG = LazyConstant(_get_debug)
HEADLESS_MODE = LazyConstant(_get_headless_mode)
ENABLE_BROWSER_MONITORING = LazyConstant(_get_enable_browser_monitoring)
SUPPRESS_CONSOLE_WARNINGS = LazyConstant(_get_suppress_console_warnings)
TIMEOUTS = LazyConstant(_get_timeouts)
RETRY_CONFIG = LazyConstant(_get_retry_config)
LINKEDIN_SELECTORS = LazyConstant(_get_linkedin_selectors)
FILE_PATHS = LazyConstant(_get_file_paths)
SCROLL_CONFIG = LazyConstant(_get_scroll_config)
QUESTION_CONFIG = LazyConstant(_get_question_config)
DELAYS = LazyConstant(_get_delays)


# ===== Backward Compatibility Functions =====

def validate_config() -> bool:
    """
    Validate that all required configuration is present.
    Same interface as old config.py validate_config().
    """
    try:
        config_manager = _get_config_manager()
        
        # Validate LinkedIn credentials
        if not config_manager.validate_credentials():
            logger.error("LinkedIn credentials are missing")
            return False
        
        # Validate file paths exist
        file_paths = config_manager.file_paths
        
        # Check if personal info file exists
        if not file_paths.personal_info.exists():
            logger.error(f"Personal info file not found: {file_paths.personal_info}")
            return False
        
        # Check if template file exists
        template_path = config_manager.get_resume_template_path()
        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            return False
        
        logger.info("Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def get_personal_info() -> Dict[str, Any]:
    """
    Get personal information as a dictionary.
    Same interface as loading from personal_info.yaml.
    """
    try:
        config_manager = _get_config_manager()
        return config_manager.personal_info.dict()
    except Exception as e:
        logger.error(f"Failed to get personal info: {e}")
        return {}


def get_keyword_weights() -> Dict[str, Any]:
    """
    Get keyword weights as a dictionary.
    Same interface as loading from keyword_weights.json.
    """
    try:
        config_manager = _get_config_manager()
        return config_manager.keyword_weights.dict()
    except Exception as e:
        logger.error(f"Failed to get keyword weights: {e}")
        return {"tech": [], "methodology": [], "soft": []}


def get_stopwords() -> set:
    """
    Get stopwords as a set.
    Same interface as loading from stopwords.json.
    """
    try:
        stopwords_path = _get_config_manager().file_paths.stopwords
        if stopwords_path.exists():
            import json
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        else:
            logger.warning(f"Stopwords file not found: {stopwords_path}")
            return set()
    except Exception as e:
        logger.error(f"Failed to get stopwords: {e}")
        return set()


def get_tech_dictionary() -> Dict[str, Any]:
    """
    Get tech dictionary as a dictionary.
    Same interface as loading from tech_dictionary.json.
    """
    try:
        tech_dict_path = _get_config_manager().file_paths.tech_dictionary
        if tech_dict_path.exists():
            import json
            with open(tech_dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Tech dictionary file not found: {tech_dict_path}")
            return {}
    except Exception as e:
        logger.error(f"Failed to get tech dictionary: {e}")
        return {}


# ===== Configuration Update Functions =====

def update_personal_info(**kwargs) -> None:
    """
    Update personal information.
    
    Args:
        **kwargs: Fields to update in personal information
    """
    try:
        config_manager = _get_config_manager()
        config_manager.update_personal_info(**kwargs)
        logger.info("Personal information updated successfully")
    except Exception as e:
        logger.error(f"Failed to update personal information: {e}")
        raise


def update_settings(**kwargs) -> None:
    """
    Update application settings.
    
    Args:
        **kwargs: Settings to update
    """
    try:
        config_manager = _get_config_manager()
        config_manager.update_settings(**kwargs)
        logger.info("Application settings updated successfully")
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise


def save_personal_info(path: Optional[Path] = None) -> None:
    """
    Save personal information to file.
    
    Args:
        path: Optional path to save to, defaults to configured path
    """
    try:
        config_manager = _get_config_manager()
        config_manager.save_personal_info(path)
        logger.info(f"Personal information saved to {path or config_manager.file_paths.personal_info}")
    except Exception as e:
        logger.error(f"Failed to save personal information: {e}")
        raise


def save_keyword_weights(path: Optional[Path] = None) -> None:
    """
    Save keyword weights to file.
    
    Args:
        path: Optional path to save to, defaults to configured path
    """
    try:
        config_manager = _get_config_manager()
        config_manager.save_keyword_weights(path)
        logger.info(f"Keyword weights saved to {path or config_manager.file_paths.keyword_weights}")
    except Exception as e:
        logger.error(f"Failed to save keyword weights: {e}")
        raise


# ===== Debug and Utility Functions =====

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration for debugging.
    
    Returns:
        Dict containing configuration summary (excluding sensitive data)
    """
    try:
        config_manager = _get_config_manager()
        return config_manager.get_config_summary()
    except Exception as e:
        logger.error(f"Failed to get config summary: {e}")
        return {"error": str(e)}


def reload_config() -> None:
    """Reload configuration from files."""
    global _config_manager
    _config_manager = None
    logger.info("Configuration reloaded")


def initialize_config(
    personal_info_path: Optional[Path] = None,
    keyword_weights_path: Optional[Path] = None,
    env_file: Optional[Path] = None
) -> None:
    """
    Initialize configuration with specific file paths.
    
    Args:
        personal_info_path: Path to personal_info.yaml
        keyword_weights_path: Path to keyword_weights.json
        env_file: Path to .env file
    """
    global _config_manager
    try:
        from .config_manager import initialize_config_manager
        _config_manager = initialize_config_manager(
            personal_info_path=personal_info_path,
            keyword_weights_path=keyword_weights_path,
            env_file=env_file
        )
        logger.info("Configuration initialized with custom paths")
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        raise


# ===== Migration Helper Functions =====

def migrate_from_old_config() -> None:
    """
    Migrate configuration from the old config.py system.
    This is a one-time migration function.
    """
    try:
        from .config_migration import migrate_configuration
        migrated_config = migrate_configuration()
        
        # Create a new config manager with migrated data
        global _config_manager
        from .config_manager import ConfigManager
        _config_manager = ConfigManager.from_dict(migrated_config)
        
        logger.info("Configuration migrated successfully from old system")
    except Exception as e:
        logger.error(f"Failed to migrate configuration: {e}")
        raise


def create_migration_report() -> Dict[str, Any]:
    """
    Create a migration report.
    
    Returns:
        Dict containing migration report
    """
    try:
        from .config_migration import create_migration_report
        return create_migration_report()
    except Exception as e:
        logger.error(f"Failed to create migration report: {e}")
        return {"error": str(e)}


# ===== Module-level initialization =====
# Initialize configuration manager lazily to avoid import-time errors
_config_manager = None

def _safe_get_config_manager() -> Optional[ConfigManager]:
    """Safely get config manager, returning None if not available."""
    global _config_manager
    if _config_manager is None:
        try:
            _config_manager = get_config_manager()
        except Exception as e:
            logger.warning(f"Failed to initialize configuration manager: {e}")
            return None
    return _config_manager

# Override the _get_config_manager function to be safer
def _get_config_manager() -> ConfigManager:
    """Get or initialize the global config manager."""
    global _config_manager
    if _config_manager is None:
        try:
            _config_manager = get_config_manager()
        except Exception as e:
            logger.error(f"Failed to initialize configuration manager: {e}")
            # Create a minimal config manager for backward compatibility
            from .config_schemas import AppSettings, PersonalInfo, LinkedInSelectors, FilePaths
            from .config_manager import ConfigManager
            
            # Create minimal settings with defaults
            settings = AppSettings(
                linkedin_email="",  # Empty but valid
                linkedin_password=""  # Empty but valid
            )
            
            # Create minimal personal info
            personal_info = PersonalInfo(
                first_name="",
                last_name="",
                email="",
                phone="",
                address={
                    "street": "",
                    "city": "",
                    "state": "",
                    "zip": ""
                },
                linkedin="",
                job_history=[],
                education=[],
                references=[]
            )
            
            # Create minimal selectors
            linkedin_selectors = LinkedInSelectors(
                login={},
                login_fallbacks=[],
                login_success=[],
                job_search={},
                job_detail={},
                easy_apply={},
                easy_apply_fallbacks=[],
                resume_upload={},
                application_status={},
                form_fields={}
            )
            
            # Create minimal file paths
            file_paths = FilePaths(
                personal_info=Path("personal_info.yaml"),
                job_urls=Path("job_urls.json"),
                stopwords=Path("stopwords.json"),
                tech_dictionary=Path("tech_dictionary.json"),
                keyword_weights=Path("keyword_weights.json"),
                resumes_dir=Path("output/resumes"),
                templates_dir=Path("templates"),
                output_dir=Path("output")
            )
            
            # Create minimal config
            from .config_schemas import AppConfig
            config = AppConfig(
                settings=settings,
                personal_info=personal_info,
                linkedin_selectors=linkedin_selectors,
                file_paths=file_paths
            )
            
            _config_manager = ConfigManager(config)
            logger.warning("Created minimal configuration manager for backward compatibility")
    
    return _config_manager
