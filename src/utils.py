import random, time, json, os
from src.job_parser import parse_job_card, wait_for_job_cards_to_hydrate
from src.shared_utils import FileHandler, TextProcessor, DelayManager
from src.logging_config import get_logger, log_function_call, log_error_context
import src.config as config

logger = get_logger(__name__)

def clean_text(text: str) -> str:
    """Normalize scraped text by removing excessive newlines and trimming spaces."""
    return TextProcessor.clean_text(text)

def normalize_skill(skill: str) -> str:
    """Normalize skill names for consistent matching."""
    return TextProcessor.normalize_skill(skill)

def load_existing_job_links(filename="job_urls.json") -> set:
    """Load previously saved job links from JSON file, return as set."""
    try:
        existing = FileHandler.load_json(filename)
        if existing:
            logger.info("Loaded previously saved job URLs", count=len(existing))
            return set(existing)
    except Exception as e:
        logger.warning("Could not load existing job URLs", error=str(e))
    return set()

def save_job_links(job_links, filename="job_urls.json"):
    """Save job links incrementally to a JSON file after each batch."""
    try:
        if FileHandler.save_json(job_links, filename):
            if config.DEBUG:
                logger.debug("Saved job URLs", count=len(job_links), filename=filename)
        else:
            logger.warning("Failed to save job URLs", filename=filename)
    except Exception as e:
        logger.warning("Failed to save job URLs", error=str(e))

def clean_existing_jobs(page, filename="job_urls.json"):
    """Removes jobs from job_urls.json that have already been applied for."""
    if not os.path.exists(filename):
        return []

    with open(filename, "r") as f:
        saved_jobs = json.load(f)

    cleaned_jobs = []
    for url in saved_jobs:
        page.goto(url)
        try:
            # Look for the "Application submitted" indicator
            if page.locator("text=Application submitted").count():
                logger.info("Job already applied - removing from list", url=url)
                continue  # skip this job
        except:
            logger.warning("Could not verify job status - keeping just in case", url=url)

        cleaned_jobs.append(url)

    # [OK] Overwrite JSON file with cleaned list
    with open(filename, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)

    return cleaned_jobs


def detect_scroll_target(page):
    """
    Detects if LinkedIn's job list container exists and is scrollable.
    Returns the best selector to scroll (either job list or window).
    """

    job_list_selector = config.LINKEDIN_SELECTORS["job_search"]["job_list"]

    try:
        found = page.evaluate(f"""
            () => {{
                const el = document.querySelector('{job_list_selector}');
                return el && el.scrollHeight > el.clientHeight;
            }}
        """)
        if found:
            logger.info("Detected scrollable job list container", selector=job_list_selector)
            return job_list_selector
        else:
            logger.info("Job list found but not scrollable - falling back to full window scroll")
            return None
    except Exception as e:
        logger.warning("Could not detect job list container", error=str(e))
        return None


# [OK] Scroll to load all jobs in a human-like way
def human_like_scroll(page, rounds=12):
    print(f"[INFO] 🖱️ Starting human-like mouse scroll for {rounds} rounds...")
    for i in range(rounds):
        scroll_amount = random.randint(250, 450)  # small varied increments
        page.mouse.wheel(0, scroll_amount)
        print(f"[DEBUG] 🖱️ Mouse wheel scroll {i+1}/{rounds} by {scroll_amount}px")

        # ⏳ Wait slightly differently each time
        time.sleep(random.uniform(0.7, 1.4))

        # 🔄 Occasionally scroll up a tiny bit to mimic human checking behavior
        if i % 4 == 3:
            page.mouse.wheel(0, -random.randint(50, 150))
            print("[DEBUG] 🔼 Small upward scroll for realism")

    print("[INFO] [OK] Finished mouse scrolling.")

