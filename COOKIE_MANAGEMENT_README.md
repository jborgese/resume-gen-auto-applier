# LinkedIn Cookie Management - Solution for Persistent Login

## Problem
LinkedIn's security checkpoint (reCAPTCHA) fails when using automated browsers because:
- Content Security Policy blocks reCAPTCHA resources
- Browser fingerprinting detects automation
- Manual intervention is required

## Solution: Cookie-Based Session Persistence

Instead of logging in every time, we save and reuse your LinkedIn session cookies.

## How It Works

### First Run (Manual Login Required)
1. Run the script normally
2. When it hits the security checkpoint, **DO NOT CLOSE THE BROWSER**
3. **Manually log in** through the browser
4. The script detects the successful login and **saves cookies to `linkedin_cookies.json`**
5. Future runs will use these cookies automatically

### Subsequent Runs (Automatic)
1. Script loads `linkedin_cookies.json`
2. Adds cookies to browser context
3. Navigates to LinkedIn feed - **bypasses login entirely**
4. Goes straight to job search

## Implementation Status

The cookie management system has been partially implemented:

### ✅ Created Files
- `src/cookie_manager.py` - Cookie saving/loading module

### 🔧 Files to Update
- `src/scraper.py` - Integration needs completion

## Manual Implementation Steps

If you want to implement this immediately, add this code to `src/scraper.py`:

### 1. After login success detection (around line 360):

```python
# Save cookies after successful login
if login_detected:
    try:
        cookies = context.cookies()
        cookie_manager.save_cookies(cookies)
        print("[INFO] Saved LinkedIn session cookies for future use")
    except Exception as e:
        logger.warning(f"Failed to save cookies: {e}")
```

### 2. Wrap the entire login block:

```python
# Try to load existing cookies for persistent login
saved_cookies = cookie_manager.load_cookies()
skip_login = False

if saved_cookies:
    try:
        context.add_cookies(saved_cookies)
        page.goto("https://www.linkedin.com/feed/", timeout=config.TIMEOUTS["login"])
        time.sleep(3)
        
        current_url = page.url
        if "/feed" in current_url or "/in/" in current_url:
            print("[INFO] Successfully logged in using saved cookies")
            skip_login = True
    except Exception:
        pass

if not skip_login:
    # ... existing login code ...
```

## Usage

1. **First time**: Run script, manually log in when prompted, cookies are saved
2. **Next time**: Script uses saved cookies, skips login completely
3. **If cookies expire**: Delete `linkedin_cookies.json` and repeat step 1

## Benefits

- ✅ No more reCAPTCHA failures
- ✅ Faster startup (no login wait time)
- ✅ More reliable automation
- ✅ Simulates "stay logged in" behavior

## File Locations

- Cookie file: `resume-gen-auto-applier/linkedin_cookies.json`
- Manager: `src/cookie_manager.py`

## Security Note

Cookies contain your LinkedIn session. Keep `linkedin_cookies.json` secure and never commit it to version control.


