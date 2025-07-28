from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
from src.utils import clean_text  # ✅ add this


def scrape_job_description(job_url: str, email: str, password: str) -> dict:
    """
    Uses Playwright to log into LinkedIn and scrape job details.

    :param job_url: LinkedIn job posting URL
    :param email: LinkedIn login email
    :param password: LinkedIn login password
    :return: dict with job title, company, location, and description
    """
    job_data = {
        "title": "N/A",
        "company": "N/A",
        "location": "N/A",
        "description": "N/A"
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # flip to True for silent automation
            context = browser.new_context()
            page = context.new_page()

            print("[INFO] Navigating to LinkedIn login page...")
            page.goto("https://www.linkedin.com/login", timeout=30000)

            try:
                page.fill('input[id="username"]', email)
                page.fill('input[id="password"]', password)
                page.click('button[type="submit"]')
            except PlaywrightTimeout:
                print("[ERROR] Login fields not found — LinkedIn may have changed its login page.")
                return job_data

            # ✅ Wait for the search bar OR captcha challenge
            try:
                page.wait_for_selector('input[placeholder="Search"]', timeout=15000)
                print("[INFO] Logged into LinkedIn successfully.")
            except PlaywrightTimeout:
                print("[WARNING] Login might have been interrupted (captcha, MFA, or slow load).")
                if page.locator('input[aria-label="Please solve this puzzle"]').count():
                    print("[ERROR] LinkedIn presented a CAPTCHA — manual intervention required.")
                return job_data

            # ✅ Navigate to the job posting
            print(f"[INFO] Navigating to job posting: {job_url}")
            page.goto(job_url, timeout=30000)

            # ✅ Wait for *any* H1 (instead of old selector that caused early return)
            try:
                page.wait_for_selector('h1', timeout=15000)
                print("[INFO] At least one H1 tag detected on job page.")
            except PlaywrightTimeout:
                print("[ERROR] No H1 tag loaded on job page — check the job URL or LinkedIn DOM.")
                return job_data

            time.sleep(2)  # allow lazy-loading

            # 🔍 DEBUG: Print all H1s to confirm the job title is visible
            print("[DEBUG] All H1 tags on page:")
            for h1_text in page.locator("h1").all_inner_texts():
                print(f" - {h1_text}")

            # === Scrape job title (with fallbacks) ===
            title_selectors = [
                'h1.t-24.t-bold.inline',                   # ✅ new LinkedIn DOM
                'h1.jobs-unified-top-card__job-title',     # older LinkedIn layout
                'h1.top-card-layout__title',               # legacy LinkedIn layout
                'h1'                                       # final fallback
            ]

            for selector in title_selectors:
                if page.locator(selector).count():
                    job_data["title"] = page.inner_text(selector).strip()
                    print(f"[INFO] Found job title using selector: {selector}")
                    break
            else:
                print("[WARNING] Could not locate job title with known selectors.")

            # 🔍 DEBUG: Print the job card section text for company & location
            print("[DEBUG] Inspecting job card top section:")
            for div_text in page.locator("div.job-details-jobs-unified-top-card").all_inner_texts():
                print(f" - {div_text}")

            # === Scrape company ===
            company_selectors = [
                'div.job-details-jobs-unified-top-card__company-name a',  # ✅ New DOM (from screenshot)
                'a.jobs-unified-top-card__company-name',                  # Fallback
                'a.topcard__org-name-link'                                # Legacy LinkedIn
            ]

            for selector in company_selectors:
                if page.locator(selector).count():
                    job_data["company"] = page.inner_text(selector).strip()
                    print(f"[INFO] Found company using selector: {selector}")
                    break
            else:
                print("[WARNING] Company name not found with known selectors.")

            # === Scrape location ===
            all_spans = page.locator('div.job-details-jobs-unified-top-card__tertiary-description-container span.tvm__text').all_inner_texts()

            for text in all_spans:
                # Look for text that matches "City, State" format (basic heuristic: has a comma and no numbers)
                if "," in text and not any(char.isdigit() for char in text):
                    job_data["location"] = text.strip()
                    print(f"[INFO] Found location: {job_data['location']}")
                    break
            else:
                print("[WARNING] Location not found using location heuristic.")

            # === Scrape job description ===
            description_selectors = [
                'div.jobs-description__content',          
                'div.description__text'                   
            ]

            for selector in description_selectors:
                if page.locator(selector).count():
                    raw_description = page.inner_text(selector).strip()
                    job_data["description"] = clean_text(raw_description)  # ✅ use helper
                    print(f"[INFO] Found job description using selector: {selector}")
                    break

            print("[INFO] Scraping complete.")
            browser.close()

    except PlaywrightTimeout:
        print("[FATAL] Playwright timed out during page load — check your internet connection.")
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")

    return job_data