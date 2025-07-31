import random, time, json, os
from src.job_parser import parse_job_card
import src.config as config

def clean_text(text: str) -> str:
    """Normalize scraped text by removing excessive newlines and trimming spaces."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

def normalize_skill(skill: str) -> str:
    if skill.isupper():  # keep acronyms as-is
        return skill
    return " ".join([w.capitalize() for w in skill.split()])

def load_existing_job_links(filename="job_urls.json") -> set:
    """Load previously saved job links from JSON file, return as set."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if isinstance(existing, list):
                print(f"[INFO] 🔄 Loaded {len(existing)} previously saved job URLs.")
                return set(existing)
        except Exception as e:
            print(f"[WARN] ⚠️ Could not load existing job URLs: {e}")
    return set()

def save_job_links(job_links, filename="job_urls.json"):
    """Save job links incrementally to a JSON file after each batch."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(job_links, f, indent=2)
        if config.DEBUG:
            print(f"[DEBUG] 💾 Saved {len(job_links)} job URLs to {filename}")
    except Exception as e:
        print(f"[WARN] ⚠️ Failed to save job URLs: {e}")



def detect_scroll_target(page):
    """
    Detects if LinkedIn's job list container exists and is scrollable.
    Returns the best selector to scroll (either job list or window).
    """

    job_list_selector = 'div.scaffold-layout__list.jobs-semantic-search-list'

    try:
        found = page.evaluate(f"""
            () => {{
                const el = document.querySelector('{job_list_selector}');
                return el && el.scrollHeight > el.clientHeight;
            }}
        """)
        if found:
            print(f"[INFO] ✅ Detected scrollable job list container: {job_list_selector}")
            return job_list_selector
        else:
            print("[INFO] ⚠️ Job list found but not scrollable — falling back to full window scroll.")
            return None
    except Exception as e:
        print(f"[WARNING] Could not detect job list container: {e}")
        return None


# ✅ Scroll to load all jobs in a human-like way
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

    print("[INFO] ✅ Finished mouse scrolling.")

def scroll_job_list_human_like(page, max_passes: int = 12, pause_between: float = 1.0) -> None:
    """
    Scrolls the LinkedIn job list container in a natural, human-like way.
    Adds jitter to scroll speed, pauses when LinkedIn stalls, and hovers to mimic hesitation.

    Args:
        page: Playwright page object.
        max_passes: Maximum number of scroll passes per page.
        pause_between: Base pause (seconds) between scrolls.
    """

    job_list_selector = "div.scaffold-layout__list.jobs-semantic-search-list"

    # ✅ Ensure job list exists before we scroll
    try:
        page.wait_for_selector(job_list_selector, timeout=10000)
    except:
        print("[WARN] No job list found for scrolling.")
        return

    if config.DEBUG:
        print(f"[DEBUG] 🎯 Starting human-like scroll inside '{job_list_selector}'")

    loaded_last_round = 0
    scroll_speed = 350  # 🎯 starting scroll speed (px per scroll)

    for scroll_round in range(max_passes):
        job_cards = page.locator("ul.semantic-search-results-list > li")
        total_cards = job_cards.count()
        placeholders = job_cards.locator(".semantic-search-results-list__generic-occludable-area").count()
        loaded_cards = total_cards - placeholders

        if config.DEBUG:
            print(f"[DEBUG] Scroll pass {scroll_round+1}: {loaded_cards}/25 jobs loaded "
                  f"(placeholders: {placeholders})")

        # ✅ Stop if we’ve loaded all visible jobs (typically 25 per page)
        if loaded_cards >= 25:
            if config.DEBUG:
                print(f"[DEBUG] ✅ All jobs loaded by scroll pass {scroll_round+1}")
            break

        # 🎯 Random jitter to simulate natural scroll inconsistency
        jitter = random.randint(-20, 20)
        adjusted_scroll = max(100, scroll_speed + jitter)  # keep it sane
        page.mouse.wheel(0, adjusted_scroll)

        if config.DEBUG:
            print(f"[DEBUG] 🖱️ Scrolled {adjusted_scroll}px "
                  f"(base {scroll_speed}px + jitter {jitter}px)")

        time.sleep(pause_between)

        # 🔄 Hover + slow down if LinkedIn didn’t load new jobs
        if loaded_cards == loaded_last_round:
            scroll_speed = max(150, scroll_speed - 50)
            if config.DEBUG:
                print(f"[DEBUG] ⏬ No new jobs — slowing scroll to {scroll_speed}px")

            page.hover(job_list_selector)
            if config.DEBUG:
                print("[DEBUG] 🕵️ Hover pause — mimicking user hesitation")

            time.sleep(1.5)
        else:
            # ✅ Speed up slightly when new jobs appear
            scroll_speed = min(500, scroll_speed + 25)
            if config.DEBUG:
                print(f"[DEBUG] ⏫ New jobs loaded — speeding scroll to {scroll_speed}px")

        loaded_last_round = loaded_cards

    # ✅ Final status
    job_cards = page.locator("ul.semantic-search-results-list > li")
    total_cards = job_cards.count()
    placeholders = job_cards.locator(".semantic-search-results-list__generic-occludable-area").count()
    loaded_cards = total_cards - placeholders
    if config.DEBUG:
        print(f"[DEBUG] ✅ Final job load count: {loaded_cards}/25 after human-like scroll.")


def collect_job_links_with_pagination(page, base_url: str, max_jobs: int = 100, start_fresh: bool = False) -> list:
    """
    Collects job posting URLs by walking through LinkedIn job search pagination.
    Uses human-like scrolling to load all jobs and skips already applied jobs.

    ✅ Saves after each page
    ✅ Skips duplicates from previous runs (loaded from job_urls.json)
    ✅ Optional start_fresh to clear existing JSON data

    Args:
        page: Playwright page object.
        base_url: LinkedIn search URL (first page).
        max_jobs: Max jobs to collect.
        start_fresh: If True, will ignore and overwrite any existing job_urls.json.

    Returns:
        list[str]: Deduplicated job posting URLs.
    """
    print("[INFO] Collecting jobs using pagination…")

    filename = "job_urls.json"

    # ✅ Handle start_fresh
    if start_fresh and os.path.exists(filename):
        os.remove(filename)
        print(f"[INFO] 🗑️ start_fresh=True → Deleted old {filename}")

    # ✅ Load any existing jobs unless starting fresh
    job_links = [] if start_fresh else list(load_existing_job_links(filename))
    seen_ids = {url.split("/")[-2] for url in job_links}  # Extract job IDs from URLs

    # ✅ Detect total job count
    try:
        page.wait_for_selector("div.t-black--light.pv4.text-body-small.mr2", timeout=5000)
        total_jobs_text = page.inner_text("div.t-black--light.pv4.text-body-small.mr2")
        total_jobs = int("".join(filter(str.isdigit, total_jobs_text)))
    except:
        print("[WARN] Could not find total job count. Defaulting to 1 page.")
        total_jobs = 0

    print(f"[INFO] ✅ Total jobs listed: {total_jobs if total_jobs else 'Unknown'}")

    jobs_per_page = 25
    max_pages = (max_jobs // jobs_per_page) + 1

    for page_num in range(max_pages):
        start_offset = page_num * jobs_per_page
        paged_url = f"{base_url}&start={start_offset}"

        print(f"[INFO] 🔄 Navigating to page batch: {paged_url}")
        page.goto(paged_url, timeout=45000)

        # ✅ Wait for job list container
        job_list_selector = "div.scaffold-layout__list.jobs-semantic-search-list"
        try:
            page.wait_for_selector(job_list_selector, timeout=10000)
            print("[INFO] ✅ Found job list container.")
        except:
            print(f"[WARN] Job list container not found on page {page_num+1}. Skipping.")
            continue

        # ✅ Hover before scrolling
        page.hover(job_list_selector)
        if config.DEBUG:
            print("[DEBUG] 🖱️ Mouse hovered over job list container.")

        # ✅ Human-like scrolling for this page
        scroll_job_list_human_like(page, max_passes=15, pause_between=1.0)

        # ✅ Parse job cards
        job_cards = page.locator("ul.semantic-search-results-list > li")
        job_count = job_cards.count()

        if config.DEBUG:
            print(f"[DEBUG] Found {job_count} <li> elements after scroll on page {page_num+1}.")

        for i in range(job_count):
            job_data = parse_job_card(job_cards.nth(i))

            # Skip missing ID
            if not job_data.get("id"):
                continue

            # Skip jobs already applied
            if job_data.get("already_applied"):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping '{job_data['title']}' – application already submitted.")
                continue

            # ✅ Skip if already saved
            if job_data["id"] in seen_ids:
                if config.DEBUG:
                    print(f"[DEBUG] 🔁 Already saved job {job_data['id']} – skipping.")
                continue

            # ✅ Add new jobs
            job_links.append(job_data["url"])
            seen_ids.add(job_data["id"])
            if config.DEBUG:
                print(f"[DEBUG] ✅ Parsed & added: {job_data}")

        # ✅ Save after each page batch
        save_job_links(job_links, filename)

        print(f"[INFO] ✅ Page {page_num+1} done. Total collected so far: {len(job_links)}")

        # ✅ Stop if limits are reached
        if len(job_links) >= max_jobs:
            break
        if total_jobs and len(job_links) >= total_jobs:
            break

    print(f"[INFO] 🎯 Finished pagination. Total jobs collected: {len(job_links)}")
    return job_links