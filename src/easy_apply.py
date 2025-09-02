# src/easy_apply.py

import json
import time, random, glob, os
import src.config as config
from playwright.sync_api import Page
import yaml
import os

YAML_PATH = "personal_info.yaml"

def step_through_easy_apply(job_page: Page) -> bool:
    """
    Steps through the LinkedIn Easy Apply modal, handling resume uploads,
    additional questions, and ensuring we don't accidentally follow companies.
    """
    for step in range(1, 8):
        if config.DEBUG:
            print(f"[DEBUG] 👣 Step {step}: Checking for buttons and form elements…")

        # ✅ If a resume upload section appears, handle it
        upload_section = job_page.locator('label.jobs-document-upload__upload-button')
        if upload_section.count():
            if config.DEBUG:
                print(f"[DEBUG] 📂 Resume upload section detected at step {step}.")
            check_and_upload_resume(job_page)

        # ✅ Handle Additional Questions (radio, dropdown, etc.)
        handle_additional_questions(job_page)

        # ✅ Footer buttons
        footer = job_page.locator("footer")
        submit_btn = footer.locator('button[aria-label="Submit application"]')
        review_btn = footer.locator('button[aria-label="Review your application"]')
        next_btn = footer.locator('button[aria-label="Continue to next step"]')

        # 🔽 *** Special handling for SUBMIT step ***
        if submit_btn.count():
            # ✅ Uncheck “Follow company” if it exists before clicking Submit
            follow_checkbox = job_page.locator("input#follow-company-checkbox")
            if follow_checkbox.count():
                try:
                    if follow_checkbox.is_checked():
                        try:
                            print("[DEBUG] 🔄 Clicking label to uncheck…")
                            job_page.locator("label[for='follow-company-checkbox']").click()
                        except:
                            print("[WARN] ⚠️ Label click failed, forcing via JS.")
                            job_page.evaluate("el => el.checked = false", follow_checkbox)
                    else:
                        print("[DEBUG] ✅ Follow box already unchecked.")
                except Exception as e:
                    print(f"[WARN] ⚠️ Could not verify/uncheck follow box: {e}")

            # ✅ Now submit the application
            print(f"[DEBUG] 🟩 Found 'Submit application' button at step {step}.")
            submit_btn.click()
            time.sleep(1.2)
            print(f"[DEBUG] ✅ Application submitted at step {step}.")
            return True

        # 🔽 *** Handle REVIEW ***
        elif review_btn.count():
            print(f"[DEBUG] 🟦 Found 'Review your application' button at step {step}.")
            review_btn.click()
            time.sleep(1)
            continue

        # 🔽 *** Handle NEXT ***
        elif next_btn.count():
            print(f"[DEBUG] 🟨 Found 'Next' button at step {step}.")
            next_btn.click()
            time.sleep(1)
            continue

        else:
            if config.DEBUG:
                print(f"[DEBUG] ⚠️ No Next/Review/Submit button found at step {step}. Breaking out.")
            break

    return False

# src/easy_apply.py

import time, random, glob, os, yaml
import src.config as config
from playwright.sync_api import Page

YAML_PATH = "personal_info.yaml"

