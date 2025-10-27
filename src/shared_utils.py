# src/shared_utils.py

"""
Shared utility functions to eliminate code duplication across modules.
Provides common functionality for file operations, data handling, and validation.
"""

import json
import yaml
import os
import time
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations with consistent error handling."""
    
    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load YAML file with error handling.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Dictionary containing YAML data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"YAML file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading YAML {file_path}: {e}")
            raise
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """
        Save data to YAML file with error handling.
        
        Args:
            data: Data to save
            file_path: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"Error saving YAML to {file_path}: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> List[str]:
        """
        Load JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of strings from JSON file
        """
        try:
            if not os.path.exists(file_path):
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return []
    
    @staticmethod
    def save_json(data: List[str], file_path: Union[str, Path]) -> bool:
        """
        Save data to JSON file with error handling.
        
        Args:
            data: Data to save
            file_path: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False

class DataValidator:
    """Validates data structures and formats."""
    
    @staticmethod
    def validate_personal_info(data: Dict[str, Any]) -> List[str]:
        """
        Validate personal information structure.
        
        Args:
            data: Personal information dictionary
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        required_fields = ["first_name", "last_name", "email", "phone"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        if "email" in data and "@" not in data["email"]:
            errors.append("Invalid email format")
        
        # Validate job history structure
        if "job_history" in data:
            for i, job in enumerate(data["job_history"]):
                if not isinstance(job, dict):
                    errors.append(f"Job {i} is not a dictionary")
                    continue
                
                job_required = ["title", "company", "start_date"]
                for field in job_required:
                    if field not in job or not job[field]:
                        errors.append(f"Job {i} missing required field: {field}")
        
        return errors
    
    @staticmethod
    def validate_job_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate job data structure.
        
        Args:
            data: Job data dictionary
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        required_fields = ["title", "company", "description"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required job field: {field}")
        
        return errors

class TextProcessor:
    """Handles text processing and cleaning operations."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = " ".join(text.split())
        
        # Remove common HTML entities
        html_entities = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&nbsp;": " "
        }
        
        for entity, replacement in html_entities.items():
            cleaned = cleaned.replace(entity, replacement)
        
        return cleaned.strip()
    
    @staticmethod
    def normalize_skill(skill: str) -> str:
        """
        Normalize skill names for consistent matching.
        
        Args:
            skill: Raw skill name
            
        Returns:
            Normalized skill name
        """
        if not skill:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = skill.lower().strip()
        
        # Remove common variations
        variations = {
            "javascript": "JavaScript",
            "python": "Python",
            "react": "React",
            "node.js": "Node.js",
            "aws": "AWS",
            "docker": "Docker"
        }
        
        return variations.get(normalized, skill)
    
    @staticmethod
    def sanitize_filename(text: str) -> str:
        """
        Sanitize text for safe filename usage.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized filename-safe text
        """
        import re
        if not text:
            return "unknown"
        
        # Remove or replace unsafe characters
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', text.replace(" ", "_"))
        return sanitized or "unknown"

class DelayManager:
    """Manages delays and timing for human-like automation."""
    
    @staticmethod
    def human_like_delay(min_delay: float = 0.5, max_delay: float = 2.0) -> None:
        """
        Add human-like delay with random variation.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @staticmethod
    def ui_stability_delay() -> None:
        """Add delay for UI stability."""
        time.sleep(0.5)
    
    @staticmethod
    def processing_delay() -> None:
        """Add delay for processing operations."""
        time.sleep(1.0)

class DataMerger:
    """Manages data merging and merging operations."""
    
    @staticmethod
    def merge_job_data(base_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge base data with job-specific data.
        
        Args:
            base_data: Base data dictionary
            job_data: Job-specific data dictionary
            
        Returns:
            Merged data dictionary
        """
        merged = base_data.copy()
        merged.update(job_data)
        return merged
    
    @staticmethod
    def merge_skills(base_skills: List[str], job_skills: List[str]) -> List[str]:
        """
        Merge skill lists without duplicates.
        
        Args:
            base_skills: Base skills list
            job_skills: Job-specific skills list
            
        Returns:
            Merged skills list without duplicates
        """
        all_skills = base_skills + job_skills
        return list(dict.fromkeys(all_skills))  # Remove duplicates while preserving order

class PathManager:
    """Manages file paths and directory operations."""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def get_safe_path(base_path: Union[str, Path], filename: str) -> Path:
        """
        Get safe file path with sanitized filename.
        
        Args:
            base_path: Base directory path
            filename: Filename to sanitize
            
        Returns:
            Safe Path object
        """
        safe_filename = TextProcessor.sanitize_filename(filename)
        return Path(base_path) / safe_filename

# Export commonly used functions
__all__ = [
    'FileHandler',
    'DataValidator', 
    'TextProcessor',
    'DelayManager',
    'DataMerger',
    'PathManager'
]



