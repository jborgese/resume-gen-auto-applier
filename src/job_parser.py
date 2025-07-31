from typing import Union

def parse_job_card(li_element) -> dict:
    """
    Parses a LinkedIn job card <li> Playwright element into structured job data.

    Args:
        li_element: Playwright locator for a single <li> job card.

    Returns:
        dict: Parsed job details with id, url, title, company, location,
              posted_date, easy_apply flag, work_mode, and applied flag.
    """
    job: dict[str, Union[str, bool, None]] = {
        "id": None,
        "url": None,
        "title": None,
        "company": None,
        "location": None,
        "posted_date": None,
        "easy_apply": False,
        "work_mode": None,          # Remote / Hybrid / On-site
        "already_applied": False    # Skip if true
    }

    # ✅ Extract job ID from wrapper div
    wrapper = li_element.locator("div.job-card-job-posting-card-wrapper")
    if wrapper.count():
        job_id = wrapper.get_attribute("data-job-id")
        if job_id:
            job["id"] = job_id
            job["url"] = f"https://www.linkedin.com/jobs/view/{job_id}/"

    # ✅ Title
    title_sel = "div.job-card-job-posting-card-wrapper__content h3, div.job-card-job-posting-card-wrapper__title"
    title_el = li_element.locator(title_sel)
    if title_el.count():
        job["title"] = title_el.inner_text().strip()

    # ✅ Company name
    company_sel = "div.job-card-job-posting-card-wrapper__content div.artdeco-entity-lockup__subtitle"
    company_el = li_element.locator(company_sel)
    if company_el.count():
        job["company"] = company_el.inner_text().strip()

    # ✅ Location (also used for work_mode detection)
    location_sel = "div.job-card-job-posting-card-wrapper__content div.artdeco-entity-lockup__caption"
    location_el = li_element.locator(location_sel)
    if location_el.count():
        location_text = location_el.inner_text().strip()
        job["location"] = location_text

        # Extract work mode (basic heuristic)
        if "(Remote)" in location_text:
            job["work_mode"] = "Remote"
        elif "(Hybrid)" in location_text:
            job["work_mode"] = "Hybrid"
        elif "(On-site)" in location_text:
            job["work_mode"] = "On-site"

    # ✅ Posted date (from <time datetime>)
    time_el = li_element.locator("time")
    if time_el.count():
        job["posted_date"] = time_el.get_attribute("datetime")

    # ✅ Easy Apply detection
    easy_apply_el = li_element.locator("li.job-card-job-posting-card-wrapper__footer-item span")
    if easy_apply_el.count():
        footer_texts = easy_apply_el.all_inner_texts()
        if any("Easy Apply" in text for text in footer_texts):
            job["easy_apply"] = True

    # ✅ Check if user already applied (Application submitted)
    applied_el = li_element.locator("div.post-apply-timeline__content")
    if applied_el.count():
        # Look for the exact text inside the timeline div
        applied_text = applied_el.inner_text().strip()
        if "Application submitted" in applied_text:
            job["already_applied"] = True

    return job
