import random, time, json, os
from src.job_parser import parse_job_card, wait_for_job_cards_to_hydrate
from src.shared_utils import FileHandler, TextProcessor, DelayManager
from src.logging_config import get_logger, log_function_call, log_error_context, debug_stop, debug_checkpoint, debug_skip_stops
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
    logger.info("Starting human-like mouse scroll", rounds=rounds)
    for i in range(rounds):
        scroll_amount = random.randint(250, 450)  # small varied increments
        page.mouse.wheel(0, scroll_amount)
        logger.debug("Mouse wheel scroll", round=i+1, total_rounds=rounds, scroll_amount=scroll_amount)

        # ⏳ Wait slightly differently each time
        time.sleep(random.uniform(0.7, 1.4))

        # 🔄 Occasionally scroll up a tiny bit to mimic human checking behavior
        if i % 4 == 3:
            page.mouse.wheel(0, -random.randint(50, 150))
            logger.debug("Small upward scroll for realism")

    logger.info("Finished mouse scrolling")

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
        logger.warning("No job list found for scrolling")
        return

    if config.DEBUG:
        logger.debug("Starting robust scroll", selector=job_list_selector)

    scroll_speed = config.SCROLL_CONFIG["base_speed"]
    loaded_last_round = 0

    for scroll_round in range(max_passes):
        # [OK] Hover over the job list so the scroll wheel applies there
        page.hover(job_list_selector)

        # [OK] Scroll down a bit (simulate human scrolling)
        jitter = random.randint(-config.SCROLL_CONFIG["jitter_range"], config.SCROLL_CONFIG["jitter_range"])
        adjusted_scroll = max(100, scroll_speed + jitter)

        if config.DEBUG:
            logger.debug("Scroll pass", pass_number=scroll_round+1, scroll_amount=adjusted_scroll)

        page.mouse.wheel(0, adjusted_scroll)
        if config.DEBUG:
            logger.debug("Scrolled", amount=adjusted_scroll, base_speed=scroll_speed, jitter=jitter)

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
            logger.debug("Hydrated job cards", hydrated_count=hydrated_count, total_cards=total_cards, scroll_round=scroll_round+1)

        # [OK] If all 25 jobs are hydrated, we can stop early
        if hydrated_count >= 25:
            if config.DEBUG:
                logger.debug("All job cards fully hydrated", scroll_round=scroll_round+1)
            break

        # [OK] Adjust speed based on hydration progress
        if hydrated_count == loaded_last_round:
            scroll_speed = max(config.SCROLL_CONFIG["min_speed"], scroll_speed - 50)
            if config.DEBUG:
                logger.debug("No new hydration - slowing scroll", scroll_speed=scroll_speed)
            time.sleep(1.5)
        else:
            scroll_speed = min(config.SCROLL_CONFIG["max_speed"], scroll_speed + 25)
            if config.DEBUG:
                logger.debug("New jobs hydrated - speeding scroll", scroll_speed=scroll_speed)

        loaded_last_round = hydrated_count

    # [OK] Final hydration summary
    job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
    hydrated_count = 0
    for i in range(job_cards.count()):
        if job_cards.nth(i).locator(config.LINKEDIN_SELECTORS["job_search"]["job_wrapper"]).count():
            hydrated_count += 1

    if config.DEBUG:
        logger.debug("Final hydration", hydrated_count=hydrated_count, total_cards=job_cards.count())


from typing import Optional

