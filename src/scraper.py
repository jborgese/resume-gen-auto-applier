# src/scraper.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from src.utils import clean_text, scroll_job_list
import time
from src.keyword_extractor import extract_keywords
from src.keyword_weighting import weigh_keywords

def scrape_jobs_from_search(search_url: str, email: str, password: str, max_jobs: int = 5) -> list:
    """
    Logs into LinkedIn, scrapes job listings from a search URL, and returns a list of job data dicts.
    Uses job card IDs (data-job-id) for clean URLs, handles metro area locations, and pauses on first job for debugging.
    """
    jobs_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set True for silent/headless mode
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"[INFO] Navigating to LinkedIn login page…")
            page.goto("https://www.linkedin.com/login", timeout=30000)

            # === LOGIN ===
            page.fill('input[id="username"]', email)
            page.fill('input[id="password"]', password)
            page.click('button[type="submit"]')

            try:
                page.wait_for_selector('input[placeholder="Search"]', timeout=30000)
                print("[INFO] ✅ Logged into LinkedIn successfully.")
            except PlaywrightTimeout:
                print("[ERROR] ❌ Login issue (captcha/MFA?). Exiting.")
                return []

            # === NAVIGATE TO JOB SEARCH ===
            print(f"[INFO] Navigating to job search URL: {search_url}")
            page.goto(search_url, timeout=45000)

            # ✅ SCROLL if needed
            job_list_selector = 'ul.semantic-search-results-list'
            if page.locator(job_list_selector).count() == 0:
                print("[WARNING] ⚠️ Could not find job list container — scrolling page fallback.")
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(2)
            else:
                print(f"[INFO] ✅ Job list container detected: {job_list_selector}")
                scroll_job_list(page, rounds=5, delay=2)

            # ✅ COLLECT JOB IDS FROM LIST ITEMS
            job_items = page.locator(f'{job_list_selector} li')
            total_items = job_items.count()
            print(f"[INFO] 📄 Found {total_items} job cards in sidebar.")

            if total_items == 0:
                print("[WARNING] ⚠️ No job cards found even after scrolling. Exiting.")
                return []

            job_links = []
            for i in range(total_items):
                wrapper = job_items.nth(i).locator('div.job-card-job-posting-card-wrapper')
                if wrapper.count():
                    job_id = wrapper.get_attribute('data-job-id')
                    if job_id:
                        job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                        if job_url not in job_links:
                            job_links.append(job_url)
                            print(f"[INFO] ✅ Found job URL: {job_url}")

                if len(job_links) >= max_jobs:
                    break

            print(f"[INFO] Preparing to scrape details for {len(job_links)} jobs (limit: {max_jobs}).")

            # ✅ SCRAPE EACH JOB PAGE
            for idx, job_url in enumerate(job_links, start=1):
                print(f"\n[INFO] Opening job {idx}/{len(job_links)}: {job_url}")
                job_page = context.new_page()
                job_page.goto(job_url, timeout=30000)

                try:
                    job_page.wait_for_selector('h1', timeout=15000)
                except PlaywrightTimeout:
                    print("[WARNING] ⚠️ Job page didn’t load properly. Skipping.")
                    job_page.close()
                    continue

                # # 🛑 DEBUG PAUSE ON FIRST JOB
                # if idx == 1:
                #     print("\n[DEBUG] 🔍 Pausing for inspection of the first job page.")
                #     input("👉 Press Enter in terminal to continue scraping...")

                job_data = {
                    "title": "N/A",
                    "company": "N/A",
                    "location": "N/A",
                    "description": "N/A",
                    "url": job_url,
                    "keywords": []  # ✅ avoids KeyError in main.py
                }

                # === TITLE ===
                if job_page.locator('h1.t-24.t-bold.inline').count():
                    job_data["title"] = job_page.inner_text('h1.t-24.t-bold.inline').strip()
                else:
                    print("[WARNING] ⚠️ Unable to retrieve job title.")

                # === COMPANY ===
                if job_page.locator('div.job-details-jobs-unified-top-card__company-name a').count():
                    job_data["company"] = job_page.inner_text('div.job-details-jobs-unified-top-card__company-name a').strip()
                else:
                    print("[WARNING] ⚠️ Unable to retrieve company name.")

                # === LOCATION (City, State or Metro Area) ===
                location_candidates = job_page.locator('span.tvm__text.tvm__text--low-emphasis').all_inner_texts()
                found_location = False
                for loc in location_candidates:
                    clean_loc = loc.strip()
                    if "," in clean_loc:  # Normal city/state
                        job_data["location"] = clean_loc
                        found_location = True
                        break
                    elif "Metropolitan Area" in clean_loc:  # Metro area special case
                        job_data["location"] = clean_loc
                        found_location = True
                        print(f"[INFO] 📍 Detected metro area location: {clean_loc}")
                        break
                if not found_location:
                    print("[WARNING] ⚠️ Unable to retrieve job location.")

                # === DESCRIPTION ===
                if job_page.locator('div.jobs-description__content').count():
                    raw_desc = job_page.inner_text('div.jobs-description__content').strip()
                    print(f"[INFO] 📝 Raw job description captured ({len(raw_desc)} chars).")
                    
                    cleaned_desc = clean_text(raw_desc)
                    
                    if cleaned_desc != raw_desc:
                        print(f"[INFO] ✨ Description cleaned — reduced from {len(raw_desc)} to {len(cleaned_desc)} chars.")
                    else:
                        print(f"[INFO] ✅ Description required no cleaning.")
                    
                    # ✅ Store the cleaned description
                    job_data["description"] = cleaned_desc

                    # ✅ Extract keywords from description
                    extracted_keywords = extract_keywords(cleaned_desc)
                    extracted = extract_keywords(cleaned_desc)
                    weighted = weigh_keywords(cleaned_desc, extracted)

                    # store BOTH (in case we need both later)
                    job_data["keywords"] = [kw for kw, _ in weighted]  # sorted keyword list
                    job_data["keyword_weights"] = weighted  # (keyword, score) tuples for deeper logic
                    print(f"[INFO] 📌 Extracted keywords: {extracted_keywords}")
                else:
                    print("[WARNING] ⚠️ Unable to retrieve job description.")
                    job_data["keywords"] = []

                print(f"[SCRAPED] ✅ {job_data['title']} at {job_data['company']} — {job_data['location']}")
                jobs_data.append(job_data)
                job_page.close()

        except Exception as e:
            print(f"[FATAL] 🚨 Unexpected error during scraping: {e}")
        finally:
            browser.close()

    return jobs_data