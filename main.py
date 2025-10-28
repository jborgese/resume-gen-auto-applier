import json
import yaml
import sys
import os
from pathlib import Path

# Initialize structured logging first
from src.logging_config import initialize_logging, get_logger, debug_stop, debug_checkpoint, debug_skip_stops
initialize_logging()
logger = get_logger(__name__)

# Debug checkpoint at application start
debug_checkpoint("application_start", 
                python_version=sys.version,
                working_directory=str(Path.cwd()))

# Debug stop before application initialization
if not debug_skip_stops():
    debug_stop("About to start resume generator application", 
              python_version=sys.version,
              working_directory=str(Path.cwd()))

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

# Debug checkpoint before loading configuration files
debug_checkpoint("loading_config_files")

# Load personal_info for resume headers and experiences
with open("personal_info.yaml", "r", encoding="utf-8") as f:
    personal_info = yaml.safe_load(f)

# Debug checkpoint after loading personal info
debug_checkpoint("personal_info_loaded", 
                personal_info_keys=list(personal_info.keys()) if personal_info else [])

# Load stopwords if needed
STOPWORDS = set()
try:
    with open("stopwords.json", "r", encoding="utf-8") as f:
        STOPWORDS = set(json.load(f))
        logger.info("Loaded stopwords", count=len(STOPWORDS))
        debug_checkpoint("stopwords_loaded", stopwords_count=len(STOPWORDS))
except FileNotFoundError:
    logger.warning("No stopwords.json found - skipping stopword filtering")
    debug_checkpoint("stopwords_not_found")

if __name__ == "__main__":
    # Debug checkpoint at main execution start
    debug_checkpoint("main_execution_start")
    
    logger.info("Using resume template", template=config.DEFAULT_TEMPLATE)

    # Debug stop before credential validation
    if not debug_skip_stops():
        debug_stop("About to validate LinkedIn credentials", 
                  linkedin_email_set=bool(config.LINKEDIN_EMAIL),
                  linkedin_password_set=bool(config.LINKEDIN_PASSWORD))

    # Validate LinkedIn credentials
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        raise ValueError("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")

    # Debug checkpoint after credential validation
    debug_checkpoint("credentials_validated")

    # LinkedIn job search URL
    search_url = (
        "https://www.linkedin.com/jobs/search-results/"
        "?f_AL=true&keywords=Software%20Engineer&origin=JOBS_HOME_SEARCH_BUTTON"
    )

    # Debug stop before job scraping
    if not debug_skip_stops():
        debug_stop("About to start job scraping", 
                  search_url=search_url,
                  max_jobs=config.MAX_JOBS,
                  auto_apply=config.AUTO_APPLY)

    # Debug checkpoint before job scraping
    debug_checkpoint("job_scraping_start", 
                    search_url=search_url,
                    max_jobs=config.MAX_JOBS)

    # Scrape jobs (scrapes, builds resumes, and optionally applies)
    jobs = scrape_jobs_from_search(
        search_url,
        config.LINKEDIN_EMAIL,
        config.LINKEDIN_PASSWORD,
        max_jobs=config.MAX_JOBS
    )

    # Debug checkpoint after job scraping
    debug_checkpoint("job_scraping_complete", 
                    jobs_processed=len(jobs) if jobs else 0)

    if not jobs:
        logger.warning("No jobs processed")
        debug_checkpoint("no_jobs_processed")
        exit(0)

    logger.info("Completed processing jobs", job_count=len(jobs))

    # Debug checkpoint before job summary
    debug_checkpoint("job_summary_start", job_count=len(jobs))

    for idx, job in enumerate(jobs, start=1):
        title   = job.get("title", "N/A")
        company = job.get("company", "N/A")
        pdf     = job.get("resume_pdf", "")
        status  = job.get("apply_status", "skipped")
        logger.info("Job summary", 
                   job_index=idx, 
                   title=title, 
                   company=company, 
                   resume_pdf=pdf, 
                   apply_status=status)

    # Debug checkpoint at application completion
    debug_checkpoint("application_complete", 
                    total_jobs_processed=len(jobs))

    logger.info("All done - processing complete")