def collect_job_links_with_pagination(page, base_url: str, max_jobs: Optional[int] = None, start_fresh: bool = False) -> list:
    """
    Collect job links with pagination support and human-like scrolling.
    Returns a list of job URLs.
    """
    # Debug checkpoint at function start
    debug_checkpoint("collect_job_links_start", 
                    base_url=base_url,
                    max_jobs=max_jobs,
                    start_fresh=start_fresh)
    
    # Debug stop before job collection
    if not debug_skip_stops():
        debug_stop("About to collect job links with pagination", 
                  base_url=base_url,
                  max_jobs=max_jobs,
                  start_fresh=start_fresh)
    
    from typing import Optional
    
    logger.info("Starting job link collection", base_url=base_url, max_jobs=max_jobs)
    
    # Load existing job links if not starting fresh
    existing_links = set()
    if not start_fresh:
        existing_links = load_existing_job_links()
        logger.info("Loaded existing job links", count=len(existing_links))
    
    # Debug checkpoint after loading existing links
    debug_checkpoint("existing_links_loaded", 
                    existing_count=len(existing_links))
    
    all_job_links = list(existing_links)
    
    # Navigate to the job search page
    try:
        page.goto(base_url, timeout=config.TIMEOUTS["search_page"])
        logger.info("Navigated to job search page", url=base_url)
        
        # Debug checkpoint after navigation
        debug_checkpoint("navigation_complete", 
                        current_url=page.url)
        
        # Wait for job cards to load
        wait_for_job_cards_to_hydrate(page)
        
        # Debug checkpoint after job cards loaded
        debug_checkpoint("job_cards_loaded")
        
    except Exception as e:
        logger.error("Failed to navigate to job search page", error=str(e))
        return all_job_links
    
    # Human-like scrolling to load more jobs
    scroll_job_list_human_like(page)
    
    # Debug checkpoint after scrolling
    debug_checkpoint("scrolling_complete")
    
    # Collect job links from current page
    job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
    total_cards = job_cards.count()
    
    logger.info("Found job cards", count=total_cards)
    
    # Debug checkpoint before parsing job cards
    debug_checkpoint("parsing_job_cards_start", 
                    total_cards=total_cards)
    
    new_links_count = 0
    for i in range(total_cards):
        try:
            job_card = job_cards.nth(i)
            job_data = parse_job_card(job_card)
            
            if job_data and job_data.get("url"):
                job_url = job_data["url"]
                if job_url not in existing_links:
                    all_job_links.append(job_url)
                    new_links_count += 1
                    
                    # Check if we've reached max_jobs limit
                    if max_jobs and len(all_job_links) >= max_jobs:
                        logger.info("Reached maximum jobs limit", max_jobs=max_jobs)
                        break
                        
        except Exception as e:
            logger.warning("Failed to parse job card", index=i, error=str(e))
            continue
    
    # Debug checkpoint after parsing
    debug_checkpoint("job_cards_parsed", 
                    new_links_found=new_links_count,
                    total_links=len(all_job_links))
    
    # Save updated job links
    if new_links_count > 0:
        save_job_links(all_job_links)
        logger.info("Saved job links", total_count=len(all_job_links), new_count=new_links_count)
    
    # Debug checkpoint at function end
    debug_checkpoint("collect_job_links_complete", 
                    total_links=len(all_job_links),
                    new_links=new_links_count)
    
    return all_job_links
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

    logger.info("Collecting jobs using pagination")

    filename = "job_urls.json"

    # [OK] Handle start_fresh
    if start_fresh and os.path.exists(filename):
        os.remove(filename)
        logger.info("Deleted old job URLs file", filename=filename)

    # [OK] Load any existing saved jobs
    job_links = list(load_existing_job_links(filename)) if os.path.exists(filename) else []
    seen_ids = {url.split("/")[-2] for url in job_links}

    logger.info("Loaded previously saved job URLs", count=len(job_links))

    # [OK] Check if we already have enough jobs - skip scraping if so
    if len(job_links) >= max_jobs:
        logger.info("Already have enough jobs - skipping scraping", job_count=len(job_links), max_jobs=max_jobs)
        return job_links

    # [OK] Detect total job count from the search page
    try:
        page.wait_for_selector(config.LINKEDIN_SELECTORS["job_search"]["total_jobs"], timeout=config.TIMEOUTS["total_jobs"])
        total_jobs_text = page.inner_text(config.LINKEDIN_SELECTORS["job_search"]["total_jobs"])
        total_jobs = int("".join(filter(str.isdigit, total_jobs_text)))
    except:
        logger.warning("Could not find total job count - defaulting to 1 page")
        total_jobs = 0

    logger.info("Total jobs listed", total_jobs=total_jobs if total_jobs else "Unknown")

    jobs_per_page = 25
    collected_count = len(job_links)  # Start with existing jobs count
    page_num = 0

    while collected_count < max_jobs and (not total_jobs or collected_count < total_jobs):
        start_offset = page_num * jobs_per_page
        paged_url = f"{base_url}&start={start_offset}"

        logger.info("Navigating to page", page_number=page_num+1, start_offset=start_offset)
        page.goto(paged_url, timeout=config.TIMEOUTS["search_page"])

        # [OK] Wait for job list container
        job_list_selector = config.LINKEDIN_SELECTORS["job_search"]["job_list"]
        try:
            page.wait_for_selector(job_list_selector, timeout=config.TIMEOUTS["job_list"])
            logger.info("Found job list container")
        except:
            logger.warning("Job list container not found", page_number=page_num+1)
            page_num += 1
            continue

        # [OK] Hover before scrolling
        page.hover(job_list_selector)
        if config.DEBUG:
            logger.debug("Mouse hovered over job list container")

        # [OK] Human-like scrolling
        scroll_job_list_human_like(page, max_passes=config.RETRY_CONFIG["max_scroll_passes"], pause_between=config.SCROLL_CONFIG["pause_between"])

        # [OK] Parse job cards
        job_cards = page.locator(config.LINKEDIN_SELECTORS["job_search"]["job_cards"])
        job_count = job_cards.count()
        if config.DEBUG:
            logger.debug("Found job elements", count=job_count, page_number=page_num+1)

        for i in range(job_count):
            job_el = job_cards.nth(i)
            job_data = parse_job_card(job_el)

            if not job_data.get("id"):
                if config.DEBUG:
                    logger.debug("Skipping job - no job ID found", li_index=i)
                continue
            if job_data.get("already_applied"):
                if config.DEBUG:
                    logger.debug("Skipping job - already applied", title=job_data['title'])
                continue
            if job_data["id"] in seen_ids:
                if config.DEBUG:
                    logger.debug("Already saved job - skipping", job_id=job_data["id"])
                continue

            job_links.append(job_data["url"])
            seen_ids.add(job_data["id"])
            collected_count += 1

            if config.DEBUG:
                logger.debug("Parsed and added job", job_data=job_data)

            # Early stop if reached limits mid-page
            if collected_count >= max_jobs or (total_jobs and collected_count >= total_jobs):
                break

        save_job_links(job_links, filename)
        logger.info("Page completed", page_number=page_num+1, collected_count=collected_count)

        # Next page
        page_num += 1

    logger.info("Finished pagination", total_collected=collected_count)
    return job_links

