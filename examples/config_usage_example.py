# examples/config_usage_example.py

"""
Example script demonstrating how to use the new type-safe configuration system.
This shows the migration from the old config.py to the new Pydantic-based system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager, initialize_config_manager
from config_schemas import AppConfig
from config_migration import ConfigMigration
from config_compat import (
    get_personal_info, get_keyword_weights, validate_config,
    update_personal_info, save_personal_info
)


def example_basic_usage():
    """Example of basic configuration usage."""
    print("=== Basic Configuration Usage ===")
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager.from_files()
        
        # Access configuration properties
        print(f"LinkedIn Email: {config_manager.linkedin_email}")
        print(f"Max Jobs: {config_manager.max_jobs}")
        print(f"Auto Apply: {config_manager.auto_apply}")
        print(f"Debug Mode: {config_manager.debug}")
        
        # Access personal information
        personal_info = config_manager.personal_info
        print(f"Name: {personal_info.first_name} {personal_info.last_name}")
        print(f"Email: {personal_info.email}")
        print(f"LinkedIn: {personal_info.linkedin}")
        
        # Access configuration objects
        print(f"Page Load Timeout: {config_manager.timeouts.page_load}ms")
        print(f"Max Retry Attempts: {config_manager.retry_config.max_attempts}")
        
        # Validate credentials
        if config_manager.validate_credentials():
            print("✅ LinkedIn credentials are valid")
        else:
            print("❌ LinkedIn credentials are missing")
        
        # Get configuration summary
        summary = config_manager.get_config_summary()
        print(f"Configuration Summary: {summary}")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")


def example_configuration_updates():
    """Example of updating configuration."""
    print("\n=== Configuration Updates ===")
    
    try:
        config_manager = ConfigManager.from_files()
        
        # Update personal information
        config_manager.update_personal_info(
            first_name="Updated Name",
            phone="(555) 999-8888"
        )
        print("✅ Personal information updated")
        
        # Update settings
        config_manager.update_settings(
            max_jobs=25,
            debug=True
        )
        print("✅ Settings updated")
        
        # Save changes
        config_manager.save_personal_info()
        print("✅ Personal information saved to file")
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")


def example_backward_compatibility():
    """Example of backward compatibility with old config.py."""
    print("\n=== Backward Compatibility ===")
    
    try:
        # Use the same interface as old config.py
        from config_compat import (
            LINKEDIN_EMAIL, MAX_JOBS, AUTO_APPLY, DEBUG,
            validate_config, get_personal_info, get_keyword_weights
        )
        
        print(f"LinkedIn Email (compat): {LINKEDIN_EMAIL}")
        print(f"Max Jobs (compat): {MAX_JOBS}")
        print(f"Auto Apply (compat): {AUTO_APPLY}")
        print(f"Debug (compat): {DEBUG}")
        
        # Validate configuration
        if validate_config():
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")
        
        # Get personal info (same as loading from YAML)
        personal_info = get_personal_info()
        print(f"Personal Info Keys: {list(personal_info.keys())}")
        
        # Get keyword weights (same as loading from JSON)
        keyword_weights = get_keyword_weights()
        print(f"Keyword Weights Keys: {list(keyword_weights.keys())}")
        
    except Exception as e:
        print(f"❌ Error with backward compatibility: {e}")


def example_migration():
    """Example of migrating from old configuration system."""
    print("\n=== Configuration Migration ===")
    
    try:
        # Create migration report
        report = ConfigMigration.create_migration_report()
        print("Migration Report:")
        print(f"  Components: {report['migrated_components']}")
        print(f"  Environment Variables: {report['environment_variables_used']}")
        print(f"  Required Files: {report['files_required']}")
        
        # Migrate configuration
        migrated_config = ConfigMigration.migrate_from_old_config()
        print(f"✅ Configuration migrated successfully")
        print(f"  Migrated components: {list(migrated_config.keys())}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")


def example_custom_initialization():
    """Example of custom configuration initialization."""
    print("\n=== Custom Initialization ===")
    
    try:
        # Initialize with custom file paths
        config_manager = initialize_config_manager(
            personal_info_path=Path("custom_personal_info.yaml"),
            keyword_weights_path=Path("custom_keyword_weights.json"),
            env_file=Path("custom.env")
        )
        
        print("✅ Custom configuration initialized")
        
    except Exception as e:
        print(f"❌ Error with custom initialization: {e}")


def example_type_safety():
    """Example of type safety benefits."""
    print("\n=== Type Safety Benefits ===")
    
    try:
        from config_schemas import PersonalInfo, Address
        
        # This will work - all required fields provided
        address = Address(
            street="123 Main St",
            city="Atlanta",
            state="GA",
            zip="30309"
        )
        print("✅ Valid address created")
        
        # This will fail - missing required fields
        try:
            invalid_address = Address(
                street="123 Main St",
                city="Atlanta"
                # Missing state and zip
            )
        except Exception as e:
            print(f"✅ Type validation caught error: {e}")
        
        # This will fail - invalid email format
        try:
            invalid_personal_info = PersonalInfo(
                first_name="John",
                last_name="Doe",
                email="invalid-email",  # Invalid format
                phone="(555) 123-4567",
                address=address,
                linkedin="https://www.linkedin.com/in/john-doe",
                job_history=[],
                education=[],
                references=[]
            )
        except Exception as e:
            print(f"✅ Email validation caught error: {e}")
        
    except Exception as e:
        print(f"❌ Error demonstrating type safety: {e}")


def main():
    """Run all examples."""
    print("🚀 Type-Safe Configuration System Examples")
    print("=" * 50)
    
    example_basic_usage()
    example_configuration_updates()
    example_backward_compatibility()
    example_migration()
    example_custom_initialization()
    example_type_safety()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")


if __name__ == "__main__":
    main()
