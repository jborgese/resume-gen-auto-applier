import random, time, json, os
from src.job_parser import parse_job_card, wait_for_job_cards_to_hydrate
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
                print(f"[INFO] ✅ Job already applied: {url} — removing from list.")
                continue  # skip this job
        except:
            print(f"[WARN] ⚠️ Could not verify job status for {url}, keeping just in case.")

        cleaned_jobs.append(url)

    # ✅ Overwrite JSON file with cleaned list
    with open(filename, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)

    return cleaned_jobs


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
    Scrolls the LinkedIn job list container with true lazy-load hydration.
    ✅ Uses mouse wheel to ensure LinkedIn thinks a human is scrolling.
    ✅ Waits for visible job cards to hydrate before moving on.
    ✅ Does NOT stop just because 25 <li> exist — checks for wrapper hydration.
    """

    job_list_selector = "div.scaffold-layout__list.jobs-semantic-search-list"

    try:
        page.wait_for_selector(job_list_selector, timeout=10000)
    except:
        print("[WARN] No job list found for scrolling.")
        return

    if config.DEBUG:
        print(f"[DEBUG] 🎯 Starting robust scroll inside '{job_list_selector}'")

    scroll_speed = 350
    loaded_last_round = 0

    for scroll_round in range(max_passes):
        # ✅ Hover over the job list so the scroll wheel applies there
        page.hover(job_list_selector)

        # ✅ Scroll down a bit (simulate human scrolling)
        jitter = random.randint(-20, 20)
        adjusted_scroll = max(100, scroll_speed + jitter)

        if config.DEBUG:
            input(f"[PAUSE] 🖱️ Scroll pass {scroll_round+1} — will scroll {adjusted_scroll}px. Press Enter to continue…")

        page.mouse.wheel(0, adjusted_scroll)
        if config.DEBUG:
            print(f"[DEBUG] 🖱️ Scrolled {adjusted_scroll}px (base {scroll_speed}px + jitter {jitter}px)")

        time.sleep(pause_between)

        # ✅ Check job list hydration status
        job_cards = page.locator("ul.semantic-search-results-list > li")
        total_cards = job_cards.count()

        # Count hydrated cards (have wrapper div)
        hydrated_count = 0
        for i in range(total_cards):
            card_wrapper = job_cards.nth(i).locator("div.job-card-job-posting-card-wrapper")
            if card_wrapper.count():
                hydrated_count += 1

        if config.DEBUG:
            print(f"[DEBUG] Hydrated {hydrated_count}/{total_cards} job cards after scroll {scroll_round+1}")

        # ✅ If all 25 jobs are hydrated, we can stop early
        if hydrated_count >= 25:
            if config.DEBUG:
                print(f"[DEBUG] ✅ All job cards fully hydrated by scroll pass {scroll_round+1}")
            break

        # ✅ Adjust speed based on hydration progress
        if hydrated_count == loaded_last_round:
            scroll_speed = max(150, scroll_speed - 50)
            if config.DEBUG:
                print(f"[DEBUG] ⏬ No new hydration — slowing scroll to {scroll_speed}px")
            time.sleep(1.5)
        else:
            scroll_speed = min(500, scroll_speed + 25)
            if config.DEBUG:
                print(f"[DEBUG] ⏫ New jobs hydrated — speeding scroll to {scroll_speed}px")

        loaded_last_round = hydrated_count

    # ✅ Final hydration summary
    job_cards = page.locator("ul.semantic-search-results-list > li")
    hydrated_count = 0
    for i in range(job_cards.count()):
        if job_cards.nth(i).locator("div.job-card-job-posting-card-wrapper").count():
            hydrated_count += 1

    if config.DEBUG:
        print(f"[DEBUG] ✅ Final hydration: {hydrated_count}/{job_cards.count()} job cards hydrated after scroll.")


def collect_job_links_with_pagination(page, base_url: str, max_jobs: int = 100, start_fresh: bool = False) -> list:
    """
    Collects job posting URLs by walking through LinkedIn job search pagination.
    ✅ Skips jobs already marked 'Applied' in the job list itself
    ✅ Deduplicates and saves to job_urls.json incrementally

    Args:
        page: Playwright page object.
        base_url: LinkedIn search URL (first page).
        max_jobs: Max jobs to collect.
        start_fresh: If True, clears job_urls.json before scraping.

    Returns:
        list[str]: Deduplicated job posting URLs.
    """
    print("[INFO] Collecting jobs using pagination…")

    filename = "job_urls.json"

    # ✅ Handle start_fresh
    if start_fresh and os.path.exists(filename):
        os.remove(filename)
        print(f"[INFO] 🗑️ start_fresh=True → Deleted old {filename}")

    # ✅ Load any existing saved jobs
    job_links = list(load_existing_job_links(filename)) if os.path.exists(filename) else []
    seen_ids = {url.split("/")[-2] for url in job_links}

    print(f"[INFO] 🔄 Loaded {len(job_links)} previously saved job URLs.")

    # ✅ Detect total job count from the search page
    try:
        page.wait_for_selector("div.t-black--light.pv4.text-body-small.mr2", timeout=5000)
        total_jobs_text = page.inner_text("div.t-black--light.pv4.text-body-small.mr2")
        total_jobs = int("".join(filter(str.isdigit, total_jobs_text)))
    except:
        print("[WARN] ⚠️ Could not find total job count. Defaulting to 1 page.")
        total_jobs = 0

    print(f"[INFO] ✅ Total jobs listed: {total_jobs if total_jobs else 'Unknown'}")

    jobs_per_page = 25
    collected_count = 0
    page_num = 0

    while collected_count < max_jobs and (not total_jobs or collected_count < total_jobs):
        start_offset = page_num * jobs_per_page
        paged_url = f"{base_url}&start={start_offset}"

        print(f"[INFO] 🔄 Navigating to page {page_num+1} (start={start_offset})")
        page.goto(paged_url, timeout=45000)

        # ✅ Wait for job list container
        job_list_selector = "div.scaffold-layout__list.jobs-semantic-search-list"
        try:
            page.wait_for_selector(job_list_selector, timeout=10000)
            print("[INFO] ✅ Found job list container.")
        except:
            print(f"[WARN] ⚠️ Job list container not found on page {page_num+1}. Skipping.")
            page_num += 1
            continue

        # ✅ Hover before scrolling
        page.hover(job_list_selector)
        if config.DEBUG:
            print("[DEBUG] 🖱️ Mouse hovered over job list container.")

        # ✅ Human-like scrolling
        scroll_job_list_human_like(page, max_passes=15, pause_between=1.0)

        # ✅ Parse job cards
        job_cards = page.locator("ul.semantic-search-results-list > li")
        job_count = job_cards.count()
        if config.DEBUG:
            print(f"[DEBUG] Found {job_count} <li> elements after scroll on page {page_num+1}.")

        for i in range(job_count):
            job_el = job_cards.nth(i)
            job_data = parse_job_card(job_el)

            if not job_data.get("id"):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping li #{i} — no job ID found.")
                continue
            if job_data.get("already_applied"):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping '{job_data['title']}' — application already submitted.")
                continue
            if job_data["id"] in seen_ids:
                if config.DEBUG:
                    print(f"[DEBUG] 🔁 Already saved job {job_data['id']} — skipping.")
                continue

            job_links.append(job_data["url"])
            seen_ids.add(job_data["id"])
            collected_count += 1

            if config.DEBUG:
                print(f"[DEBUG] ✅ Parsed & added: {job_data}")

            # Early stop if reached limits mid-page
            if collected_count >= max_jobs or (total_jobs and collected_count >= total_jobs):
                break

        save_job_links(job_links, filename)
        print(f"[INFO] ✅ Page {page_num+1} done. Total collected so far: {collected_count}")

        # Next page
        page_num += 1

    print(f"[INFO] 🎯 Finished pagination. Total jobs collected: {collected_count}")
    return job_links

