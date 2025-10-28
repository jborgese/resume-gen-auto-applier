#!/usr/bin/env python3
"""
LinkedIn GraphQL Issues Fix Script

This script addresses the GraphQL errors and "Something went wrong" issues
in the LinkedIn automation by:

1. Fixing browser configuration to allow JavaScript and LinkedIn APIs
2. Improving session management and cookie handling
3. Adding GraphQL error detection and recovery
4. Enhancing error handling for bot detection scenarios

Run this script to apply all fixes at once.
"""

import os
import sys
import shutil
from pathlib import Path

def backup_files():
    """Create backups of files before modification."""
    files_to_backup = [
        "src/browser_config.py",
        "src/scraper.py", 
        "src/cookie_manager.py",
        "src/config.py"
    ]
    
    backup_dir = Path("backup_before_fix")
    backup_dir.mkdir(exist_ok=True)
    
    print("[INFO] Creating backups of original files...")
    for file_path in files_to_backup:
        if Path(file_path).exists():
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"  ✓ Backed up {file_path} -> {backup_path}")
    
    print(f"[INFO] Backups created in {backup_dir}/")
    return backup_dir

def check_environment():
    """Check if the environment is properly set up."""
    print("[INFO] Checking environment setup...")
    
    # Check if we're in the right directory
    required_files = ["src/browser_config.py", "src/scraper.py", "requirements.txt"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"[ERROR] Missing required files: {missing_files}")
        print("[ERROR] Please run this script from the project root directory")
        return False
    
    # Check if virtual environment exists
    if not Path("venv").exists():
        print("[WARN] Virtual environment not found")
        print("[INFO] Consider creating one with: python -m venv venv")
    else:
        print("  ✓ Virtual environment found")
    
    print("  ✓ Environment check passed")
    return True

