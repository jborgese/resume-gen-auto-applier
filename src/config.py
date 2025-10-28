# src/config.py

"""
Modern type-safe configuration system with backward compatibility.
This module replaces the old config.py with a Pydantic-based system
while maintaining the same interface for existing code.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.logging_config import get_logger, log_function_call, log_error_context

# Import the new configuration system
from .config_manager import get_config_manager, ConfigManager
from .config_schemas import AppConfig

logger = get_logger(__name__)

# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def _get_config_manager() -> ConfigManager:
    """Get or initialize the global config manager."""
    global _config_manager
    if _config_manager is None:
        try:
            _config_manager = get_config_manager()
        except Exception as e:
            logger.error(f"Failed to initialize configuration manager: {e}")
            # Create a minimal fallback config for backward compatibility
            _config_manager = _create_fallback_config()
    return _config_manager


def _create_fallback_config() -> ConfigManager:
    """Create a minimal fallback configuration for backward compatibility."""
    from .config_schemas import AppSettings, PersonalInfo, Address, LinkedInSelectors, FilePaths
    from .config_manager import ConfigManager
    
    # Create minimal settings with defaults
    settings = AppSettings(
        linkedin_email=os.getenv("LINKEDIN_EMAIL", "dummy@example.com"),
        linkedin_password=os.getenv("LINKEDIN_PASSWORD", "dummy_password")
    )
    
    # Create minimal personal info with valid defaults
    personal_info = PersonalInfo(
        first_name="Dummy",
        last_name="User",
        email="dummy@example.com",
        phone="(555) 123-4567",
        address=Address(
            street="123 Main St",
            city="Atlanta",
            state="GA",
            zip="30309"
        ),
        linkedin="https://www.linkedin.com/in/dummy-user",
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
    base_dir = Path(__file__).parent.parent
    file_paths = FilePaths(
        personal_info=base_dir / "personal_info.yaml",
        job_urls=base_dir / "job_urls.json",
        stopwords=base_dir / "src" / "stopwords.json",
        tech_dictionary=base_dir / "src" / "tech_dictionary.json",
        keyword_weights=base_dir / "src" / "keyword_weights.json",
        resumes_dir=base_dir / "output" / "resumes",
        templates_dir=base_dir / "templates",
        output_dir=base_dir / "output"
    )
    
    # Create minimal config
    config = AppConfig(
        settings=settings,
        personal_info=personal_info,
        linkedin_selectors=linkedin_selectors,
        file_paths=file_paths
    )
    
    return ConfigManager(config)


# ===== Backward Compatibility Constants =====
# These provide the same interface as the old config.py

class LazyConfig:
    """Lazy-loaded configuration constants for backward compatibility."""
    
    @property
    def BASE_DIR(self) -> Path:
        return _get_config_manager().settings.base_dir
    
    @property
    def OUTPUT_DIR(self) -> Path:
        return _get_config_manager().file_paths.output_dir
    
    @property
    def RESUMES_DIR(self) -> Path:
        return _get_config_manager().file_paths.resumes_dir
    
    @property
    def TEMPLATES_DIR(self) -> Path:
        return _get_config_manager().file_paths.templates_dir
    
    @property
    def LINKEDIN_EMAIL(self) -> str:
        return _get_config_manager().linkedin_email
    
    @property
    def LINKEDIN_PASSWORD(self) -> str:
        return _get_config_manager().linkedin_password
    
    @property
    def PORTFOLIO(self) -> Optional[str]:
        return _get_config_manager().settings.portfolio
    
    @property
    def MAX_JOBS(self) -> int:
        return _get_config_manager().max_jobs
    
    @property
    def AUTO_APPLY(self) -> bool:
        return _get_config_manager().auto_apply
    
    @property
    def DEFAULT_TEMPLATE(self) -> str:
        return _get_config_manager().settings.default_template
    
    @property
    def DEBUG(self) -> bool:
        return _get_config_manager().debug
    
    @property
    def HEADLESS_MODE(self) -> bool:
        return _get_config_manager().headless_mode
    
    @property
    def ENABLE_BROWSER_MONITORING(self) -> bool:
        return _get_config_manager().settings.enable_browser_monitoring
    
    @property
    def SUPPRESS_CONSOLE_WARNINGS(self) -> bool:
        return _get_config_manager().settings.suppress_console_warnings
    
    @property
    def TIMEOUTS(self) -> Dict[str, int]:
        return _get_config_manager().timeouts.dict()
    
    @property
    def RETRY_CONFIG(self) -> Dict[str, Any]:
        return _get_config_manager().retry_config.dict()
    
    @property
    def LINKEDIN_SELECTORS(self) -> Dict[str, Any]:
        return _get_config_manager().linkedin_selectors.dict()
    
    @property
    def FILE_PATHS(self) -> Dict[str, Path]:
        return _get_config_manager().file_paths.dict()
    
    @property
    def SCROLL_CONFIG(self) -> Dict[str, Any]:
        return _get_config_manager().scroll_config.dict()
    
    @property
    def QUESTION_CONFIG(self) -> Dict[str, Any]:
        return _get_config_manager().question_config.dict()
    
    @property
    def DELAYS(self) -> Dict[str, Any]:
        return _get_config_manager().delays.dict()


# Create lazy config instance
_lazy_config = LazyConfig()

# Export constants for backward compatibility
BASE_DIR = _lazy_config.BASE_DIR
OUTPUT_DIR = _lazy_config.OUTPUT_DIR
RESUMES_DIR = _lazy_config.RESUMES_DIR
TEMPLATES_DIR = _lazy_config.TEMPLATES_DIR
LINKEDIN_EMAIL = _lazy_config.LINKEDIN_EMAIL
LINKEDIN_PASSWORD = _lazy_config.LINKEDIN_PASSWORD
PORTFOLIO = _lazy_config.PORTFOLIO
MAX_JOBS = _lazy_config.MAX_JOBS
AUTO_APPLY = _lazy_config.AUTO_APPLY
DEFAULT_TEMPLATE = _lazy_config.DEFAULT_TEMPLATE
DEBUG = _lazy_config.DEBUG
HEADLESS_MODE = _lazy_config.HEADLESS_MODE
ENABLE_BROWSER_MONITORING = _lazy_config.ENABLE_BROWSER_MONITORING
SUPPRESS_CONSOLE_WARNINGS = _lazy_config.SUPPRESS_CONSOLE_WARNINGS
TIMEOUTS = _lazy_config.TIMEOUTS
RETRY_CONFIG = _lazy_config.RETRY_CONFIG
LINKEDIN_SELECTORS = _lazy_config.LINKEDIN_SELECTORS
FILE_PATHS = _lazy_config.FILE_PATHS
SCROLL_CONFIG = _lazy_config.SCROLL_CONFIG
QUESTION_CONFIG = _lazy_config.QUESTION_CONFIG
DELAYS = _lazy_config.DELAYS


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


# ===== New Configuration System Access =====

def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    This provides access to the new type-safe configuration system.
    """
    return _get_config_manager()


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


# ===== Module-level initialization =====
# Initialize configuration manager lazily to avoid import-time errors
logger.info("Configuration system initialized with backward compatibility")