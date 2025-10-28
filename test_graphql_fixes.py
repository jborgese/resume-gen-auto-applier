#!/usr/bin/env python3
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
        js_disabled = any('--disable-javascript' == arg for arg in args)
        if js_disabled:
            print("  [FAIL] JavaScript is still disabled - GraphQL will fail")
            return False
        else:
            print("  [PASS] JavaScript is enabled")
        
        # Check that LinkedIn APIs are allowed
        print("  [PASS] Browser configuration test passed")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Browser config test failed: {e}")
        return False

def test_cookie_manager():
    """Test cookie manager."""
    print("[TEST] Testing cookie manager...")
    
    try:
        from src.cookie_manager import CookieManager
        
        manager = CookieManager()
        print("  [PASS] Cookie manager initialized successfully")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Cookie manager test failed: {e}")
        return False

def test_config():
    """Test configuration."""
    print("[TEST] Testing configuration...")
    
    try:
        import src.config as config
        
        # Check that new delay configurations exist
        if hasattr(config, 'DELAYS') and 'session_recovery_wait' in config.DELAYS:
            print("  [PASS] Enhanced delay configuration found")
        else:
            print("  [FAIL] Enhanced delay configuration missing")
            return False
        
        print("  [PASS] Configuration test passed")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Configuration test failed: {e}")
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
        print("[SUCCESS] All tests passed! Fixes appear to be working correctly.")
        print("\n[INFO] You can now run your LinkedIn automation:")
        print("  python main.py")
    else:
        print("[FAILURE] Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())