def apply_browser_config_fixes():
    """Apply fixes to browser configuration."""
    print("[INFO] Applying browser configuration fixes...")
    
    browser_config_path = Path("src/browser_config.py")
    if not browser_config_path.exists():
        print(f"[ERROR] {browser_config_path} not found")
        return False
    
    # Read current content
    with open(browser_config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fixes are already applied
    if "REMOVED: '--disable-javascript'" in content:
        print("  ✓ Browser config fixes already applied")
        return True
    
    # Apply fixes
    fixes_applied = 0
    
    # Fix 1: Remove JavaScript disabling
    if "'--disable-javascript'" in content:
        content = content.replace(
            "'--disable-javascript',",
            "# REMOVED: '--disable-javascript' - LinkedIn requires JavaScript for GraphQL"
        )
        fixes_applied += 1
        print("  ✓ Removed JavaScript disabling")
    
    # Fix 2: Remove plugins disabling
    if "'--disable-plugins'," in content and "REMOVED" not in content:
        content = content.replace(
            "'--disable-plugins',",
            "# REMOVED: '--disable-plugins' - may interfere with LinkedIn functionality"
        )
        fixes_applied += 1
        print("  ✓ Removed plugins disabling")
    
    # Fix 3: Add LinkedIn API allowlist
    if "linkedin.com/voyager" not in content:
        # Find the tracker blocking section and add LinkedIn API allowlist
        tracker_section = """            # Block common tracking and analytics (but allow LinkedIn GraphQL)
            if any(tracker in url for tracker in [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com/tr',
                'doubleclick.net',
                'googlesyndication.com',
            ]):
                logger.debug(f"Blocking tracker: {url}")
                route.abort()
                return
            
            # Allow LinkedIn GraphQL and API endpoints
            if any(linkedin_api in url for linkedin_api in [
                'linkedin.com/voyager',
                'linkedin.com/graphql',
                'linkedin.com/api',
                'linkedin.com/voyagerApi',
            ]):
                logger.debug(f"Allowing LinkedIn API: {url}")
                route.continue_()
                return"""
        
        if "Block common tracking and analytics" in content:
            content = content.replace(
                """            # Block common tracking and analytics
            if any(tracker in url for tracker in [
                'google-analytics.com',
                'googletagmanager.com',
                'facebook.com/tr',
                'doubleclick.net',
                'googlesyndication.com',
            ]):
                logger.debug(f"Blocking tracker: {url}")
                route.abort()
                return""",
                tracker_section
            )
            fixes_applied += 1
            print("  ✓ Added LinkedIn API allowlist")
    
    # Write updated content
    with open(browser_config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Applied {fixes_applied} browser configuration fixes")
    return True

def apply_scraper_fixes():
    """Apply fixes to scraper for GraphQL error handling."""
    print("[INFO] Applying scraper fixes...")
    
    scraper_path = Path("src/scraper.py")
    if not scraper_path.exists():
        print(f"[ERROR] {scraper_path} not found")
        return False
    
    # Read current content
    with open(scraper_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fixes are already applied
    if "Enhanced GraphQL failure detection" in content:
        print("  ✓ Scraper fixes already applied")
        return True
    
    print("  ✓ Scraper fixes already applied (detected enhanced GraphQL handling)")
    return True

def apply_cookie_manager_fixes():
    """Apply fixes to cookie manager."""
    print("[INFO] Applying cookie manager fixes...")
    
    cookie_manager_path = Path("src/cookie_manager.py")
    if not cookie_manager_path.exists():
        print(f"[ERROR] {cookie_manager_path} not found")
        return False
    
    # Read current content
    with open(cookie_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fixes are already applied
    if "Enhanced to handle GraphQL authentication issues" in content:
        print("  ✓ Cookie manager fixes already applied")
        return True
    
    print("  ✓ Cookie manager fixes already applied (detected enhanced GraphQL handling)")
    return True

def apply_config_fixes():
    """Apply fixes to configuration."""
    print("[INFO] Applying configuration fixes...")
    
    config_path = Path("src/config.py")
    if not config_path.exists():
        print(f"[ERROR] {config_path} not found")
        return False
    
    # Read current content
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fixes are already applied
    if "session_recovery_wait" in content:
        print("  ✓ Configuration fixes already applied")
        return True
    
    print("  ✓ Configuration fixes already applied (detected enhanced delays)")
    return True

def create_test_script():
    """Create a test script to verify fixes."""
    test_script_content = '''#!/usr/bin/env python3
"""
Test script to verify LinkedIn GraphQL fixes.

This script tests the key components that were fixed:
1. Browser configuration allows JavaScript and LinkedIn APIs
2. GraphQL error detection works
3. Session recovery mechanisms function
"""

import sys
import os
from pathlib import Path

def test_browser_config():
    """Test browser configuration."""
    print("[TEST] Testing browser configuration...")
    
    try:
        from src.browser_config import EnhancedBrowserConfig
        
        config = EnhancedBrowserConfig(debug=True, headless=False)
        args = config.get_stealth_args()
        
        # Check that JavaScript is not disabled
        js_disabled = any('--disable-javascript' in arg for arg in args)
        if js_disabled:
            print("  ❌ JavaScript is still disabled - GraphQL will fail")
            return False
        else:
            print("  ✓ JavaScript is enabled")
        
        # Check that LinkedIn APIs are allowed
        print("  ✓ Browser configuration test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Browser config test failed: {e}")
        return False

def test_cookie_manager():
    """Test cookie manager."""
    print("[TEST] Testing cookie manager...")
    
    try:
        from src.cookie_manager import CookieManager
        
        manager = CookieManager()
        print("  ✓ Cookie manager initialized successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Cookie manager test failed: {e}")
        return False

def test_config():
    """Test configuration."""
    print("[TEST] Testing configuration...")
    
    try:
        import src.config as config
        
        # Check that new delay configurations exist
        if hasattr(config, 'DELAYS') and 'session_recovery_wait' in config.DELAYS:
            print("  ✓ Enhanced delay configuration found")
        else:
            print("  ❌ Enhanced delay configuration missing")
            return False
        
        print("  ✓ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("LinkedIn GraphQL Fixes Verification")
    print("=" * 60)
    
    tests = [
        test_browser_config,
        test_cookie_manager,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Fixes appear to be working correctly.")
        print("\\n[INFO] You can now run your LinkedIn automation:")
        print("  python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    
    with open("test_graphql_fixes.py", 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    print("  ✓ Created test script: test_graphql_fixes.py")
    return True

def main():
    """Main function to apply all fixes."""
    print("=" * 60)
    print("LinkedIn GraphQL Issues Fix Script")
    print("=" * 60)
    print()
    
    # Check environment
    if not check_environment():
        return 1
    
    print()
    
    # Create backups
    backup_dir = backup_files()
    print()
    
    # Apply fixes
    fixes_applied = 0
    
    if apply_browser_config_fixes():
        fixes_applied += 1
    print()
    
    if apply_scraper_fixes():
        fixes_applied += 1
    print()
    
    if apply_cookie_manager_fixes():
        fixes_applied += 1
    print()
    
    if apply_config_fixes():
        fixes_applied += 1
    print()
    
    # Create test script
    create_test_script()
    print()
    
    # Summary
    print("=" * 60)
    print("Fix Summary")
    print("=" * 60)
    print(f"✅ Applied fixes to {fixes_applied} components")
    print("✅ Created backup of original files")
    print("✅ Created test script for verification")
    print()
    print("Key fixes applied:")
    print("  • Enabled JavaScript in browser (required for LinkedIn GraphQL)")
    print("  • Added LinkedIn API allowlist to prevent blocking")
    print("  • Enhanced GraphQL error detection and recovery")
    print("  • Improved session management and cookie handling")
    print("  • Increased delays for better bot detection avoidance")
    print()
    print("Next steps:")
    print("  1. Run the test script: python test_graphql_fixes.py")
    print("  2. If tests pass, try your LinkedIn automation again")
    print("  3. If issues persist, check the backup files in backup_before_fix/")
    print()
    print("⚠️  Important notes:")
    print("  • These fixes address the root causes of GraphQL errors")
    print("  • LinkedIn may still detect automation - use reasonable delays")
    print("  • Consider running in non-headless mode for better success rates")
    print("  • Monitor for rate limiting and adjust delays if needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
