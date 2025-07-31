# src/easy_apply.py

import time, random, glob, os
import src.config as config
from playwright.sync_api import Page

def step_through_easy_apply(job_page: Page, max_steps: int = 7) -> bool:
    """
    Steps through LinkedIn Easy Apply modal until submission or exit.
    Returns True if application submitted, False otherwise.
    """
    for step in range(1, max_steps + 1):
        time.sleep(random.uniform(0.4, 0.8))  # human-like hesitation

        if config.DEBUG:
            print(f"[DEBUG] 👣 Step {step}: Checking for Next/Review/Submit buttons…")

        if job_page.locator('button[aria-label="Review your application"]').count():
            if config.DEBUG:
                print(f"[DEBUG] 🟦 Found 'Review your application' button at step {step}.")
            print(f"[INFO] Clicking Review (step {step}).")
            job_page.click('button[aria-label="Review your application"]')

        elif job_page.locator('button[aria-label="Submit application"]').count():
            if config.DEBUG:
                print(f"[DEBUG] 🟩 Found 'Submit application' button at step {step}.")
            print(f"[INFO] Clicking Submit (step {step}).")
            job_page.click('button[aria-label="Submit application"]')
            if config.DEBUG:
                print(f"[DEBUG] ✅ Submitted at step {step}.")
            return True  # ✅ Application submitted

        elif job_page.locator('button[aria-label="Continue to next step"]').count():
            if config.DEBUG:
                print(f"[DEBUG] 🟦 Found 'Continue to next step' button at step {step}.")
            print(f"[INFO] Clicking Next (step {step}).")
            job_page.click('button[aria-label="Continue to next step"]')

        else:
            if config.DEBUG:
                print(f"[DEBUG] ⚠️ No actionable button found at step {step}. Stopping iteration.")
            break

        time.sleep(1.2)  # wait for modal to update

    if config.DEBUG:
        print(f"[DEBUG] 🔚 Reached max steps or no more buttons — no submission detected.")
    return False  # 🚨 Exited without submitting



