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
# Automatically attempt LinkedIn Easy Apply after resume generation
AUTO_APPLY = os.getenv("AUTO_APPLY", "false").lower() in ("true", "1", "yes")

# Default HTML template for resumes (stored in /templates/)
DEFAULT_TEMPLATE = os.getenv("DEFAULT_TEMPLATE", "base_resume.html")

# (Future) Add toggles for additional automation steps
# Example: ENABLE_EMAIL_NOTIFICATIONS, TRACK_APPLICATIONS, etc.
