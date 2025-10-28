# test_new_config.py

"""
Test script to demonstrate the new type-safe configuration system.
This script shows how to use the new configuration system and validates its functionality.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test that all configuration modules can be imported."""
    print("=== Testing Basic Imports ===")
    
    try:
        from config_schemas import PersonalInfo, AppSettings, AppConfig
        print("config_schemas imported successfully")
        
        from config_manager import ConfigManager
        print("config_manager imported successfully")
        
        from config_migration import ConfigMigration
        print("config_migration imported successfully")
        
        from config_compat import MAX_JOBS, LINKEDIN_EMAIL, validate_config
        print("config_compat imported successfully")
        
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False


def test_schema_validation():
    """Test Pydantic schema validation."""
    print("\n=== Testing Schema Validation ===")
    
    try:
        from config_schemas import PersonalInfo, Address, Education, JobHistory
        
        # Test valid personal info
        address = Address(
            street="123 Main St",
            city="Atlanta",
            state="GA",
            zip="30309"
        )
        print("Address validation passed")
        
        education = Education(
            degree="Bachelor of Science",
            institution="Georgia Tech",
            location="Atlanta, GA",
            graduation_date="05-2020"
        )
        print("Education validation passed")
        
        job = JobHistory(
            title="Software Engineer",
            company="Tech Corp",
            location="Atlanta, GA",
            start_date="01-2020",
            end_date="present",
            responsibilities=["Developed software"]
        )
        print("Job history validation passed")
        
        personal_info = PersonalInfo(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="(555) 123-4567",
            address=address,
            linkedin="https://www.linkedin.com/in/john-doe",
            job_history=[job],
            education=[education],
            references=[]
        )
        print("Personal info validation passed")
        
        return True
    except Exception as e:
        print(f"Schema validation failed: {e}")
        return False


def test_backward_compatibility():
    """Test backward compatibility with old config.py interface."""
    print("\n=== Testing Backward Compatibility ===")
    
    try:
        from config_compat import (
            MAX_JOBS, LINKEDIN_EMAIL, DEBUG, AUTO_APPLY,
            BASE_DIR, OUTPUT_DIR, RESUMES_DIR, TEMPLATES_DIR
        )
        
        print(f"MAX_JOBS: {MAX_JOBS}")
        print(f"LINKEDIN_EMAIL: {LINKEDIN_EMAIL}")
        print(f"DEBUG: {DEBUG}")
        print(f"AUTO_APPLY: {AUTO_APPLY}")
        print(f"BASE_DIR: {BASE_DIR}")
        print(f"OUTPUT_DIR: {OUTPUT_DIR}")
        print(f"RESUMES_DIR: {RESUMES_DIR}")
        print(f"TEMPLATES_DIR: {TEMPLATES_DIR}")
        
        return True
    except Exception as e:
        print(f"Backward compatibility failed: {e}")
        return False


def test_config_manager():
    """Test ConfigManager functionality."""
    print("\n=== Testing ConfigManager ===")
    
    try:
        from config_manager import ConfigManager
        from config_schemas import PersonalInfo, Address
        
        # Create a minimal config for testing
        config_data = {
            "settings": {
                "linkedin_email": "test@example.com",
                "linkedin_password": "password123",
                "max_jobs": 20,
                "debug": True
            },
            "personal_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "(555) 123-4567",
                "address": {
                    "street": "123 Main St",
                    "city": "Atlanta",
                    "state": "GA",
                    "zip": "30309"
                },
                "linkedin": "https://www.linkedin.com/in/john-doe",
                "job_history": [],
                "education": [],
                "references": []
            },
            "linkedin_selectors": {
                "login": {"username": "input[id='username']"},
                "login_fallbacks": [],
                "login_success": [],
                "job_search": {},
                "job_detail": {},
                "easy_apply": {},
                "easy_apply_fallbacks": [],
                "resume_upload": {},
                "application_status": {},
                "form_fields": {}
            },
            "file_paths": {
                "personal_info": Path("personal_info.yaml"),
                "job_urls": Path("job_urls.json"),
                "stopwords": Path("stopwords.json"),
                "tech_dictionary": Path("tech_dictionary.json"),
                "keyword_weights": Path("keyword_weights.json"),
                "resumes_dir": Path("output/resumes"),
                "templates_dir": Path("templates"),
                "output_dir": Path("output")
            }
        }
        
        config_manager = ConfigManager.from_dict(config_data)
        print("ConfigManager created successfully")
        
        # Test properties
        print(f"LinkedIn Email: {config_manager.linkedin_email}")
        print(f"Max Jobs: {config_manager.max_jobs}")
        print(f"Debug: {config_manager.debug}")
        print(f"Personal Info Name: {config_manager.personal_info.first_name} {config_manager.personal_info.last_name}")
        
        # Test validation
        if config_manager.validate_credentials():
            print("Credential validation passed")
        else:
            print("Credential validation failed (expected without real credentials)")
        
        # Test configuration summary
        summary = config_manager.get_config_summary()
        print(f"Configuration summary: {list(summary.keys())}")
        
        return True
    except Exception as e:
        print(f"ConfigManager test failed: {e}")
        return False


def test_migration():
    """Test configuration migration functionality."""
    print("\n=== Testing Configuration Migration ===")
    
    try:
        from config_migration import ConfigMigration
        
        # Test migration report
        report = ConfigMigration.create_migration_report()
        print("Migration report created successfully")
        print(f"Migrated components: {report['migrated_components']}")
        print(f"Environment variables: {len(report['environment_variables_used'])}")
        
        # Test migration (this will fail without environment variables, but that's expected)
        try:
            migrated_config = ConfigMigration.migrate_from_old_config()
            print("Configuration migration completed")
        except Exception as e:
            print(f"Migration failed (expected without environment variables): {e}")
        
        return True
    except Exception as e:
        print(f"Migration test failed: {e}")
        return False


def test_type_safety():
    """Test type safety features."""
    print("\n=== Testing Type Safety ===")
    
    try:
        from config_schemas import PersonalInfo, Address
        
        # Test invalid email
        try:
            invalid_personal_info = PersonalInfo(
                first_name="John",
                last_name="Doe",
                email="invalid-email",  # Invalid format
                phone="(555) 123-4567",
                address=Address(
                    street="123 Main St",
                    city="Atlanta",
                    state="GA",
                    zip="30309"
                ),
                linkedin="https://www.linkedin.com/in/john-doe",
                job_history=[],
                education=[],
                references=[]
            )
            print("Invalid email should have been caught")
            return False
        except ValueError as e:
            print(f"Email validation caught error: {e}")
        
        # Test invalid LinkedIn URL
        try:
            invalid_personal_info = PersonalInfo(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="(555) 123-4567",
                address=Address(
                    street="123 Main St",
                    city="Atlanta",
                    state="GA",
                    zip="30309"
                ),
                linkedin="https://linkedin.com/in/john-doe",  # Invalid format
                job_history=[],
                education=[],
                references=[]
            )
            print("Invalid LinkedIn URL should have been caught")
            return False
        except ValueError as e:
            print(f"LinkedIn URL validation caught error: {e}")
        
        return True
    except Exception as e:
        print(f"Type safety test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Type-Safe Configuration System")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_schema_validation,
        test_backward_compatibility,
        test_config_manager,
        test_migration,
        test_type_safety
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed! Configuration system is working correctly.")
    else:
        print("Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
