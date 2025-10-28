# src/config_manager.py

"""
Type-safe configuration manager using Pydantic schemas.
This module provides a centralized way to load, validate, and access configuration.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from src.logging_config import get_logger, log_function_call, log_error_context
from .config_schemas import AppConfig, AppSettings, PersonalInfo, KeywordWeights

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)


class ConfigManager:
    """
    Centralized configuration manager with type safety and validation.
    
    This class provides a single point of access for all configuration
    throughout the application, with automatic validation and error handling.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config: Pre-loaded AppConfig instance, or None to load from files
        """
        self._config = config
        self._initialized = config is not None
    
    @classmethod
    def from_files(
        cls,
        personal_info_path: Optional[Path] = None,
        keyword_weights_path: Optional[Path] = None,
        env_file: Optional[Path] = None
    ) -> "ConfigManager":
        """
        Create ConfigManager by loading configuration from files.
        
        Args:
            personal_info_path: Path to personal_info.yaml
            keyword_weights_path: Path to keyword_weights.json
            env_file: Path to .env file
            
        Returns:
            ConfigManager: Initialized configuration manager
            
        Raises:
            ValueError: If configuration files cannot be loaded or validated
        """
        try:
            config = AppConfig.load_from_files(
                personal_info_path=personal_info_path,
                keyword_weights_path=keyword_weights_path,
                env_file=env_file
            )
            logger.info("Configuration loaded successfully from files")
            return cls(config)
        except Exception as e:
            logger.error(f"Failed to load configuration from files: {e}")
            raise ValueError(f"Configuration loading failed: {e}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConfigManager":
        """
        Create ConfigManager from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration data
            
        Returns:
            ConfigManager: Initialized configuration manager
        """
        try:
            config = AppConfig(**config_dict)
            logger.info("Configuration loaded successfully from dictionary")
            return cls(config)
        except Exception as e:
            logger.error(f"Failed to load configuration from dictionary: {e}")
            raise ValueError(f"Configuration loading failed: {e}")
    
    def initialize(self) -> None:
        """Initialize the configuration if not already done."""
        if not self._initialized:
            try:
                self._config = AppConfig.load_from_files()
                self._initialized = True
                logger.info("Configuration initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize configuration: {e}")
                raise ValueError(f"Configuration initialization failed: {e}")
    
    @property
    def config(self) -> AppConfig:
        """Get the complete configuration object."""
        if not self._initialized:
            self.initialize()
        return self._config
    
    # Convenience properties for easy access
    @property
    def settings(self) -> AppSettings:
        """Get application settings."""
        return self.config.settings
    
    @property
    def personal_info(self) -> PersonalInfo:
        """Get personal information."""
        return self.config.personal_info
    
    @property
    def keyword_weights(self) -> KeywordWeights:
        """Get keyword weights configuration."""
        return self.config.keyword_weights
    
    @property
    def linkedin_email(self) -> str:
        """Get LinkedIn email."""
        return self.settings.linkedin_email
    
    @property
    def linkedin_password(self) -> str:
        """Get LinkedIn password."""
        return self.settings.linkedin_password
    
    @property
    def max_jobs(self) -> int:
        """Get maximum jobs to scrape."""
        return self.settings.max_jobs
    
    @property
    def auto_apply(self) -> bool:
        """Get auto-apply setting."""
        return self.settings.auto_apply
    
    @property
    def debug(self) -> bool:
        """Get debug mode setting."""
        return self.settings.debug
    
    @property
    def headless_mode(self) -> bool:
        """Get headless mode setting."""
        return self.settings.headless_mode
    
    @property
    def file_paths(self):
        """Get file paths configuration."""
        return self.config.file_paths
    
    @property
    def timeouts(self):
        """Get timeout configuration."""
        return self.config.timeouts
    
    @property
    def retry_config(self):
        """Get retry configuration."""
        return self.config.retry_config
    
    @property
    def delays(self):
        """Get delay configuration."""
        return self.config.delays
    
    @property
    def linkedin_selectors(self):
        """Get LinkedIn selectors configuration."""
        return self.config.linkedin_selectors
    
    @property
    def question_config(self):
        """Get question configuration."""
        return self.config.question_config
    
    @property
    def scroll_config(self):
        """Get scroll configuration."""
        return self.config.scroll_config
    
    @property
    def browser_config(self):
        """Get browser configuration."""
        return self.config.browser_config
    
    def validate_credentials(self) -> bool:
        """Validate that required credentials are present."""
        return self.config.validate_linkedin_credentials()
    
    def get_resume_template_path(self) -> Path:
        """Get the path to the resume template."""
        return self.config.get_resume_template_path()
    
    def get_output_resume_path(self, job_title: str, company: str) -> Path:
        """Generate output resume path for a specific job."""
        return self.config.get_output_resume_path(job_title, company)
    
    def save_personal_info(self, path: Optional[Path] = None) -> None:
        """Save personal information to file."""
        self.config.save_personal_info(path)
        logger.info(f"Personal info saved to {path or self.file_paths.personal_info}")
    
    def save_keyword_weights(self, path: Optional[Path] = None) -> None:
        """Save keyword weights to file."""
        self.config.save_keyword_weights(path)
        logger.info(f"Keyword weights saved to {path or self.file_paths.keyword_weights}")
    
    def update_personal_info(self, **kwargs) -> None:
        """
        Update personal information fields.
        
        Args:
            **kwargs: Fields to update in personal information
        """
        try:
            # Create updated personal info
            current_data = self.personal_info.dict()
            current_data.update(kwargs)
            updated_personal_info = PersonalInfo(**current_data)
            
            # Update the config
            self.config.personal_info = updated_personal_info
            logger.info("Personal information updated successfully")
        except Exception as e:
            logger.error(f"Failed to update personal information: {e}")
            raise ValueError(f"Personal information update failed: {e}")
    
    def update_settings(self, **kwargs) -> None:
        """
        Update application settings.
        
        Args:
            **kwargs: Settings to update
        """
        try:
            # Create updated settings
            current_data = self.settings.dict()
            current_data.update(kwargs)
            updated_settings = AppSettings(**current_data)
            
            # Update the config
            self.config.settings = updated_settings
            logger.info("Application settings updated successfully")
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            raise ValueError(f"Settings update failed: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration for debugging.
        
        Returns:
            Dict containing configuration summary (excluding sensitive data)
        """
        return {
            "debug_mode": self.debug,
            "max_jobs": self.max_jobs,
            "auto_apply": self.auto_apply,
            "headless_mode": self.headless_mode,
            "linkedin_email_set": bool(self.linkedin_email),
            "linkedin_password_set": bool(self.linkedin_password),
            "personal_info_loaded": bool(self.personal_info),
            "keyword_weights_loaded": bool(self.keyword_weights),
            "file_paths": {
                "personal_info": str(self.file_paths.personal_info),
                "resumes_dir": str(self.file_paths.resumes_dir),
                "templates_dir": str(self.file_paths.templates_dir),
                "output_dir": str(self.file_paths.output_dir),
            },
            "timeouts": self.timeouts.dict(),
            "retry_config": self.retry_config.dict(),
        }
    
    def __repr__(self) -> str:
        """String representation of the configuration manager."""
        return f"ConfigManager(initialized={self._initialized}, debug={self.debug})"


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager: Global configuration manager
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager.from_files()
    return _config_manager


def initialize_config_manager(
    personal_info_path: Optional[Path] = None,
    keyword_weights_path: Optional[Path] = None,
    env_file: Optional[Path] = None
) -> ConfigManager:
    """
    Initialize the global configuration manager with specific file paths.
    
    Args:
        personal_info_path: Path to personal_info.yaml
        keyword_weights_path: Path to keyword_weights.json
        env_file: Path to .env file
        
    Returns:
        ConfigManager: Initialized global configuration manager
    """
    global _config_manager
    _config_manager = ConfigManager.from_files(
        personal_info_path=personal_info_path,
        keyword_weights_path=keyword_weights_path,
        env_file=env_file
    )
    return _config_manager


def reset_config_manager() -> None:
    """Reset the global configuration manager."""
    global _config_manager
    _config_manager = None
