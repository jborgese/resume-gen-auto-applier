from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re
import time

def sanitize_filename(text: str) -> str:
    """Sanitize text for safe filename usage."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', text.replace(" ", "_"))

def build_resume(data: dict) -> str:
    """
    Generate a unique PDF resume from a Jinja2 HTML template.
    :param data: dict containing resume details
    :return: path to generated PDF
    """

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
    output_path = Path(f"output/resumes/{safe_title}_{safe_company}_{timestamp}.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ✅ Generate PDF
    HTML(string=html_content).write_pdf(str(output_path))

    print(f"[INFO] 📄 Resume generated: {output_path}")
    return str(output_path)
