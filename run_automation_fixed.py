#!/usr/bin/env python3
"""
Fixed LinkedIn Automation Runner

This script addresses the issues found in the previous run:
- Unicode encoding errors
- Debug pauses removed
- Better error handling for LinkedIn GraphQL errors
- Enhanced browser configuration

Usage:
    python run_automation_fixed.py

Environment Variables:
    HEADLESS_MODE=true          # Run in headless mode
    ENABLE_BROWSER_MONITORING=true  # Enable browser monitoring
    DEBUG=false                 # Disable debug mode (no pauses)
"""

import os
import sys
from pathlib import Path

# Set proper encoding for Windows
if sys.platform == "win32":
    import locale
    import codecs
    
    # Set UTF-8 encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Try to set UTF-8 locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass
    
    # Set stdout encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scraper import scrape_jobs_from_search
import src.config as config

def main():
    """Run fixed LinkedIn automation with all issues addressed."""
    
    print("🚀 Fixed LinkedIn Automation")
    print("=" * 50)
    
    # Set environment variables to avoid issues
    os.environ.setdefault("DEBUG", "false")  # Disable debug pauses
    os.environ.setdefault("HEADLESS_MODE", "false")  # Run with browser visible
    os.environ.setdefault("ENABLE_BROWSER_MONITORING", "false")  # Disable monitoring for now
    
    # Check environment variables
    headless_mode = os.getenv("HEADLESS_MODE", "false").lower() == "true"
    browser_monitoring = os.getenv("ENABLE_BROWSER_MONITORING", "false").lower() == "true"
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"📋 Configuration:")
    print(f"   • Headless Mode: {headless_mode}")
    print(f"   • Browser Monitoring: {browser_monitoring}")
    print(f"   • Debug Mode: {debug_mode}")
    print(f"   • Encoding: {sys.stdout.encoding}")
    print()
    
    # Check required credentials
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        print("❌ Error: LinkedIn credentials not found!")
        print("   Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
        print("   or add them to your .env file")
        return 1
    
    # Example search URL (you can modify this)
    search_url = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=United%20States"
    
    print(f"🔍 Searching for jobs: {search_url}")
    print()
    
    try:
        # Run the enhanced automation
        jobs_data = scrape_jobs_from_search(
            search_url=search_url,
            email=config.LINKEDIN_EMAIL,
            password=config.LINKEDIN_PASSWORD,
            max_jobs=3,  # Limit for testing
            personal_info_path="personal_info.yaml"
        )
        
        print(f"\n✅ Automation completed!")
        print(f"📊 Results: {len(jobs_data)} jobs processed")
        
        # Show results summary
        if jobs_data:
            print("\n📋 Job Results:")
            for i, job in enumerate(jobs_data, 1):
                print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"      Status: {job.get('apply_status', 'N/A')}")
                if job.get('pdf_path'):
                    print(f"      Resume: {job['pdf_path']}")
                print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Automation stopped by user")
        return 1
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


