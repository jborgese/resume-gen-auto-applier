from typing import Union
import src.config as config
import time

def wait_for_job_cards_to_hydrate(page, timeout=None):
    """
    Ensures job <li> elements are fully populated (not placeholders).
    Will loop until all visible job cards have real content or timeout is reached.
    """
    import time
    if timeout is None:
        timeout = config.TIMEOUTS["job_cards"]
    start = time.time()
    while time.time() - start < timeout / 1000:
        all_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
        hydrated = True
        for i in range(all_cards.count()):
            card = all_cards.nth(i)
            # If no wrapper, it's probably still a skeleton
            wrapper = card.locator(config.LINKEDIN_SELECTORS["job_search"]["job_wrapper"])
            if wrapper.count() == 0:
                hydrated = False
                break
        if hydrated:
            if config.DEBUG:
                print("[DEBUG] ✅ All job cards are hydrated with data.")
            return True
        time.sleep(0.5)

    print("[WARN] ⚠️ Some job cards may not have hydrated fully.")
    return False


def parse_job_card(li_element) -> dict:
    """
    Parses a LinkedIn job card <li> Playwright element into structured job data.
    ✅ Waits for card hydration before parsing.
    ✅ Detects 'Applied' status from search list (footer) and fallback banners.
    ✅ Uses try/except on each field to prevent breaks from partial skeletons.
    """
    job = {
        "id": None,
        "url": None,
        "title": None,
        "company": None,
        "location": None,
        "posted_date": None,
        "easy_apply": False,
        "work_mode": None,
        "already_applied": False,
        "hydrated": False  # for debugging
    }

    wrapper_selector = config.LINKEDIN_SELECTORS["job_search"]["job_wrapper"]
    hydrated = False
    for attempt in range(5):  # wait up to ~5 seconds for hydration
        if li_element.locator(wrapper_selector).count():
            hydrated = True
            break
        time.sleep(1)
    job["hydrated"] = hydrated

    if not hydrated:
        print("[WARN] ⚠️ Job card not fully hydrated (missing wrapper) — parsing anyway.")

    # ✅ ID from wrapper
    try:
        wrapper = li_element.locator(wrapper_selector)
        if wrapper.count():
            job_id = wrapper.get_attribute("data-job-id")
            if job_id:
                job["id"] = job_id
                job["url"] = f"https://www.linkedin.com/jobs/view/{job_id}/"
    except:
        print("[WARN] ⚠️ Could not get job ID from wrapper.")

    # ✅ Fallback: grab from <a> href
    if not job["id"]:
        try:
            job_link = li_element.locator("a[href*='/jobs/view/']").first
            if job_link.count():
                href = job_link.get_attribute("href")
                if href and "/jobs/view/" in href:
                    job_id = href.split("/jobs/view/")[1].split("/")[0]
                    job["id"] = job_id
                    job["url"] = f"https://www.linkedin.com/jobs/view/{job_id}/"
        except:
            print("[WARN] ⚠️ Could not parse job link fallback.")

    # ✅ Title
    try:
        title_el = li_element.locator("h3")
        if title_el.count():
            job["title"] = title_el.inner_text().strip()
    except:
        print("[WARN] ⚠️ Could not parse title.")

    # ✅ Company
    try:
        company_el = li_element.locator(
            "div.artdeco-entity-lockup__subtitle, span.job-card-container__primary-description"
        )
        if company_el.count():
            job["company"] = company_el.inner_text().strip()
    except:
        print("[WARN] ⚠️ Could not parse company.")

    # ✅ Location + Work Mode Heuristic
    try:
        location_el = li_element.locator("div.artdeco-entity-lockup__caption, .job-card-container__metadata-item")
        if location_el.count():
            location_text = location_el.inner_text().strip()
            job["location"] = location_text

            if "Remote" in location_text:
                job["work_mode"] = "Remote"
            elif "Hybrid" in location_text:
                job["work_mode"] = "Hybrid"
            elif "On-site" in location_text:
                job["work_mode"] = "On-site"
    except:
        print("[WARN] ⚠️ Could not parse location.")

    # ✅ Posted Date
    try:
        time_el = li_element.locator("time")
        if time_el.count():
            job["posted_date"] = time_el.get_attribute("datetime")
    except:
        print("[WARN] ⚠️ Could not parse posted date.")

    # ✅ Easy Apply
    try:
        footer_texts = li_element.locator("span").all_inner_texts()
        if any("Easy Apply" in text for text in footer_texts):
            job["easy_apply"] = True
    except:
        print("[WARN] ⚠️ Could not verify Easy Apply status.")

    # ✅ Already applied (job card footer)
    try:
        applied_footer_item = li_element.locator("li.job-card-job-posting-card-wrapper__footer-item.t-bold")
        if applied_footer_item.count():
            applied_text = applied_footer_item.inner_text().strip()
            if "Applied" in applied_text:
                job["already_applied"] = True
    except:
        print("[WARN] ⚠️ Could not check 'Applied' footer.")

    # ✅ Fallback: job detail banner check (rare case where LinkedIn marks applied here)
    if not job["already_applied"]:
        try:
            applied_banner = li_element.locator("div.post-apply-timeline__content")
            if applied_banner.count() and "Application submitted" in applied_banner.inner_text():
                job["already_applied"] = True
        except:
            print("[WARN] ⚠️ Could not check 'Application submitted' banner.")

    return job
