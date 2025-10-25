# src/scraper.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright._impl._errors import TargetClosedError
from src.utils import clean_text, normalize_skill, collect_job_links_with_pagination
from src.keyword_extractor import extract_keywords
from src.keyword_weighting import weigh_keywords
from src.resume_builder import build_resume
from src.easy_apply import apply_to_job
from src.llm_summary import generate_resume_summary
import src.config as config
from src.config import MAX_JOBS
from typing import Optional
import yaml
import json
import time

def scrape_jobs_from_search(
    search_url: str,
    email: str,
    password: str,
    max_jobs: Optional[int] = None,
    personal_info_path: str = "personal_info.yaml"
) -> list:
    """
    Logs into LinkedIn, scrapes job listings from a search URL,
    tailors + builds a resume PDF (with personal_info.yaml fields),
    then (if enabled) runs Easy Apply on each job.
    Returns a list of job_data dicts including paths to generated PDFs.

    Args:
        search_url (str): LinkedIn job search URL.
        email (str): LinkedIn login email.
        password (str): LinkedIn login password.
        max_jobs (Optional[int]): Maximum number of jobs to scrape.
        personal_info_path (str): Path to the personal_info.yaml file.
    """
    # Use default max if not provided
    if max_jobs is None:
        max_jobs = MAX_JOBS

        # - LOGIN -

    # Start Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not config.DEBUG)
        context = browser.new_context()
        page = context.new_page()

        # — LOGIN —
        print("[INFO] Navigating to LinkedIn login page…")
        page.goto("https://www.linkedin.com/login", timeout=config.TIMEOUTS["login"])
        print("[INFO] Entering credentials…")
        page.fill(config.LINKEDIN_SELECTORS["login"]["username"], email)
        page.fill(config.LINKEDIN_SELECTORS["login"]["password"], password)
        page.click(config.LINKEDIN_SELECTORS["login"]["submit"])
        
        # Give LinkedIn a moment to process the login
        time.sleep(config.DELAYS["login_processing"])
        
        # Check for login success using multiple methods
        login_detected = False
        
        try:
            # Method 1: Check URL - if we're redirected away from login page, likely successful
            current_url = page.url
            if "/login" not in current_url and ("linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url):
                print(f"[INFO] ✅ Logged in successfully (URL redirect detected: {current_url}).")
                login_detected = True
            
            # Method 2: Check page title
            elif not login_detected:
                page_title = page.title()
                if "Feed" in page_title or "LinkedIn" in page_title and "Sign In" not in page_title:
                    print(f"[INFO] ✅ Logged in successfully (page title indicates success: '{page_title}').")
                    login_detected = True
            
            # Method 3: Try common selectors as fallback
            if not login_detected:
                login_success_selectors = config.LINKEDIN_SELECTORS["login_success"]
                
                for selector in login_success_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=config.TIMEOUTS["login_success"])
                        print(f"[INFO] ✅ Logged in successfully (detected via: {selector}).")
                        login_detected = True
                        break
                    except PlaywrightTimeout:
                        continue
            
            # If still no success, check for error conditions
            if not login_detected:
                # Check for common error indicators
                if page.locator('div.challenge').count() > 0:
                    print("[ERROR] ❌ Login blocked by security challenge/CAPTCHA. Please log in manually first.")
                elif page.locator('[data-test-id="sign-in-error"]').count() > 0:
                    print("[ERROR] ❌ Invalid credentials. Please check your LINKEDIN_EMAIL and LINKEDIN_PASSWORD.")
                elif page.locator('.form__input--error').count() > 0:
                    print("[ERROR] ❌ Login form error detected. Please check your credentials.")
                elif "/login" in page.url:
                    print("[ERROR] ❌ Still on login page - credentials may be incorrect or CAPTCHA required.")
                else:
                    print("[ERROR] ❌ Login failed - unable to detect successful login. This could be due to:")
                    print("         • CAPTCHA/MFA challenge")
                    print("         • Invalid credentials") 
                    print("         • LinkedIn UI changes")
                    print("         • Rate limiting")
                
                if config.DEBUG:
                    print(f"[DEBUG] Current URL: {page.url}")
                    print(f"[DEBUG] Page title: {page.title()}")
                    print("[DEBUG] Press Enter to continue or Ctrl+C to exit...")
                    input()
                
                return []
                
        except Exception as e:
            print(f"[ERROR] ❌ Unexpected error during login: {e}")
            return []

        # — GO TO SEARCH PAGE —
        print(f"[INFO] Navigating to job search URL: {search_url}")
        page.goto(search_url, timeout=config.TIMEOUTS["search_page"])
        if config.DEBUG:
            print("\n[DEBUG] Search page loaded. Verify jobs list is visible in the browser.")

        # — SCROLL TO LOAD ALL JOBS —
        print("[INFO] Collecting jobs using pagination…")
        job_links = collect_job_links_with_pagination(page, search_url, max_jobs)
        if not job_links:
            print("[WARNING] ⚠️ No jobs found after pagination. Exiting.")
            return []

        print(f"[INFO] ✅ Collected {len(job_links)} job URLs during pagination.")

        if config.DEBUG:
            print("\n[DEBUG] Collected job URLs:")
            for u in job_links:
                print("   ", u)
            input("Press Enter to begin scraping job details…")


        # — LOAD PERSONAL INFO YAML ONCE —
        try:
            with open(personal_info_path, "r", encoding="utf-8") as f:
                personal_info = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[ERROR] personal_info.yaml not found at '{personal_info_path}'. Exiting.")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to load personal_info.yaml: {e}")
            return []

        # Construct a single-line address
        addr = personal_info.get("address", {})
        city = addr.get("city")
        state = addr.get("state")
        zip_code = str(addr.get("zip")) if addr.get("zip") is not None else None
        city_state_zip = " ".join(filter(None, [state, zip_code]))
        city_state_zip = ", ".join(filter(None, [city, city_state_zip])) if city or city_state_zip else ""
        address = ", ".join(filter(None, [
            addr.get("street"),
            city_state_zip,
            addr.get("country")
        ]))
        # Map job_history → experiences list (keep bullet points intact)
        experiences = []
        for entry in personal_info.get("job_history", []):
            experiences.append({
                "role": entry.get("title", ""),
                "company": entry.get("company", ""),
                "location": entry.get("location", ""),  # ✅ Include location
                "years": f"{entry.get('start_date','')}–{entry.get('end_date','')}",
                "responsibilities": entry.get("responsibilities", [])  # ✅ Keep as list for bullet points
            })


        # Education & references
        education  = personal_info.get("education", [])
        references = personal_info.get("references", [])

        # — SCRAPE, BUILD & APPLY LOOP —
        jobs_data = []  
        for idx, job_url in enumerate(job_links, start=1):
            print(f"\n[INFO] [{idx}/{len(job_links)}] Opening job page: {job_url}")

            try:
                # ✅ Open a fresh page for each job to avoid TargetClosedError
                job_page = context.new_page()

                try:
                    job_page.goto(job_url, timeout=config.TIMEOUTS["job_page"])
                except TargetClosedError:
                    print(f"[WARN] LinkedIn closed the tab unexpectedly for {job_url}. Skipping.")
                    continue
                except PlaywrightTimeout:
                    print(f"[WARN] Timeout loading {job_url}. Skipping.")
                    continue

                # ✅ Detect expired/unavailable job
                if job_page.locator(config.LINKEDIN_SELECTORS["job_detail"]["unavailable"]).count():
                    print(f"[INFO] Job {job_url} is unavailable or expired. Skipping.")
                    job_page.close()
                    continue

                job_page.wait_for_selector("h1", timeout=config.TIMEOUTS["job_title"])

                # --- SCRAPE METADATA ---
                title_sel = ",".join(config.LINKEDIN_SELECTORS["job_detail"]["title"])
                titles = job_page.locator(title_sel).all_inner_texts()
                title = titles[0].strip() if titles else "N/A"

                comp_sel = ",".join(config.LINKEDIN_SELECTORS["job_detail"]["company"])
                comps = job_page.locator(comp_sel).all_inner_texts()
                company = comps[0].strip() if comps else "N/A"

                locs = job_page.locator(config.LINKEDIN_SELECTORS["job_detail"]["location"]).all_inner_texts()
                location = "N/A"
                for loc in locs:
                    clean_loc = loc.strip()
                    if "," in clean_loc or "Metropolitan Area" in clean_loc:
                        location = clean_loc
                        break

                # ✅ Description (scraped ONCE)
                raw_desc = job_page.inner_text(config.LINKEDIN_SELECTORS["job_detail"]["description"]).strip() if job_page.locator(config.LINKEDIN_SELECTORS["job_detail"]["description"]).count() else ""
                desc = clean_text(raw_desc)
                print(f"  [INFO] Description captured ({len(raw_desc)} → {len(desc)} chars after cleaning)")

                # ✅ Extract & weight keywords
                kws = extract_keywords(desc)
                weighted = weigh_keywords(desc, kws)
                extracted = [kw for kw, _ in weighted]
                print(f"  [INFO] Extracted {len(extracted)} keywords.")

                # ✅ LLM summary + skills
                raw_summary = generate_resume_summary(title, company, desc)
                try:
                    parsed = json.loads(raw_summary)
                except json.JSONDecodeError as e:
                    print(f"  [ERROR] ❌ LLM returned invalid JSON for {title} @ {company}: {e}")
                    print(f"  [DEBUG] Raw summary was: {raw_summary}")
                    print("  [SKIP] Skipping this job because summary couldn’t be parsed.")
                    job_page.close()
                    continue   # 🚨 SKIP this job entirely

                summary_text = parsed.get("summary", "").strip()
                llm_skills  = [kw.strip() for kw in parsed.get("keywords", "").split(",") if kw.strip()]

                if not summary_text:
                    print(f"  [WARN] Empty summary for {title} @ {company}. Skipping this job.")
                    job_page.close()
                    continue   # 🚨 Also skip if summary field came back blank

                # ✅ Build payload for resume
                payload = {
                    "name":        f"{personal_info.get('first_name','')} {personal_info.get('last_name','')}",
                    "email":       personal_info.get("email",""),
                    "phone":       personal_info.get("phone",""),
                    "linkedin":    personal_info.get("linkedin",""),
                    "github":      personal_info.get("github",""),
                    "address":     address,
                    "summary":     summary_text,
                    "skills": [normalize_skill(kw) for kw in (llm_skills or extracted)],
                    "matched_keywords": extracted,
                    "experiences": experiences,
                    "education":   education,
                    "references":  references,
                    "title":       title,
                    "company":     company,
                    "location":    location,
                    "description": desc,
                }

                # ✅ Generate tailored resume PDF
                pdf_path = build_resume(payload)
                print(f"[INFO] 📄 Resume generated: {pdf_path}")

                # ✅ Easy Apply automation
                apply_status = "skipped"
                apply_error = None
                if config.AUTO_APPLY:
                    if config.DEBUG:
                        input("\n👉 [PAUSE] About to attempt LinkedIn Easy Apply. Inspect the page, then press Enter to continue…\n")
                    print("  [INFO] Attempting LinkedIn Easy Apply…")
                    try:
                        ok = apply_to_job(job_page, pdf_path, job_url)
                        apply_status = "applied" if ok else "failed"
                        print(f"  [RESULT] Easy Apply {'✅ SUCCESS' if ok else '❌ FAILED'}")
                    except Exception as e:
                        apply_status = "failed"
                        apply_error = str(e)
                        print(f"  [ERROR] Easy Apply failed: {apply_error}")

                # ✅ Store job results
                jobs_data.append({
                    **payload,
                    "url":          job_url,
                    "resume_pdf":   pdf_path,
                    "apply_status": apply_status,
                    "apply_error":  apply_error if apply_status == "failed" else None
                })

            finally:
                # ✅ Always close job_page if still open
                if 'job_page' in locals() and not job_page.is_closed():
                    job_page.close()


    return jobs_data
