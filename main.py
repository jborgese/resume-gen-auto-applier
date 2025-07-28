# main.py
from src.scraper import scrape_job_description
from src.keyword_extractor import extract_keywords
from src.resume_builder import build_resume
from src.easy_apply import easy_apply_linkedin

def main(job_url):
    print(f"[INFO] Scraping job listing: {job_url}")
    job_data = scrape_job_description(job_url)

    print("[INFO] Extracting keywords...")
    keywords = extract_keywords(job_data["description"])

    print("[INFO] Building tailored resume...")
    resume_path = build_resume(keywords)

    print("[INFO] Optional: Easy Apply automation...")
    easy_apply_linkedin(job_url, resume_path)

if __name__ == "__main__":
    # Temporary: hardcoded test job
    job_url = "https://www.linkedin.com/jobs/view/1234567890"
    main(job_url)
