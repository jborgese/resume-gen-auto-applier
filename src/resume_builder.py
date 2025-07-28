from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def build_resume(data: dict) -> str:
    """
    Generate a PDF resume from a Jinja2 HTML template.
    :param data: dict containing resume details
    :return: path to generated PDF
    """

    # Set up Jinja2 to load from templates directory
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("base_resume.html")

    # Render the template with provided data
    html_content = template.render(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        linkedin=data["linkedin"],
        summary=data["summary"],
        skills=data["skills"],
        experiences=data["experiences"],
        matched_keywords=", ".join(data["matched_keywords"])
    )

    # Output folder for resumes
    output_path = Path("output/resumes/tailored_resume.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate PDF
    HTML(string=html_content).write_pdf(str(output_path))

    print(f"[INFO] Resume generated: {output_path}")
    return str(output_path)