def scroll_job_list_human_like(page, max_passes: int = 12, pause_between: float = 1.0) -> None:
    """
    Scrolls the LinkedIn job list container with true lazy-load hydration.
    [OK] Uses mouse wheel to ensure LinkedIn thinks a human is scrolling.
    [OK] Waits for visible job cards to hydrate before moving on.
    [OK] Does NOT stop just because 25 <li> exist  checks for wrapper hydration.
    """

    job_list_selector = config.LINKEDIN_SELECTORS["job_search"]["job_list"]

    try:
        page.wait_for_selector(job_list_selector, timeout=config.TIMEOUTS["job_list"])
    except:
        print("[WARN] No job list found for scrolling.")
        return

    if config.DEBUG:
        print(f"[DEBUG] 🎯 Starting robust scroll inside '{job_list_selector}'")

    scroll_speed = config.SCROLL_CONFIG["base_speed"]
    loaded_last_round = 0

    for scroll_round in range(max_passes):
        # [OK] Hover over the job list so the scroll wheel applies there
        page.hover(job_list_selector)

        # [OK] Scroll down a bit (simulate human scrolling)
        jitter = random.randint(-config.SCROLL_CONFIG["jitter_range"], config.SCROLL_CONFIG["jitter_range"])
        adjusted_scroll = max(100, scroll_speed + jitter)

        if config.DEBUG:
            print(f"[DEBUG] 🖱️ Scroll pass {scroll_round+1}  will scroll {adjusted_scroll}px.")

        page.mouse.wheel(0, adjusted_scroll)
        if config.DEBUG:
            print(f"[DEBUG] 🖱️ Scrolled {adjusted_scroll}px (base {scroll_speed}px + jitter {jitter}px)")

        time.sleep(config.SCROLL_CONFIG["pause_between"])

        # [OK] Check job list hydration status
        job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
        total_cards = job_cards.count()

        # Count hydrated cards (have wrapper div)
        hydrated_count = 0
        for i in range(total_cards):
            card_wrapper = job_cards.nth(i).locator(config.LINKEDIN_SELECTORS["job_search"]["job_wrapper"])
            if card_wrapper.count():
                hydrated_count += 1

        if config.DEBUG:
            print(f"[DEBUG] Hydrated {hydrated_count}/{total_cards} job cards after scroll {scroll_round+1}")

        # [OK] If all 25 jobs are hydrated, we can stop early
        if hydrated_count >= 25:
            if config.DEBUG:
                print(f"[DEBUG] [OK] All job cards fully hydrated by scroll pass {scroll_round+1}")
            break

        # [OK] Adjust speed based on hydration progress
        if hydrated_count == loaded_last_round:
            scroll_speed = max(config.SCROLL_CONFIG["min_speed"], scroll_speed - 50)
            if config.DEBUG:
                print(f"[DEBUG] ⏬ No new hydration  slowing scroll to {scroll_speed}px")
            time.sleep(1.5)
        else:
            scroll_speed = min(config.SCROLL_CONFIG["max_speed"], scroll_speed + 25)
            if config.DEBUG:
                print(f"[DEBUG] ⏫ New jobs hydrated  speeding scroll to {scroll_speed}px")

        loaded_last_round = hydrated_count

    # [OK] Final hydration summary
    job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
    hydrated_count = 0
    for i in range(job_cards.count()):
        if job_cards.nth(i).locator(config.LINKEDIN_SELECTORS["job_search"]["job_wrapper"]).count():
            hydrated_count += 1

    if config.DEBUG:
        print(f"[DEBUG] [OK] Final hydration: {hydrated_count}/{job_cards.count()} job cards hydrated after scroll.")


from typing import Optional

