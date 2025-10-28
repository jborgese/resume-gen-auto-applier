# src/easy_apply.py

import json
import time, random, glob, os
import src.config as config
from playwright.sync_api import Page
import yaml
import os
from src.human_behavior import HumanBehavior

YAML_PATH = str(config.FILE_PATHS["personal_info"])

def debug_pause(message: str = "", duration: float = 0) -> None:
    """
    Pause for debugging purposes. In DEBUG mode, waits for user input.
    Otherwise, sleeps for the specified duration.
    
    Args:
        message: Optional message to display during pause
        duration: Duration to sleep if not in DEBUG mode (default: 0 for user input)
    """
    if config.DEBUG:
        if message:
            print(f"[DEBUG] ⏸️  {message}")
        print("[DEBUG] Press Enter to continue...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print("[DEBUG] Continuing automatically...")
    elif duration > 0:
        time.sleep(duration)

def step_through_easy_apply(job_page: Page) -> bool:
    """
    Steps through the LinkedIn Easy Apply modal, handling resume uploads,
    additional questions, and ensuring we don't accidentally follow companies.
    """
    # Debug pause before starting Easy Apply steps
    if config.DEBUG:
        print("[DEBUG] ⏸️  About to start stepping through Easy Apply modal")
        print("[DEBUG] Press Enter to continue...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print("[DEBUG] Continuing automatically...")
    
    for step in range(1, 8):
        if config.DEBUG:
            print(f"[DEBUG] Step {step}: Checking for buttons and form elements")
            print(f"[DEBUG] ⏸️  Step {step} - Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")

        # [OK] If a resume upload section appears, handle it
        upload_section = job_page.locator(config.LINKEDIN_SELECTORS["resume_upload"]["upload_button"])
        if upload_section.count():
            if config.DEBUG:
                print(f"[DEBUG] Resume upload section detected at step {step}.")
                print("[DEBUG] ⏸️  About to handle resume upload - Press Enter to continue...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("[DEBUG] Continuing automatically...")
            check_and_upload_resume(job_page)

        # [OK] Handle Additional Questions (radio, dropdown, etc.)
        if config.DEBUG:
            print(f"[DEBUG] ⏸️  Step {step} - About to handle additional questions - Press Enter to continue...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        handle_additional_questions(job_page)

        # [OK] Footer buttons
        footer = job_page.locator("footer")
        submit_btn = footer.locator(config.LINKEDIN_SELECTORS["easy_apply"]["submit"])
        review_btn = footer.locator(config.LINKEDIN_SELECTORS["easy_apply"]["review"])
        next_btn = footer.locator(config.LINKEDIN_SELECTORS["easy_apply"]["next"])

        # [SUBMIT] *** Special handling for SUBMIT step ***
        if submit_btn.count():
            # [OK] Uncheck "Follow company" if it exists before clicking Submit
            follow_checkbox = job_page.locator(config.LINKEDIN_SELECTORS["easy_apply"]["follow_checkbox"])
            if follow_checkbox.count():
                try:
                    if follow_checkbox.is_checked():
                        try:
                            print("[DEBUG] [RETRY] Clicking label to uncheck")
                            job_page.locator(config.LINKEDIN_SELECTORS["easy_apply"]["follow_label"]).click()
                        except:
                            print("[WARN] [WARN] Label click failed, forcing via JS.")
                            job_page.evaluate("el => el.checked = false", follow_checkbox)
                    else:
                        print("[DEBUG] [OK] Follow box already unchecked.")
                except Exception as e:
                    print(f"[WARN] [WARN] Could not verify/uncheck follow box: {e}")

            # [OK] Now submit the application
            print(f"[DEBUG] 🟩 Found 'Submit application' button at step {step}.")
            
            # Human-like hesitation before final submit
            HumanBehavior.simulate_hesitation(0.5, 1.2)
            HumanBehavior.human_like_click(job_page, submit_btn, move_to_element=True)
            time.sleep(1.2)
            print(f"[DEBUG] [OK] Application submitted at step {step}.")
            return True

        # 🔽 *** Handle REVIEW ***
        elif review_btn.count():
            print(f"[DEBUG] 🟦 Found 'Review your application' button at step {step}.")
            HumanBehavior.simulate_hesitation(0.3, 0.7)
            HumanBehavior.human_like_click(job_page, review_btn, move_to_element=True)
            time.sleep(1)
            continue

        # 🔽 *** Handle NEXT ***
        elif next_btn.count():
            print(f"[DEBUG] 🟨 Found 'Next' button at step {step}.")
            HumanBehavior.simulate_hesitation(0.2, 0.6)
            HumanBehavior.human_like_click(job_page, next_btn, move_to_element=True)
            time.sleep(1)
            continue

        else:
            if config.DEBUG:
                print(f"[DEBUG] [WARN] No Next/Review/Submit button found at step {step}. Breaking out.")
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

    # [OK] Guarantee the `questions` key always exists
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
    upload_button = job_page.locator(config.LINKEDIN_SELECTORS["resume_upload"]["upload_button"])
    if not upload_button.count():
        if config.DEBUG:
            print("[DEBUG] 🟦 No 'Upload resume' button on this step.")
        return

    print("[INFO] [RESUME] 'Upload resume' button detected. Uploading resume...")
    
    if config.DEBUG:
        debug_pause("Resume upload button detected, preparing to upload...", 0.3)

    # [OK] Only select the resume upload field, not the cover letter
    file_input = job_page.locator(config.LINKEDIN_SELECTORS["resume_upload"]["file_input"])

    if file_input.count() != 1:
        print(f"[ERROR] [ERROR] Found {file_input.count()} resume inputs  expected 1.")
        return

    # [OK] Find the newest resume file
    resume_dir = str(config.FILE_PATHS["resumes_dir"])
    resume_files = glob.glob(os.path.join(resume_dir, "Borgese_*.pdf"))
    if not resume_files:
        print("[ERROR] [ERROR] No resume files found in output/resumes.")
        return

    latest_resume = max(resume_files, key=os.path.getmtime)
    
    if config.DEBUG:
        print(f"[DEBUG] 📄 Uploading resume: {latest_resume}")

    # [OK] Upload to LinkedIn resume field
    file_input.set_input_files(latest_resume)

    print(f"[INFO] [OK] Resume uploaded: {latest_resume}")
    debug_pause("Resume uploaded, waiting for confirmation...", 2.0)


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
    try:
        radio_fieldsets = job_page.locator(config.LINKEDIN_SELECTORS["form_fields"]["radio_fieldset"])
        if config.DEBUG:
            print(f"[DEBUG] Found {radio_fieldsets.count()} radio fieldsets")
            if radio_fieldsets.count() > 0:
                debug_pause(f"Processing {radio_fieldsets.count()} radio questions...", 0.2)
        
        for fieldset in radio_fieldsets.all():
            try:
                # Get the question text from the legend
                question_text = fieldset.locator("legend").inner_text().strip()
                saved_answer = data["questions"].get(question_text)

                # [OK] 1. Check if LinkedIn already pre-filled an answer
                pre_selected = None
                radio_inputs = fieldset.locator(config.LINKEDIN_SELECTORS["form_fields"]["radio_input"])
                for i in range(radio_inputs.count()):
                    if radio_inputs.nth(i).is_checked():
                        pre_selected = radio_inputs.nth(i).get_attribute("value")
                        break

                if pre_selected:
                    print(f"[INFO] [OK] '{question_text}' already answered with '{pre_selected}'  skipping.")
                    continue  # [SKIP] Skip YAML lookup and move on

                # [OK] 2. No prefill? Look for saved YAML answer
                if not saved_answer:
                    print(f"[DEBUG] 🛑 No saved answer for radio Q '{question_text}'  skipping.")
                    continue

                # [OK] Find the radio input that matches the saved answer
                radio_input = fieldset.locator(f"input[type='radio'][value='{saved_answer}']")
                if not radio_input.count():
                    print(f"[WARN] [WARN] Could not find radio option '{saved_answer}' for '{question_text}'")
                    continue

                # [OK] Get the label tied to this radio
                radio_id = radio_input.get_attribute("id")
                if not radio_id:
                    print(f"[WARN] [WARN] Radio input missing 'id' for '{question_text}'")
                    continue

                label = job_page.locator(f"label[for='{radio_id}']")
                if label.count():
                    try:
                        # Simulate reading the question before answering
                        HumanBehavior.simulate_reading(question_text, min_time=0.3, max_time=1.5)
                        
                        # Human-like click on radio option
                        HumanBehavior.human_like_click(job_page, label, move_to_element=True)
                        print(f"[INFO] [OK] Selected '{saved_answer}' for radio Q: '{question_text}'")
                    except Exception as e:
                        print(f"[WARN] [WARN] Human-like click failed for '{saved_answer}', using fallback. ({e})")
                        label.scroll_into_view_if_needed()
                        time.sleep(config.DELAYS["ui_stability"])
                        try:
                            label.click(timeout=config.TIMEOUTS["radio_click"])
                        except:
                            job_page.evaluate("el => el.click()", label)
                        print(f"[INFO] [OK] Fallback click for '{saved_answer}' on '{question_text}'")
                else:
                    print(f"[WARN] [WARN] No label found for radio '{saved_answer}' on '{question_text}'")

            except Exception as e:
                if config.DEBUG:
                    print(f"[DEBUG] Radio handling failed for a question: {e}")
                    print(f"[DEBUG] Fieldset type: {type(fieldset)}")
                    print(f"[DEBUG] Fieldset value: {fieldset}")
                print(f"[ERROR] [ERROR] Radio handling failed for a question: {e}")
    except Exception as e:
        if config.DEBUG:
            print(f"[DEBUG] Error accessing radio fieldsets: {e}")
        print(f"[WARN] [WARN] Could not process radio fieldsets: {e}")

    # --- DROPDOWN QUESTIONS ---
    try:
        dropdowns = job_page.locator(config.LINKEDIN_SELECTORS["form_fields"]["dropdown"])
        if config.DEBUG:
            print(f"[DEBUG] Found {dropdowns.count()} dropdowns")
            if dropdowns.count() > 0:
                debug_pause(f"Processing {dropdowns.count()} dropdown questions...", 0.2)
        ignore_keywords = config.QUESTION_CONFIG["ignore_keywords"]
        SKIP_QUESTIONS = config.QUESTION_CONFIG["skip_questions"]
        for i in range(dropdowns.count()):
            dropdown = dropdowns.nth(i)

            # Extract question text (label preceding the select)
            label_locator = dropdown.locator(config.LINKEDIN_SELECTORS["form_fields"]["dropdown_label"])
            question_text = label_locator.inner_text().strip() if label_locator.count() else "Unknown question"

            # [OK] Skip pre-filled LinkedIn profile fields
            if any(skip in question_text for skip in SKIP_QUESTIONS):
                if config.DEBUG:
                    print(f"[DEBUG] ⏭️ Skipping '{question_text}'  LinkedIn profile field.")
                continue
            
            if any(word in question_text for word in ignore_keywords):
                print(f"[INFO] ⏭️ Skipping '{question_text}'  handled by LinkedIn profile.")
                continue

            selected_value = dropdowns.nth(i).input_value()
            if selected_value and selected_value != "Select an option":
                if config.DEBUG:
                    print(f"[DEBUG] [OK] '{question_text}' already has value '{selected_value}'  skipping.")
                continue

            # Use saved or new answer
            saved_answer = data["questions"].get(question_text)
            if not saved_answer:
                saved_answer = determine_answer(question_text)
                save_answer_to_yaml(question_text, saved_answer)
                print(f"[INFO] [OK] Determined answer for dropdown Q: '{question_text}' -> '{saved_answer}'")
            else:
                if config.DEBUG:
                    print(f"[DEBUG] 🔁 Using saved answer for dropdown Q '{question_text}': {saved_answer}")

            # Select dropdown option with human-like behavior
            try:
                # Simulate reading the question before selecting
                HumanBehavior.simulate_reading(question_text, min_time=0.3, max_time=1.2)
                
                # Human-like interaction with dropdown
                dropdown.scroll_into_view_if_needed()
                HumanBehavior.simulate_hesitation(0.2, 0.6)
                
                # Hover before selecting
                try:
                    dropdown.hover()
                    time.sleep(random.uniform(0.15, 0.35))
                except:
                    pass
                
                dropdown.select_option(saved_answer)
                HumanBehavior.simulate_hesitation(0.1, 0.3)  # Pause after selection
                print(f"[INFO] [TAG] Dropdown Q: '{question_text}' -> '{saved_answer}'")
            except Exception as e:
                # Try to print available options if possible
                try:
                    options = dropdown.locator("option")
                    option_texts = [options.nth(j).inner_text().strip() for j in range(options.count())]
                    print(f"[WARN] [WARN] Could not select '{saved_answer}' for '{question_text}': {e}")
                    print(f"[WARN] [WARN] Available options for '{question_text}': {option_texts}")
                except Exception as opt_e:
                    print(f"[WARN] [WARN] Could not select '{saved_answer}' for '{question_text}': {e}")
                    print(f"[WARN] [WARN] Also failed to retrieve options: {opt_e}")
    except Exception as e:
        if config.DEBUG:
            print(f"[DEBUG] Error processing dropdowns: {e}")
        print(f"[WARN] [WARN] Could not process dropdowns: {e}")

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
    [OK] Cleans up job_urls.json (removes completed or already-applied jobs)
    """
    print("[ACTION] Starting Easy Apply")
    
    # Debug pause before starting Easy Apply
    if config.DEBUG:
        print("[DEBUG] ⏸️  About to start Easy Apply process")
        print(f"[DEBUG] Resume path: {resume_path}")
        print(f"[DEBUG] Job URL: {job_url}")
        print("[DEBUG] Press Enter to continue...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print("[DEBUG] Continuing automatically...")

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
                print(f"[INFO] [DELETE] Removed {url} from job_urls.json.")
        except Exception as e:
            print(f"[WARN] [WARN] Could not remove {url} from job_urls.json: {e}")

    try:
        # [OK] Check if the job was already applied for
        applied_banner = job_page.locator(config.LINKEDIN_SELECTORS["application_status"]["applied_banner"])
        if applied_banner.count():
            text = applied_banner.inner_text().strip()
            if config.LINKEDIN_SELECTORS["application_status"]["applied_text"] in text:
                print("[INFO] [OK] Already applied for this job. Skipping Easy Apply.")
                remove_from_json(job_url)
                return False

        # [OK] Check if job is no longer accepting applications
        no_longer_accepting_selectors = config.LINKEDIN_SELECTORS["application_status"]["no_longer_accepting"]
        
        for selector in no_longer_accepting_selectors:
            if job_page.locator(selector).count():
                print("[INFO] [WARN] Job is no longer accepting applications. Skipping and removing from list.")
                remove_from_json(job_url)
                return False
        
        # Also check the page text content for the phrase
        page_text = job_page.inner_text("body").lower()
        if "no longer accepting applications" in page_text:
            print("[INFO] [WARN] Job is no longer accepting applications. Skipping and removing from list.")
            remove_from_json(job_url)
            return False

        # [OK] Find & click Easy Apply button with fallback selectors
        easy_apply_button = None
        button_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["button"]
        
        # Try each selector until we find one that works
        for selector in button_selectors if isinstance(button_selectors, list) else [button_selectors]:
            try:
                button = job_page.locator(selector)
                if button.count() > 0:
                    easy_apply_button = button
                    print(f"[DEBUG] Found Easy Apply button with selector: {selector}")
                    break
            except Exception as e:
                continue
        
        if not easy_apply_button or not easy_apply_button.count():
            print("[ERROR] [ERROR] No Easy Apply button found with any selector.")
            remove_from_json(job_url)
            return False

        # Human-like interaction with Easy Apply button
        easy_apply_button.scroll_into_view_if_needed()
        HumanBehavior.simulate_hesitation(0.3, 0.8)  # Pause to "read" button
        
        # Random mouse movement before clicking
        try:
            bbox = easy_apply_button.bounding_box()
            if bbox:
                HumanBehavior.random_mouse_movement(job_page, bbox)
        except:
            pass
        
        # Human-like hover and click
        try:
            HumanBehavior.human_like_click(job_page, easy_apply_button, move_to_element=True)
            if config.DEBUG:
                print("[DEBUG] 🖱️ Human-like click on Easy Apply button.")
        except Exception as e:
            print(f"[WARN] [WARN] Human-like click failed, using fallback: {e}")
            easy_apply_button.hover()
            time.sleep(random.uniform(0.2, 0.5))
            easy_apply_button.click(timeout=config.TIMEOUTS["easy_apply_click"])
        
        print("[INFO] [OK] Easy Apply button clicked.")
        
        # Pause after clicking Easy Apply button
        debug_pause("Easy Apply button clicked, waiting for modal...", 1.0)

        # [OK] Wait for modal with fallback selectors
        modal_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["modal"]
        modal_found = False
        
        for selector in modal_selectors if isinstance(modal_selectors, list) else [modal_selectors]:
            try:
                job_page.wait_for_selector(selector, state="visible", timeout=config.TIMEOUTS["modal_wait"])
                print(f"[INFO] [OK] Easy Apply modal detected with selector: {selector}")
                modal_found = True
                break
            except:
                continue
        
        if not modal_found:
            print("[ERROR] [ERROR] Easy Apply modal not detected with any selector.")
            remove_from_json(job_url)
            return False

        # Pause after modal appears
        debug_pause("Easy Apply modal detected, ready to process steps...", 0.5)

        # [OK] Iterate through modal steps
        step_counter = 1
        max_steps = config.RETRY_CONFIG["max_steps"]  # Safeguard against infinite loops
        while step_counter <= max_steps:
            if config.DEBUG:
                print(f"[DEBUG] 👣 Step {step_counter}/{max_steps}: Checking for questions, resume uploads, and buttons")

            try:
                # Handle resume upload (every step)
                check_and_upload_resume(job_page)
                
                # Pause after resume upload check
                if config.DEBUG:
                    debug_pause(f"After resume upload check (step {step_counter})...", 0.3)

                # Handle radio & dropdown questions
                handle_additional_questions(job_page)
                
                # Pause after processing questions
                if config.DEBUG:
                    debug_pause(f"After processing questions (step {step_counter})...", 0.3)

                # [OK] Footer buttons
                footer = job_page.locator("footer")
                
                # Handle submit button (which is a list of selectors)
                submit_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["submit"]
                submit_selectors_list = submit_selectors if isinstance(submit_selectors, list) else [submit_selectors]
                submit_btn = None
                for selector in submit_selectors_list:
                    btn = footer.locator(selector)
                    if btn.count() > 0:
                        submit_btn = btn
                        break
                
                # Handle review button (which is a list of selectors)
                review_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["review"]
                review_selectors_list = review_selectors if isinstance(review_selectors, list) else [review_selectors]
                review_btn = None
                for selector in review_selectors_list:
                    btn = footer.locator(selector)
                    if btn.count() > 0:
                        review_btn = btn
                        break
                
                # Handle next button (which is a list of selectors)
                next_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["next"]
                next_selectors_list = next_selectors if isinstance(next_selectors, list) else [next_selectors]
                next_btn = None
                for selector in next_selectors_list:
                    btn = footer.locator(selector)
                    if btn.count() > 0:
                        next_btn = btn
                        break
                
                # Pause before checking buttons
                if config.DEBUG:
                    debug_pause(f"Checking for buttons (step {step_counter})...", 0.2)
                
            except Exception as step_error:
                if config.DEBUG:
                    print("\n" + "="*80)
                    print(f"[DEBUG] 🛑 STOPPING FOR DEBUG INSPECTION - Step processing error")
                    print("="*80)
                    print(f"[DEBUG] Error: {step_error}")
                    print(f"[DEBUG] Step: {step_counter}/{max_steps}")
                    print(f"[DEBUG] Job URL: {job_url}")
                    print(f"[DEBUG] Current page URL: {job_page.url}")
                    print("[DEBUG] Browser will remain open for inspection.")
                    print("[DEBUG] Press Enter in terminal to continue...")
                    print("="*80 + "\n")
                    try:
                        input()  # Wait for user input in debug mode
                    except (EOFError, KeyboardInterrupt):
                        print("[DEBUG] Continuing automatically...")
                raise  # Re-raise to be caught by outer exception handler

            if submit_btn and submit_btn.count() > 0:
                # [OK] Make sure "Follow company" is unchecked
                follow_checkbox_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["follow_checkbox"]
                follow_checkbox_selectors_list = follow_checkbox_selectors if isinstance(follow_checkbox_selectors, list) else [follow_checkbox_selectors]
                
                follow_checkbox = None
                for selector in follow_checkbox_selectors_list:
                    cb = job_page.locator(selector)
                    if cb.count() > 0:
                        follow_checkbox = cb
                        break
                
                if follow_checkbox and follow_checkbox.count() > 0:
                    try:
                        if follow_checkbox.is_checked():
                            try:
                                print("[DEBUG] [RETRY] Clicking label to uncheck")
                                follow_label_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["follow_label"]
                                follow_label_selectors_list = follow_label_selectors if isinstance(follow_label_selectors, list) else [follow_label_selectors]
                                
                                label_clicked = False
                                for label_selector in follow_label_selectors_list:
                                    try:
                                        label = job_page.locator(label_selector)
                                        if label.count() > 0:
                                            label.click()
                                            label_clicked = True
                                            break
                                    except:
                                        continue
                                
                                if not label_clicked:
                                    print("[WARN] [WARN] Label click failed, forcing via JS.")
                                    job_page.evaluate("el => el.checked = false", follow_checkbox.first)
                            except Exception as e:
                                print(f"[WARN] [WARN] Could not uncheck follow box: {e}")
                                job_page.evaluate("el => el.checked = false", follow_checkbox.first)
                        else:
                            print("[DEBUG] [OK] Follow box already unchecked.")
                    except Exception as e:
                        print(f"[WARN] [WARN] Could not verify/uncheck follow box: {e}")

                if config.DEBUG:
                    print("[DEBUG] About to click SUBMIT")
                    debug_pause("About to click SUBMIT button...", 0.5)
                submit_btn.first.click()
                print("[INFO] [OK] Submitted application.")
                debug_pause("Submit button clicked, waiting for confirmation...", 1.0)
                break

            elif review_btn and review_btn.count() > 0:
                if config.DEBUG:
                    print("[DEBUG] About to click REVIEW")
                    debug_pause("About to click REVIEW button...", 0.5)
                review_btn.first.click()
                print("[INFO] [RETRY] Clicked Review button.")
                debug_pause("Review button clicked, continuing...", 0.8)
            elif next_btn and next_btn.count() > 0:
                if config.DEBUG:
                    print("[DEBUG] About to click NEXT")
                    debug_pause("About to click NEXT button...", 0.5)
                next_btn.first.click()
                print(f"[INFO] ➡️ Clicked Next button (step {step_counter}/{max_steps}).")
                debug_pause("Next button clicked, moving to next step...", 0.8)

            else:
                print(f"[DEBUG] [WARN] No Next/Review/Submit button at step {step_counter}. Stopping.")
                debug_pause("No buttons found, stopping...", 0.5)
                break
    
            # Check if we hit the max steps limit
            if step_counter > max_steps:
                print(f"[ERROR] [ERROR] Reached maximum steps ({max_steps}) without completion. Possible infinite loop detected.")
                remove_from_json(job_url)
                return False
                break

            time.sleep(config.DELAYS["step_processing"])
            step_counter += 1
        
        # Pause after completing all steps
        debug_pause("All steps completed, checking for submission confirmation...", 0.5)

        # [OK] Confirm submission (LinkedIn sometimes refreshes the job page after submission)
        success = False
        try:
            job_page.wait_for_timeout(config.TIMEOUTS["dom_refresh"])  # small wait for DOM to refresh

            # Check for confirmation using centralized selectors
            confirmation_selectors = config.LINKEDIN_SELECTORS["application_status"]["confirmation"]
            for i, selector in enumerate(confirmation_selectors):
                if job_page.locator(selector).count() > 0:
                    print(f"[SUCCESS] [OK] Application submitted (confirmation method {i+1} found).")
                    success = True
                    break

            else:
                print("[WARNING] [WARN] No explicit confirmation detected  submission status uncertain.")
                success = False  # <-- mark as failed instead of assuming success

        except Exception as e:
            print(f"[WARN] [WARN] Could not confirm submission visually: {e}")
            success = False
        
                # [OK] Remove from JSON only if verified success
        if success:
            remove_from_json(job_url)



        # [OK] Close modal
        # Try dismissing any modals without crashing
        debug_pause("Attempting to close modal...", 0.5)
        try:
            dismiss_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["dismiss"]
            dismiss_selectors_list = dismiss_selectors if isinstance(dismiss_selectors, list) else [dismiss_selectors]
            
            dismiss_clicked = False
            for selector in dismiss_selectors_list:
                try:
                    dismiss_buttons = job_page.locator(selector)
                    if dismiss_buttons.count() > 0:
                        dismiss_buttons.first.click()
                        print(f"[DEBUG] [OK] Clicked first dismiss button with selector: {selector}")
                        dismiss_clicked = True
                        break
                except Exception as e:
                    if config.DEBUG:
                        print(f"[DEBUG] Failed to click dismiss with selector {selector}: {e}")
                    continue
            
            if not dismiss_clicked:
                print("[DEBUG] ❎ No dismiss button found with any selector.")
        except Exception as e:
            print(f"[WARN] [WARN] Could not dismiss modal: {e}")
        return success

    except Exception as e:
        print(f"[ERROR] [ERROR] Easy Apply failed: {e}")
        
        # Debug mode: Add stop for inspection
        if config.DEBUG:
            print("\n" + "="*80)
            print("[DEBUG] 🛑 STOPPING FOR DEBUG INSPECTION")
            print("="*80)
            print(f"[DEBUG] Error: {e}")
            print(f"[DEBUG] Job URL: {job_url}")
            print(f"[DEBUG] Current page URL: {job_page.url}")
            print("[DEBUG] Browser will remain open for inspection.")
            print("[DEBUG] Press Enter in terminal to continue...")
            print("="*80 + "\n")
            try:
                input()  # Wait for user input in debug mode
            except (EOFError, KeyboardInterrupt):
                print("[DEBUG] Continuing automatically...")
        
        remove_from_json(job_url)   # [OK] REMOVE even on failure so bad jobs dont clog
        
        # Try to dismiss modal with proper selector handling
        try:
            dismiss_selectors = config.LINKEDIN_SELECTORS["easy_apply"]["dismiss"]
            dismiss_selectors_list = dismiss_selectors if isinstance(dismiss_selectors, list) else [dismiss_selectors]
            
            for selector in dismiss_selectors_list:
                try:
                    dismiss_buttons = job_page.locator(selector)
                    if dismiss_buttons.count() > 0:
                        dismiss_buttons.first.click()
                        print(f"[DEBUG] [OK] Dismissed modal with selector: {selector}")
                        break
                except:
                    continue
        except:
            pass
        return False
