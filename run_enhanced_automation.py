#!/usr/bin/env python3
"""
Enhanced LinkedIn Automation Runner

This script demonstrates the new enhanced browser configuration features:
- Clean browser profile
- Extension blocking
- Headless mode support
- Better error handling for blocked resources

Usage:
    python run_enhanced_automation.py

Environment Variables:
    HEADLESS_MODE=true          # Run in headless mode
    ENABLE_BROWSER_MONITORING=true  # Enable browser monitoring
    DEBUG=true                  # Enable debug mode
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scraper import scrape_jobs_from_search
import src.config as config

def main():
    """Run enhanced LinkedIn automation with new features."""
    
    print("🚀 Enhanced LinkedIn Automation")
    print("=" * 50)
    
    # Check environment variables
    headless_mode = os.getenv("HEADLESS_MODE", "false").lower() == "true"
    browser_monitoring = os.getenv("ENABLE_BROWSER_MONITORING", "false").lower() == "true"
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"📋 Configuration:")
    print(f"   • Headless Mode: {headless_mode}")
    print(f"   • Browser Monitoring: {browser_monitoring}")
    print(f"   • Debug Mode: {debug_mode}")
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
            max_jobs=5,  # Limit for demo
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
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


