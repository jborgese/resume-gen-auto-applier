import json
import yaml
import sys
import os
from pathlib import Path

# Redirect stderr to filter GLib warnings before any imports
class GLibWarningFilter:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
    
    def write(self, text):
        # Filter out GLib-GIO warnings
        if 'GLib-GIO-WARNING' not in text and 'UWP app' not in text:
            self.original_stderr.write(text)
            self.original_stderr.flush()
    
    def flush(self):
        self.original_stderr.flush()

# Apply the filter
sys.stderr = GLibWarningFilter(sys.stderr)

# Suppress GLib-GIO warnings before any other imports
from src.glib_suppression import suppress_glib_warnings
suppress_glib_warnings()

import src.config as config
from src.scraper import scrape_jobs_from_search

# Load personal_info for resume headers and experiences
with open("personal_info.yaml", "r", encoding="utf-8") as f:
    personal_info = yaml.safe_load(f)

# Load stopwords if needed
STOPWORDS = set()
try:
    with open("stopwords.json", "r", encoding="utf-8") as f:
        STOPWORDS = set(json.load(f))
        print(f"[INFO] Loaded {len(STOPWORDS)} stopwords.")
except FileNotFoundError:
    print("[WARNING] No stopwords.json found - skipping stopword filtering.")

if __name__ == "__main__":
    print(f"[INFO] Using resume template: {config.DEFAULT_TEMPLATE}")

    # Validate LinkedIn credentials
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        raise ValueError("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")

    # LinkedIn job search URL
    search_url = (
        "https://www.linkedin.com/jobs/search-results/"
        "?f_AL=true&keywords=Software%20Engineer&origin=JOBS_HOME_SEARCH_BUTTON"
    )

    # Scrape jobs (scrapes, builds resumes, and optionally applies)
    jobs = scrape_jobs_from_search(
        search_url,
        config.LINKEDIN_EMAIL,
        config.LINKEDIN_PASSWORD,
        max_jobs=config.MAX_JOBS
    )

    if not jobs:
        print("[WARNING] No jobs processed.")
        exit(0)

    print(f"[INFO] Completed processing {len(jobs)} job(s). Summary:\n")

    for idx, job in enumerate(jobs, start=1):
        title   = job.get("title", "N/A")
        company = job.get("company", "N/A")
        pdf     = job.get("resume_pdf", "")
        status  = job.get("apply_status", "skipped")
        print(f" Job {idx}: {title} @ {company}")
        print(f"   • Resume → {pdf}")
        print(f"   • Apply   → {status}\n")

    print("[COMPLETE] All done.")
