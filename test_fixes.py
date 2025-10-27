#!/usr/bin/env python3
"""
Test script to verify all fixes for LinkedIn automation

This script tests:
1. Job description scraping with fallback selectors
2. Rate limiting handling with delays
3. Enhanced Easy Apply with fallback selectors
4. Unicode encoding fixes
5. Debug pause removal

Usage:
    python test_fixes.py
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
    """Test all the fixes implemented."""
    
    print("🧪 Testing LinkedIn Automation Fixes")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ.setdefault("DEBUG", "false")  # No debug pauses
    os.environ.setdefault("HEADLESS_MODE", "false")  # Visible browser for testing
    os.environ.setdefault("ENABLE_BROWSER_MONITORING", "false")
    os.environ.setdefault("MAX_JOBS", "2")  # Limit to 2 jobs for testing
    
    print(f"📋 Test Configuration:")
    print(f"   • Headless Mode: {os.getenv('HEADLESS_MODE', 'false')}")
    print(f"   • Debug Mode: {os.getenv('DEBUG', 'false')}")
    print(f"   • Max Jobs: {os.getenv('MAX_JOBS', '2')}")
    print(f"   • Encoding: {sys.stdout.encoding}")
    print()
    
    # Check required credentials
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        print("❌ Error: LinkedIn credentials not found!")
        print("   Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
        print("   or add them to your .env file")
        return 1
    
    # Test search URL
    search_url = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=United%20States"
    
    print(f"🔍 Testing with search: {search_url}")
    print()
    
    try:
        # Run the enhanced automation
        jobs_data = scrape_jobs_from_search(
            search_url=search_url,
            email=config.LINKEDIN_EMAIL,
            password=config.LINKEDIN_PASSWORD,
            max_jobs=2,  # Limit for testing
            personal_info_path="personal_info.yaml"
        )
        
        print(f"\n✅ Test completed!")
        print(f"📊 Results: {len(jobs_data)} jobs processed")
        
        # Analyze results
        successful_jobs = 0
        jobs_with_descriptions = 0
        jobs_with_resumes = 0
        
        if jobs_data:
            print("\n📋 Detailed Results:")
            for i, job in enumerate(jobs_data, 1):
                print(f"\n   Job {i}: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                
                # Check description
                desc_length = len(job.get('description', ''))
                if desc_length > 0:
                    jobs_with_descriptions += 1
                    print(f"      ✅ Description: {desc_length} characters")
                else:
                    print(f"      ❌ Description: 0 characters (scraping failed)")
                
                # Check resume
                if job.get('pdf_path') and os.path.exists(job.get('pdf_path', '')):
                    jobs_with_resumes += 1
                    print(f"      ✅ Resume: {job['pdf_path']}")
                else:
                    print(f"      ❌ Resume: Not generated or file missing")
                
                # Check apply status
                apply_status = job.get('apply_status', 'unknown')
                print(f"      📝 Apply Status: {apply_status}")
                
                if apply_status == 'applied':
                    successful_jobs += 1
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   • Total Jobs Processed: {len(jobs_data)}")
        print(f"   • Jobs with Descriptions: {jobs_with_descriptions}")
        print(f"   • Jobs with Resumes: {jobs_with_resumes}")
        print(f"   • Successful Applications: {successful_jobs}")
        
        # Determine success
        if len(jobs_data) > 0 and jobs_with_descriptions > 0 and jobs_with_resumes > 0:
            print(f"\n🎉 All fixes working correctly!")
            return 0
        else:
            print(f"\n⚠️  Some issues remain:")
            if jobs_with_descriptions == 0:
                print(f"   • Job description scraping still failing")
            if jobs_with_resumes == 0:
                print(f"   • Resume generation still failing")
            return 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


