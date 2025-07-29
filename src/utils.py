import time

def clean_text(text: str) -> str:
    """Normalize scraped text by removing excessive newlines and trimming spaces."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)

def detect_scroll_target(page):
    """
    Detects if LinkedIn's job list container exists and is scrollable.
    Returns the best selector to scroll (either job list or window).
    """

    job_list_selector = 'ul.jobs-search__results-list'

    try:
        found = page.evaluate(f"""
            () => {{
                const el = document.querySelector('{job_list_selector}');
                if (el && el.scrollHeight > el.clientHeight) {{
                    return true;
                }} else {{
                    return false;
                }}
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


def scroll_job_list(page, rounds: int = 5, delay: int = 2):
    """
    Smart scroll: attempts to scroll the LinkedIn job results sidebar (if found),
    otherwise scrolls the entire window.

    :param page: Playwright page object
    :param rounds: Number of scroll attempts
    :param delay: Delay (seconds) between scrolls
    """
    print(f"[INFO] 🔍 Starting smart scrolling for {rounds} rounds...")

    # ✅ Dynamically detect which container to scroll
    scroll_targets = [
        "div.jobs-search-results-list",         # most common LinkedIn container
        "ul.jobs-search-results-list",          # UL variant
        "ul.jobs-search__results-list",         # older LinkedIn class
        "div.scaffold-layout__list-container"   # generic fallback
    ]

    scroll_target = None
    for selector in scroll_targets:
        if page.locator(selector).count() > 0:
            scroll_target = selector
            break

    if scroll_target:
        print(f"[INFO] ✅ Detected scrollable container: {scroll_target}")
    else:
        print("[WARNING] ⚠️ No sidebar container found — will scroll full page instead.")

    for i in range(rounds):
        try:
            if scroll_target:
                # ✅ Scroll inside job list sidebar
                scrolled = page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{scroll_target}');
                        if (el) {{
                            const before = el.scrollTop;
                            el.scrollBy(0, el.scrollHeight);
                            return before !== el.scrollTop;  // check if scroll position changed
                        }}
                        return false;
                    }}
                """)

                if scrolled:
                    print(f"[INFO] ↕️ Scrolled job list container (round {i+1}/{rounds})")
                else:
                    print(f"[DEBUG] ⚠️ Scroll position didn’t change (round {i+1}) — container may already be at bottom.")
            else:
                # ✅ Scroll entire page
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                print(f"[INFO] ↕️ Scrolled main window (round {i+1}/{rounds})")

        except Exception as e:
            print(f"[WARNING] ❗ Scroll attempt {i+1} failed: {e}")
            print("[INFO] 🔄 Fallback: window scroll")
            page.evaluate("window.scrollBy(0, window.innerHeight)")

        # ✅ Pause for lazy loading
        page.wait_for_timeout(delay * 1000)

    # ✅ Final aggressive scroll (LinkedIn sometimes loads jobs slowly)
    print("[INFO] ⏬ Final aggressive scroll to ensure all jobs load.")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    page.wait_for_timeout(2000)
    print("[INFO] ✅ Finished smart scrolling.")
