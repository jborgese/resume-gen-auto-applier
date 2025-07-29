from pathlib import Path
import json
import src.config as config
from src.scraper import scrape_jobs_from_search
from src.resume_builder import build_resume
from src.easy_apply import apply_to_job
from src.llm_summary import generate_resume_summary
import yaml

# Load personal_info.yaml if needed
with open("personal_info.yaml", "r") as f:
    info = yaml.safe_load(f)

# ✅ Try loading stopwords.json if present
STOPWORDS = set()
try:
    with open("stopwords.json") as f:
        STOPWORDS = set(json.load(f))
        print(f"[INFO] 🛑 Loaded {len(STOPWORDS)} stopwords from stopwords.json.")
except FileNotFoundError:
    print("[WARNING] ⚠️ No stopwords.json found — all scraped keywords will be used.")

if __name__ == "__main__":
    print(f"[INFO] Using resume template: {config.DEFAULT_TEMPLATE}")

    # ✅ LinkedIn search URL
    search_url = "https://www.linkedin.com/jobs/search-results/?f_AL=true&keywords=Software%20Engineer&origin=JOBS_HOME_SEARCH_BUTTON"

    # ✅ Check for LinkedIn credentials
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        raise ValueError("❌ LinkedIn email and password must be set in the .env file.")

    # ✅ Scrape job listings from LinkedIn search page
    jobs = scrape_jobs_from_search(search_url, config.LINKEDIN_EMAIL, config.LINKEDIN_PASSWORD)

    if not jobs:
        print("[WARNING] No jobs found in search results.")
        exit()

    print(f"[INFO] Found {len(jobs)} jobs in search results.")

    # ✅ Limit for testing (e.g., apply to first 3 jobs)
    max_jobs_to_apply = 5

    for i, job in enumerate(jobs[:max_jobs_to_apply], start=1):
        try:
            print(f"\n===== [JOB {i}] {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')} =====")

            # ✅ Safely extract job fields
            title = job.get("title", "Unknown").strip() if job.get("title") else "Unknown"
            company = job.get("company", "Unknown").strip() if job.get("company") else "Unknown"
            location = job.get("location", "N/A").strip() if job.get("location") else "N/A"
            description = job.get("description", "").strip()

            # ✅ Handle keywords robustly
            raw_keywords = job.get("keywords", [])
            if not isinstance(raw_keywords, list):
                print(f"[WARNING] ⚠️ Keywords for {title} came back as {type(raw_keywords)} — converting to list.")
                raw_keywords = [str(raw_keywords)]

            # ✅ Normalize and filter
            normalized_keywords = []
            for kw in raw_keywords:
                if isinstance(kw, str):
                    kw_clean = kw.strip()
                    kw_lower = kw_clean.lower()

                    # ✅ Skip empty strings & stopwords first
                    if not kw_lower or kw_lower in STOPWORDS:
                        continue

                    # ✅ Only keep words longer than 2 chars unless they’re special short terms
                    if len(kw_lower) > 2 or kw_lower in ["ai", "c#", "go"]:
                        normalized_keywords.append(kw_lower)

            # ✅ Deduplicate & capitalize for display
            deduped_keywords = sorted(set(normalized_keywords))
            display_keywords = [kw.upper() if kw.isupper() else kw.capitalize() for kw in deduped_keywords]

            summary_keywords = ", ".join(display_keywords) if display_keywords else "various technologies"


            # ✅ Grab weighted keywords (if available)
            weighted_keywords = job.get("keyword_weights", [])

            # ✅ Pick top 10 keywords for skills (remove duplicates, strip whitespace)
            top_weighted_keywords = [kw for kw, score in weighted_keywords][:10]

            # ✅ If too few keywords found, backfill with your core stack
            fallback_skills = ["Python", "Playwright", "LLM Integration", "Docker", "GitHub Actions", "NLP"]
            final_skills = display_keywords[:10] if display_keywords else fallback_skills
            
            # ✅ Generate a resume summary using GPT
            print(f"[INFO] Generating resume summary for '{title}' at '{company}' with skills: {final_skills}")
            summary_result_raw = generate_resume_summary(title, company, description)
            print(f"[DEBUG] Raw summary_result from LLM: {summary_result_raw}")

            try:
                summary_result = json.loads(summary_result_raw)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to decode LLM summary JSON: {e}")
                summary_result = {}

            summary = summary_result.get("summary", "")
            llm_keywords = summary_result.get("keywords", [])

            print(f"[INFO] LLM summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")
            print(f"[INFO] LLM keywords (raw): {llm_keywords}")

            # ✅ Ensure llm_keywords is always a list
            if isinstance(llm_keywords, str):
                print("[DEBUG] LLM keywords returned as string, splitting by comma.")
                llm_keywords = [kw.strip() for kw in llm_keywords.split(',') if kw.strip()]
            elif not isinstance(llm_keywords, list):
                print(f"[WARNING] LLM keywords returned as {type(llm_keywords)}, using fallback skills.")
                llm_keywords = final_skills

            # ✅ Capitalize each keyword if not already
            llm_keywords = [kw.capitalize() if isinstance(kw, str) else kw for kw in llm_keywords]

            print(f"[INFO] Final LLM keywords: {llm_keywords}")

            # ✅ Build hardened resume data structure
            resume_data = {
                "name": f"{info['first_name']} {info['last_name']}",
                "email": info["email"],
                "phone": info["phone"],
                "linkedin": info["linkedin"],
                "github": info["github"],
                "summary": summary,
                "skills": llm_keywords,
                "experiences": info.get("job_history", []),
                "education": info.get("education", []),
                "references": info.get("references", []),
                "matched_keywords": llm_keywords,   # ✅ Save full keyword set for reference
                "location": location,
                "description": description,

                # ✅ NEW FIELDS for PDF filenames & template
                "title": title,
                "company": company
            }

            # ✅ Generate tailored PDF resume (now job-specific)
            resume_path = build_resume(resume_data)
            print(f"[SUCCESS] Resume generated for {title}: {resume_path}")

            # ✅ Auto Apply logic
            if config.AUTO_APPLY:
                print("[INFO] Auto Apply is enabled — attempting Easy Apply automation...")
                success = apply_to_job(job["page"], resume_path)
                if success:
                    print(f"[SUCCESS] Easy Apply submitted for {title} at {company}")
                else:
                    print(f"[WARNING] Easy Apply may have failed for {title} at {company}")
            else:
                print("[INFO] Auto Apply is disabled — skipping automated application.")

        except Exception as e:
            print(f"[ERROR] ❌ Error processing job {i} ({job.get('title', 'Unknown')}): {e}")

    print("\n[COMPLETE] Finished processing jobs.")
