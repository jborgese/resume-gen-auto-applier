# src/easy_apply.py

import time
from playwright.sync_api import Page

def apply_to_job(job_page: Page, resume_path: str) -> bool:
    """
    Automates LinkedIn's Easy Apply process on a job_page tab.

    Steps:
    - Clicks Easy Apply button
    - Uploads tailored resume
    - Clicks through any intermediate steps
    - Submits the application

    :param job_page: Playwright Page object (job posting tab)
    :param resume_path: Path to the tailored resume PDF
    :return: True if application submitted successfully, False otherwise
    """

    print("[ACTION] Starting Easy Apply process...")

    try:
        # ✅ Ensure Easy Apply button exists
        if not job_page.locator('button.jobs-apply-button').count():
            print("[ERROR] No Easy Apply button found on this job listing.")
            return False

        print("[INFO] Clicking Easy Apply button...")
        job_page.click('button.jobs-apply-button', timeout=10000)

        # ✅ Wait for modal to load
        job_page.wait_for_selector('div.jobs-easy-apply-modal', timeout=10000)
        print("[INFO] Easy Apply modal opened.")

        # ✅ Upload tailored resume (if file input is present)
        upload_inputs = job_page.locator('input[type="file"]')
        if upload_inputs.count():
            print(f"[INFO] Found {upload_inputs.count()} file input field(s). Uploading resume...")
            upload_inputs.first.set_input_files(resume_path)
            print("[INFO] Resume uploaded successfully.")
            time.sleep(1)
        else:
            print("[WARNING] No file upload field found. (Might be prefilled or optional.)")

        # ✅ Loop through up to 5 Easy Apply steps (Next → Submit)
        for step in range(1, 6):
            submit_btn = job_page.locator('button[aria-label="Submit application"]')
            next_btn = job_page.locator('button[aria-label="Next"]')

            if submit_btn.count():
                print(f"[INFO] Found Submit button at step {step}. Submitting application...")
                submit_btn.click()
                print("[SUCCESS] Application submitted.")
                time.sleep(2)
                break

            elif next_btn.count():
                print(f"[INFO] Clicking Next button (Step {step})...")
                next_btn.click()
                time.sleep(1)
            else:
                print(f"[WARNING] Neither Next nor Submit found at step {step} — stopping flow.")
                break

        # ✅ Confirm submission (modal closes & confirmation toast appears)
        confirmation = job_page.locator('div.jobs-apply-confirmation')
        if confirmation.count():
            print("[SUCCESS] Application confirmed via confirmation modal.")
            return True

        print("[WARNING] No confirmation modal detected — application may require manual review.")
        return False

    except Exception as e:
        print(f"[ERROR] Easy Apply process failed: {e}")
        return False