def apply_to_job(job_page: Page, resume_path: str) -> bool:
    """
    Automates LinkedIn's Easy Apply process on a job_page tab, with human-like pauses,
    forces uploading the generated resume (if upload UI is present),
    and pauses before each navigation click in DEBUG mode.
    """
    print("[ACTION] Starting Easy Apply…")

    try:
        # ✅ Locate Easy Apply button inside top-card
        easy_apply_button = job_page.locator('div.jobs-apply-button--top-card button.jobs-apply-button')
        if not easy_apply_button.count():
            print("[ERROR] No Easy Apply button found.")
            return False

        # ✅ Scroll into view and hover before clicking
        easy_apply_button.scroll_into_view_if_needed()
        time.sleep(0.5)
        try:
            easy_apply_button.hover()
            if config.DEBUG:
                print("[DEBUG] 🖱️ Hovered over Easy Apply button.")
        except:
            print("[WARN] Could not hover over Easy Apply button (not fatal).")

        # ✅ Human hesitation before clicking
        delay = random.uniform(0.4, 0.8)
        if config.DEBUG:
            print(f"[DEBUG] ⏳ Pausing {delay:.2f}s before clicking to mimic human hesitation.")
        time.sleep(delay)

        # ✅ Click the Easy Apply button
        if easy_apply_button.is_visible():
            print("[INFO] Easy Apply button visible — clicking.")
            easy_apply_button.click(timeout=5000)
        else:
            print("[WARN] Easy Apply button not visible — forcing click.")
            easy_apply_button.click(force=True, timeout=5000)

        print("[INFO] ✅ Clicked Easy Apply button.")

        # ✅ Wait for Easy Apply modal
        modal_selector = 'div.jobs-easy-apply-modal[role="dialog"], div.artdeco-modal.jobs-easy-apply-modal'
        job_page.wait_for_selector(modal_selector, state="visible", timeout=20000)
        print("[INFO] ✅ Easy Apply modal detected.")

        # ✅ Handle resume upload section
        upload_container = job_page.locator('div.js-jobs-document-upload__container')
        if upload_container.count():
            print("[INFO] 📂 Upload container found.")

            # ✅ Remove any pre-attached resume first
            remove_button = upload_container.locator('button[aria-label*="Remove"]')
            if remove_button.count():
                print("[INFO] 🗙 Pre-attached resume detected — removing it.")
                try:
                    remove_button.click()
                    time.sleep(0.5)
                    print("[INFO] ✅ Old resume removed.")
                except Exception as e:
                    print(f"[WARN] ⚠️ Failed to remove old resume: {e}")

            # ✅ Find the hidden file input
            file_input = upload_container.locator('input[type="file"]')
            if file_input.count():
                # ✅ Find latest generated resume file
                resume_dir = r"C:\Users\Nipply Nathan\Documents\GitHub\resume-gen-auto-applier\output\resumes"
                resume_files = glob.glob(os.path.join(resume_dir, "Borgese_*.pdf"))

                if resume_files:
                    latest_resume = max(resume_files, key=os.path.getmtime)

                    # ✅ Upload via Playwright API (bypasses Explorer popup)
                    file_input.first.set_input_files(latest_resume)
                    print(f"[INFO] 📄 Uploaded generated resume: {latest_resume}")
                else:
                    print("[WARN] ⚠️ No matching resume files found in output/resumes.")
            else:
                print("[WARN] ⚠️ Upload container exists but file input not found!")

        else:
            print("[INFO] ⚠️ No upload section or file input found — LinkedIn may be using pre-attached resume.")
            
        # ✅ Step through Easy Apply process (manual pause for each click)
        step_counter = 1
        while True:
            if config.DEBUG:
                print(f"[DEBUG] 👣 Step {step_counter}: Checking for Next/Review/Submit buttons…")

            # ✅ Buttons to check
            review_btn = job_page.locator('button[aria-label="Review your application"]')
            submit_btn = job_page.locator('button[aria-label="Submit application"]')
            next_btn = job_page.locator('button[aria-label="Continue to next step"]')

            if review_btn.count():
                print(f"[DEBUG] 🟦 Found 'Review your application' button at step {step_counter}.")
                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click REVIEW button…")
                review_btn.click()
            elif submit_btn.count():
                print(f"[DEBUG] 🟩 Found 'Submit application' button at step {step_counter}.")
                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click SUBMIT button…")
                submit_btn.click()
                print(f"[DEBUG] ✅ Submitted at step {step_counter}.")
                break  # stop after submission
            elif next_btn.count():
                print(f"[DEBUG] 🟦 Found 'Next' button at step {step_counter}.")
                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click NEXT button…")
                next_btn.click()
            else:
                print(f"[DEBUG] ❌ No Next/Review/Submit button found at step {step_counter}. Ending loop.")
                break

            time.sleep(1)
            step_counter += 1

        # ✅ Confirm submission
        confirmation = job_page.locator('div.jobs-apply-confirmation')
        if confirmation.count():
            print("[SUCCESS] ✅ Application submitted.")
            success = True
        else:
            print("[WARNING] ⚠️ No confirmation detected after clicking submit.")
            success = False

        # ✅ Close modal if still open
        dismiss_button = job_page.locator('button[aria-label="Dismiss"]')
        if dismiss_button.count():
            dismiss_button.click()
            if config.DEBUG:
                print("[DEBUG] 🗙 Dismissed Easy Apply modal after finishing steps.")
            else:
                print("[INFO] 🗙 Easy Apply modal dismissed.")

        return success

    except Exception as e:
        print(f"[ERROR] Easy Apply failed: {e}")
        try:
            if job_page.locator('button[aria-label="Dismiss"]').count():
                job_page.click('button[aria-label="Dismiss"]')
                if config.DEBUG:
                    print("[DEBUG] 🗙 Dismissed modal after exception.")
        except:
            pass
        return False