def collect_job_links_with_pagination(page, base_url: str, max_jobs: Optional[int] = None, start_fresh: bool = False) -> list:
    """
    Collects job posting URLs by walking through LinkedIn job search pagination.
    [OK] Skips jobs already marked 'Applied' in the job list itself
    [OK] Deduplicates and saves to job_urls.json incrementally

    Args:
        page: Playwright page object.
        base_url: LinkedIn search URL (first page).
        max_jobs: Max jobs to collect. If None, uses config.MAX_JOBS.
        start_fresh: If True, clears job_urls.json before scraping.

    Returns:
        list[str]: Deduplicated job posting URLs.
    """
    if max_jobs is None:
        max_jobs = config.MAX_JOBS

    print("[INFO] Collecting jobs using pagination")

    filename = "job_urls.json"

    # [OK] Handle start_fresh
    if start_fresh and os.path.exists(filename):
        os.remove(filename)
        print(f"[INFO] [DELETE] start_fresh=True -> Deleted old {filename}")

    # [OK] Load any existing saved jobs
    job_links = list(load_existing_job_links(filename)) if os.path.exists(filename) else []
    seen_ids = {url.split("/")[-2] for url in job_links}

    print(f"[INFO] Loaded {len(job_links)} previously saved job URLs.")

    # [OK] Check if we already have enough jobs - skip scraping if so
    if len(job_links) >= max_jobs:
        print(f"[INFO] Already have {len(job_links)} jobs (>= {max_jobs} max). Skipping scraping and using existing jobs.")
        return job_links

    # [OK] Detect total job count from the search page
    try:
        page.wait_for_selector(config.LINKEDIN_SELECTORS["job_search"]["total_jobs"], timeout=config.TIMEOUTS["total_jobs"])
        total_jobs_text = page.inner_text(config.LINKEDIN_SELECTORS["job_search"]["total_jobs"])
        total_jobs = int("".join(filter(str.isdigit, total_jobs_text)))
    except:
        print("[WARN] [WARN] Could not find total job count. Defaulting to 1 page.")
        total_jobs = 0

    print(f"[INFO] Total jobs listed: {total_jobs if total_jobs else 'Unknown'}")

    jobs_per_page = 25
    collected_count = len(job_links)  # Start with existing jobs count
    page_num = 0

    while collected_count < max_jobs and (not total_jobs or collected_count < total_jobs):
        start_offset = page_num * jobs_per_page
        paged_url = f"{base_url}&start={start_offset}"

        print(f"[INFO] Navigating to page {page_num+1} (start={start_offset})")
        page.goto(paged_url, timeout=config.TIMEOUTS["search_page"])

        # [OK] Wait for job list container
        job_list_selector = config.LINKEDIN_SELECTORS["job_search"]["job_list"]
        try:
            page.wait_for_selector(job_list_selector, timeout=config.TIMEOUTS["job_list"])
            print("[INFO] Found job list container.")
        except:
            print(f"[WARN] Job list container not found on page {page_num+1}. Skipping.")
            page_num += 1
            continue

        # [OK] Hover before scrolling
        page.hover(job_list_selector)
        if config.DEBUG:
            print("[DEBUG] 🖱️ Mouse hovered over job list container.")

        # [OK] Human-like scrolling
        scroll_job_list_human_like(page, max_passes=config.RETRY_CONFIG["max_scroll_passes"], pause_between=config.SCROLL_CONFIG["pause_between"])

        # [OK] Parse job cards
        job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
        job_count = job_cards.count()
        if config.DEBUG:
            print(f"[DEBUG] Found {job_count} <li> elements after scroll on page {page_num+1}.")

        for i in range(job_count):
            job_el = job_cards.nth(i)
            job_data = parse_job_card(job_el)

            if not job_data.get("id"):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping li #{i}  no job ID found.")
                continue
            if job_data.get("already_applied"):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping '{job_data['title']}'  application already submitted.")
                continue
            if job_data["id"] in seen_ids:
                if config.DEBUG:
                    print(f"[DEBUG] 🔁 Already saved job {job_data['id']}  skipping.")
                continue

            job_links.append(job_data["url"])
            seen_ids.add(job_data["id"])
            collected_count += 1

            if config.DEBUG:
                print(f"[DEBUG] [OK] Parsed & added: {job_data}")

            # Early stop if reached limits mid-page
            if collected_count >= max_jobs or (total_jobs and collected_count >= total_jobs):
                break

        save_job_links(job_links, filename)
        print(f"[INFO] Page {page_num+1} done. Total collected so far: {collected_count}")

        # Next page
        page_num += 1

    print(f"[INFO] Finished pagination. Total jobs collected: {collected_count}")
    return job_links

