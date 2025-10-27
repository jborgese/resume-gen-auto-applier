from pathlib import Path
import re
import time
import logging

# Suppress GLib-GIO warnings before importing WeasyPrint
from src.glib_suppression import suppress_glib_warnings
suppress_glib_warnings()

from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from src.error_handler import retry_with_backoff, ErrorContext, APIFailureHandler, RetryableError, FatalError

logger = logging.getLogger(__name__)

def sanitize_filename(text: str) -> str:
    """Sanitize text for safe filename usage."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', text.replace(" ", "_"))

@retry_with_backoff(max_attempts=2, base_delay=1.0)
def build_resume(data: dict) -> str:
    """
    Generate a unique PDF resume from a Jinja2 HTML template.
    :param data: dict containing resume details
    :return: path to generated PDF
    """
    with ErrorContext("Resume generation", None) as context:
        context.add_context("job_title", data.get("title", "N/A"))
        context.add_context("company", data.get("company", "N/A"))
        context.add_context("name", data.get("name", "Unknown"))
        
        try:
            # ✅ Set up Jinja2 environment
            env = Environment(loader=FileSystemLoader("templates"))
            template = env.get_template("base_resume.html")

            # ✅ Render the template with provided data (now includes optional fields)
            html_content = template.render(
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                linkedin=data["linkedin"],
                github=data.get("github"),       # <-- ✅ Optional GitHub link
                address=data.get("address"),     # <-- ✅ Optional address block
                summary=data["summary"],
                skills=data["skills"],
                experiences=data["experiences"],
                education=data["education"],
                references=data["references"],
                matched_keywords=data.get("matched_keywords", []),  # <-- ✅ Leave as list for template join
                title=data.get("title", "N/A"),
                company=data.get("company", "N/A"),
            )

            # ✅ Sanitize job title & company for filename
            safe_title = sanitize_filename(data.get("title", "Job"))
            safe_company = sanitize_filename(data.get("company", "Company"))

            # ✅ Include timestamp for uniqueness
            timestamp = time.strftime("%Y%m%d-%H%M%S")

            # ✅ Build unique output path
            last_name = sanitize_filename(data.get("name", "").split()[-1] if data.get("name") else "Unknown")
            output_path = Path(f"output/resumes/{last_name}_{safe_title}_{safe_company}.pdf")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # ✅ Generate PDF with error handling and UTF-8 encoding
            try:
                # Ensure HTML content is properly encoded as UTF-8
                if isinstance(html_content, str):
                    html_content = html_content.encode('utf-8').decode('utf-8')
                
                HTML(string=html_content).write_pdf(str(output_path))
                context.add_context("success", True)
                context.add_context("output_path", str(output_path))
            except Exception as e:
                logger.error(f"❌ WeasyPrint PDF generation failed: {e}")
                context.add_context("error", f"WeasyPrint failed: {e}")
                
                # Try fallback PDF generation
                fallback_success = APIFailureHandler.handle_weasyprint_failure(html_content, str(output_path))
                if not fallback_success:
                    raise FatalError(f"PDF generation failed: {e}")
                else:
                    logger.info("✅ Fallback PDF generation succeeded")

            print(f"[INFO] 📄 Resume generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            context.add_context("error", str(e))
            context.add_context("error_type", type(e).__name__)
            
            if "template" in str(e).lower():
                raise FatalError(f"Template error: {e}")
            elif "permission" in str(e).lower():
                raise FatalError(f"Permission error: {e}")
            else:
                raise RetryableError(f"Resume generation failed: {e}")