# --------------------------
# YAML Helpers
# --------------------------
def load_personal_info():
    """Load or initialize the YAML with a guaranteed 'questions' section."""
    if os.path.exists(YAML_PATH):
        with open(YAML_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # ✅ Guarantee the `questions` key always exists
    if "questions" not in data:
        data["questions"] = {}

    return data


def save_personal_info(data):
    """Save the updated YAML data, making sure 'questions' exists."""
    if "questions" not in data:
        data["questions"] = {}  # safety net
    with open(YAML_PATH, "w") as f:
        yaml.safe_dump(data, f)


def save_answer_to_yaml(question: str, answer: str):
    """Save an answered question into YAML."""
    data = load_personal_info()
    if "questions" not in data:
        data["questions"] = {}
    data["questions"][question] = answer
    save_personal_info(data)

# --------------------------
# Answer Logic
# --------------------------
def determine_answer(question: str) -> str:
    """
    Basic keyword-based logic to infer a safe & intelligent default answer.
    """
    q_lower = question.lower()

    if "sponsorship" in q_lower:
        return "No"
    if "work in an onsite" in q_lower or "work onsite" in q_lower:
        return "Yes"
    if "relocate" in q_lower:
        return "Yes"
    if "authorized to work" in q_lower:
        return "Yes"
    if "years of experience" in q_lower:
        return "Yes"
    if "background check" in q_lower:
        return "Yes"
    if "convicted" in q_lower:
        return "No"

    return "Yes"  # fallback default

# --------------------------
# Resume Upload
# --------------------------
def check_and_upload_resume(job_page):
    """
    Upload the most recent generated resume if an upload section is present.
    Only targets the resume upload field (ignores cover letter).
    """
    upload_button = job_page.locator('label.jobs-document-upload__upload-button')
    if not upload_button.count():
        if config.DEBUG:
            print("[DEBUG] 🟦 No 'Upload resume' button on this step.")
        return

    print("[INFO] 📄 'Upload resume' button detected. Uploading resume...")

    # ✅ Only select the resume upload field, not the cover letter
    file_input = job_page.locator(
        "div.js-jobs-document-upload__container input[type='file'][id*='upload-resume']"
    )

    if file_input.count() != 1:
        print(f"[ERROR] ❌ Found {file_input.count()} resume inputs — expected 1.")
        return

    # ✅ Find the newest resume file
    resume_dir = r"C:\Users\Nipply Nathan\Documents\GitHub\resume-gen-auto-applier\output\resumes"
    resume_files = glob.glob(os.path.join(resume_dir, "Borgese_*.pdf"))
    if not resume_files:
        print("[ERROR] ❌ No resume files found in output/resumes.")
        return

    latest_resume = max(resume_files, key=os.path.getmtime)

    # ✅ Upload to LinkedIn resume field
    file_input.set_input_files(latest_resume)

    print(f"[INFO] ✅ Resume uploaded: {latest_resume}")
    time.sleep(2)


# --------------------------
# Additional Questions (Radio + Dropdown)
# --------------------------
def handle_additional_questions(job_page):
    """
    Detect and intelligently answer both radio button and dropdown questions.
    Answers are stored in personal_info.yaml for re-use.
    """
    data = load_personal_info()

    # --- RADIO QUESTIONS ---
    for fieldset in job_page.locator("fieldset[data-test-form-builder-radio-button-form-component='true']").all():
        try:
            # Get the question text from the legend
            question_text = fieldset.locator("legend").inner_text().strip()
            saved_answer = data["questions"].get(question_text)

            # ✅ 1. Check if LinkedIn already pre-filled an answer
            pre_selected = None
            radio_inputs = fieldset.locator("input[type='radio']")
            for i in range(radio_inputs.count()):
                if radio_inputs.nth(i).is_checked():
                    pre_selected = radio_inputs.nth(i).get_attribute("value")
                    break

            if pre_selected:
                print(f"[INFO] ✅ '{question_text}' already answered with '{pre_selected}' – skipping.")
                continue  # 🚀 Skip YAML lookup and move on

            # ✅ 2. No prefill? Look for saved YAML answer
            if not saved_answer:
                print(f"[DEBUG] 🛑 No saved answer for radio Q '{question_text}' – skipping.")
                continue

            # ✅ Find the radio input that matches the saved answer
            radio_input = fieldset.locator(f"input[type='radio'][value='{saved_answer}']")
            if not radio_input.count():
                print(f"[WARN] ⚠️ Could not find radio option '{saved_answer}' for '{question_text}'")
                continue

            # ✅ Get the label tied to this radio
            radio_id = radio_input.get_attribute("id")
            if not radio_id:
                print(f"[WARN] ⚠️ Radio input missing 'id' for '{question_text}'")
                continue

            label = job_page.locator(f"label[for='{radio_id}']")
            if label.count():
                try:
                    label.scroll_into_view_if_needed()
                    time.sleep(0.2)  # Small pause for UI stability
                    label.click(timeout=3000)
                    print(f"[INFO] ✅ Selected '{saved_answer}' for radio Q: '{question_text}'")
                except Exception as e:
                    print(f"[WARN] ⚠️ Normal click failed for '{saved_answer}' – using JS click. ({e})")
                    job_page.evaluate("el => el.click()", label)
                    print(f"[INFO] ✅ Forced JS click for '{saved_answer}' on '{question_text}'")
            else:
                print(f"[WARN] ⚠️ No label found for radio '{saved_answer}' on '{question_text}'")

        except Exception as e:
            print(f"[ERROR] ❌ Radio handling failed for a question: {e}")

    # --- DROPDOWN QUESTIONS ---
    dropdowns = job_page.locator("select.fb-dash-form-element__select-dropdown")
    ignore_keywords = ["phone", "email address", "country code"]
    SKIP_QUESTIONS = [
        "email address", 
        "phone country code", 
        "mobile phone number",
        "first name",
        "last name",
        "city",
        "address"
    ]
    for i in range(dropdowns.count()):
        dropdown = dropdowns.nth(i)

        # Extract question text (label preceding the select)
        label_locator = dropdown.locator('xpath=preceding-sibling::label[1]')
        question_text = label_locator.inner_text().strip() if label_locator.count() else "Unknown question"

        # ✅ Skip pre-filled LinkedIn profile fields
        if any(skip in question_text for skip in SKIP_QUESTIONS):
            if config.DEBUG:
                print(f"[DEBUG] ⏭️ Skipping '{question_text}' – LinkedIn profile field.")
            continue
        
        if any(word in question_text for word in ignore_keywords):
            print(f"[INFO] ⏭️ Skipping '{question_text}' — handled by LinkedIn profile.")
            continue

        selected_value = dropdowns.nth(i).input_value()
        if selected_value and selected_value != "Select an option":
            if config.DEBUG:
                print(f"[DEBUG] ✅ '{question_text}' already has value '{selected_value}' – skipping.")
            continue

        # Use saved or new answer
        saved_answer = data["questions"].get(question_text)
        if not saved_answer:
            saved_answer = determine_answer(question_text)
            save_answer_to_yaml(question_text, saved_answer)
            print(f"[INFO] ✅ Determined answer for dropdown Q: '{question_text}' → '{saved_answer}'")
        else:
            if config.DEBUG:
                print(f"[DEBUG] 🔁 Using saved answer for dropdown Q '{question_text}': {saved_answer}")

        # Select dropdown option
        try:
            dropdown.select_option(saved_answer)
            print(f"[INFO] 🏷 Dropdown Q: '{question_text}' → '{saved_answer}'")
        except Exception as e:
            # Try to print available options if possible
            try:
                options = dropdown.locator("option")
                option_texts = [options.nth(j).inner_text().strip() for j in range(options.count())]
                print(f"[WARN] ⚠️ Could not select '{saved_answer}' for '{question_text}': {e}")
                print(f"[WARN] ⚠️ Available options for '{question_text}': {option_texts}")
            except Exception as opt_e:
                print(f"[WARN] ⚠️ Could not select '{saved_answer}' for '{question_text}': {e}")
                print(f"[WARN] ⚠️ Also failed to retrieve options: {opt_e}")

# --------------------------
# Main Easy Apply Flow
# --------------------------
def apply_to_job(job_page: Page, resume_path: str, job_url: str) -> bool:
    """
    Automates LinkedIn's Easy Apply process:
    - Clicks Easy Apply button
    - Uploads latest resume if prompted
    - Answers radio & dropdown questions
    - Ensures 'Follow company' is unchecked before submission
    - Saves answers to YAML for re-use
    ✅ Cleans up job_urls.json (removes completed or already-applied jobs)
    """
    print("[ACTION] Starting Easy Apply…")

    def remove_from_json(url: str):
        """Removes a job URL from job_urls.json so it doesn't get retried."""
        try:
            if not os.path.exists("job_urls.json"):
                return
            with open("job_urls.json", "r") as f:
                urls = json.load(f)
            if url in urls:
                urls.remove(url)
                with open("job_urls.json", "w") as f:
                    json.dump(urls, f, indent=2)
                print(f"[INFO] 🗑️ Removed {url} from job_urls.json.")
        except Exception as e:
            print(f"[WARN] ⚠️ Could not remove {url} from job_urls.json: {e}")

    try:
        # ✅ Check if the job was already applied for
        applied_banner = job_page.locator("div.post-apply-timeline__content")
        if applied_banner.count():
            text = applied_banner.inner_text().strip()
            if "Application submitted" in text:
                print("[INFO] ✅ Already applied for this job. Skipping Easy Apply.")
                remove_from_json(job_url)
                return False

        # ✅ Find & click Easy Apply button
        easy_apply_button = job_page.locator('div.jobs-apply-button--top-card button.jobs-apply-button')
        if not easy_apply_button.count():
            print("[ERROR] ❌ No Easy Apply button found.")
            remove_from_json(job_url)
            return False

        easy_apply_button.scroll_into_view_if_needed()
        time.sleep(0.5)
        try:
            easy_apply_button.hover()
            if config.DEBUG:
                print("[DEBUG] 🖱️ Hovered over Easy Apply button.")
        except:
            print("[WARN] ⚠️ Could not hover over Easy Apply button.")

        delay = random.uniform(0.4, 0.8)
        if config.DEBUG:
            print(f"[DEBUG] ⏳ Pausing {delay:.2f}s before clicking Easy Apply.")
        time.sleep(delay)

        easy_apply_button.click(timeout=5000)
        print("[INFO] ✅ Easy Apply button clicked.")

        # ✅ Wait for modal
        modal_selector = 'div.jobs-easy-apply-modal[role="dialog"], div.artdeco-modal.jobs-easy-apply-modal'
        job_page.wait_for_selector(modal_selector, state="visible", timeout=20000)
        print("[INFO] ✅ Easy Apply modal detected.")

        # ✅ Iterate through modal steps
        step_counter = 1
        max_steps = 10  # Safeguard against infinite loops
        while step_counter <= max_steps:
            if config.DEBUG:
                print(f"[DEBUG] 👣 Step {step_counter}/{max_steps}: Checking for questions, resume uploads, and buttons…")

            # Handle resume upload (every step)
            check_and_upload_resume(job_page)

            # Handle radio & dropdown questions
            handle_additional_questions(job_page)

            # ✅ Footer buttons
            footer = job_page.locator("footer")
            submit_btn = footer.locator('button[aria-label="Submit application"]')
            review_btn = footer.locator('button[aria-label="Review your application"]')
            next_btn = footer.locator('button[aria-label="Continue to next step"]')

            if submit_btn.count():
                # ✅ Make sure "Follow company" is unchecked
                follow_checkbox = job_page.locator("input#follow-company-checkbox")
                if follow_checkbox.count():
                    try:
                        if follow_checkbox.is_checked():
                            try:
                                print("[DEBUG] 🔄 Clicking label to uncheck…")
                                job_page.locator("label[for='follow-company-checkbox']").click()
                            except:
                                print("[WARN] ⚠️ Label click failed, forcing via JS.")
                                job_page.evaluate("el => el.checked = false", follow_checkbox)
                        else:
                            print("[DEBUG] ✅ Follow box already unchecked.")
                    except Exception as e:
                        print(f"[WARN] ⚠️ Could not verify/uncheck follow box: {e}")

                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click SUBMIT…")
                submit_btn.click()
                print("[INFO] ✅ Submitted application.")
                break

            elif review_btn.count():
                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click REVIEW…")
                review_btn.click()
                print("[INFO] 🔄 Clicked Review button.")
            elif next_btn.count():
                if config.DEBUG:
                    input("👉 [PAUSE] Press Enter to click NEXT…")
                next_btn.click()
                print(f"[INFO] ➡️ Clicked Next button (step {step_counter}/{max_steps}).")

            else:
                print(f"[DEBUG] ⚠️ No Next/Review/Submit button at step {step_counter}. Stopping.")
                break
    
            # Check if we hit the max steps limit
            if step_counter > max_steps:
                print(f"[ERROR] ❌ Reached maximum steps ({max_steps}) without completion. Possible infinite loop detected.")
                remove_from_json(job_url)
                return False
                break

            time.sleep(1)
            step_counter += 1

        # ✅ Confirm submission (LinkedIn sometimes refreshes the job page after submission)
        success = False
        try:
            job_page.wait_for_timeout(3000)  # small wait for DOM to refresh

            # 1️⃣ Check for confirmation banner
            if job_page.locator('div.jobs-apply-confirmation').count() > 0:
                print("[SUCCESS] ✅ Application submitted (confirmation banner found).")
                success = True

            # 2️⃣ Check for 'Application submitted' timeline content
            elif job_page.locator('div.post-apply-timeline__content').filter(has_text="Application submitted").count() > 0:
                print("[SUCCESS] ✅ Application submitted ('Application submitted' text found).")
                success = True

            # 3️⃣ Check for 'Submitted resume' download link
            elif job_page.locator('a[aria-label="Download your submitted resume"]').count() > 0:
                print("[SUCCESS] ✅ Application submitted ('Submitted resume' link present).")
                success = True

            # 4️⃣ Fallback: check if button now says 'Applied'
            elif job_page.locator('button.jobs-apply-button[aria-label*="Applied"]').count() > 0:
                print("[SUCCESS] ✅ Application submitted (button now shows 'Applied').")
                success = True

            else:
                print("[WARNING] ⚠️ No explicit confirmation detected — submission status uncertain.")
                success = False  # <-- mark as failed instead of assuming success

        except Exception as e:
            print(f"[WARN] ⚠️ Could not confirm submission visually: {e}")
            success = False
        
                # ✅ Remove from JSON only if verified success
        if success:
            remove_from_json(job_url)



        # ✅ Close modal
        # Try dismissing any modals without crashing
        try:
            dismiss_buttons = job_page.locator("button[aria-label='Dismiss']")
            if dismiss_buttons.count() > 0:
                dismiss_buttons.first.click()
                print("[DEBUG] ✅ Clicked first dismiss button.")
            else:
                print("[DEBUG] ❎ No dismiss button found.")
        except Exception as e:
            print(f"[WARN] ⚠️ Could not dismiss modal: {e}")
        return success

    except Exception as e:
        print(f"[ERROR] ❌ Easy Apply failed: {e}")
        remove_from_json(job_url)   # ✅ REMOVE even on failure so bad jobs don’t clog
        try:
            if job_page.locator('button[aria-label="Dismiss"]').count():
                job_page.click('button[aria-label="Dismiss"]')
        except:
            pass
        return False
