from dotenv import load_dotenv
import os
import yaml

# Load environment variables from .env file
load_dotenv()

# ===== Login Info =====

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")



# ===== Optional Links =====
PORTFOLIO = os.getenv("PORTFOLIO", None)

# ===== Job Search Settings =====
MAX_JOBS = 10 # Default max jobs to scrape
# Automatically attempt LinkedIn Easy Apply after resume generation
AUTO_APPLY = True

# Default HTML template for resumes (stored in /templates/)
DEFAULT_TEMPLATE = os.getenv("DEFAULT_TEMPLATE", "base_resume.html")

# (Future) Add toggles for additional automation steps
# Example: ENABLE_EMAIL_NOTIFICATIONS, TRACK_APPLICATIONS, etc.

# Toggle verbose, in‑browser debugging pauses
DEBUG = True   # set to True when you want to step through in a visible browser
