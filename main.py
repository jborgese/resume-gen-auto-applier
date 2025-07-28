from src.resume_builder import build_resume
import src.config as config
from pathlib import Path
from src.scraper import scrape_job_description
import src.config as config

if __name__ == "__main__":
    # Log what template is being used (from .env)
    print(f"[INFO] Using resume template: {config.DEFAULT_TEMPLATE}")
    job_url = "https://www.linkedin.com/jobs/view/4263376109"  # replace with real job link
    if config.LINKEDIN_EMAIL is None or config.LINKEDIN_PASSWORD is None:
        raise ValueError("LinkedIn email and password must be set in the configuration.")
    job_data = scrape_job_description(job_url, config.LINKEDIN_EMAIL, config.LINKEDIN_PASSWORD)
    print(job_data)

    # Build the data dictionary for the resume
    resume_data = {
        "name": config.NAME,
        "email": config.EMAIL,
        "phone": config.PHONE,
        "linkedin": config.LINKEDIN,
        "summary": "Software developer with expertise in backend systems, automation, and CI/CD pipelines.",
        "skills": [
            "Python", "Playwright", "LLM Integration", "Docker", "GitHub Actions", "NLP"
        ],
        "experiences": [
            {
                "role": "Software Developer",
                "company": "Digital Bounty",
                "years": "2021–Present",
                "desc": "Developed backend systems, integrated CI/CD pipelines, and automated key workflows."
            },
            {
                "role": "Product Manager",
                "company": "Startup XYZ",
                "years": "2019–2021",
                "desc": "Led cross-functional teams, defined product roadmaps, and launched MVP to market."
            }
        ],
        "matched_keywords": ["Python", "Automation", "CI/CD", "LinkedIn Easy Apply"]
    }

    # Generate the PDF resume
    resume_path = build_resume(resume_data)

    # Inform the user where the PDF was saved
    print(f"[SUCCESS] Resume generated: {resume_path}")

    # Handle auto-apply logic based on .env setting
    if config.AUTO_APPLY:
        print("[INFO] Auto Apply is enabled — starting LinkedIn Easy Apply automation...")
        # Placeholder for future Playwright automation
        # from src.easy_apply import easy_apply_linkedin
        # easy_apply_linkedin(job_url, resume_path)
    else:
        print("[INFO] Auto Apply is disabled — skipping automated application.")
