from weasyprint import HTML
from pathlib import Path

def build_resume(keywords: list) -> str:
    """Generate a tailored PDF resume based on keywords."""
    # Simple starter HTML — later we’ll load a styled HTML template instead
    html_content = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.5;
          }}
          h1 {{
            color: #333;
          }}
          .keywords {{
            margin-top: 20px;
            font-size: 14px;
            color: #555;
          }}
        </style>
      </head>
      <body>
        <h1>Tailored Resume</h1>
        <p>This resume was dynamically generated for this job listing.</p>
        <div class="keywords">
          <strong>Matched Keywords:</strong> {", ".join(keywords)}
        </div>
      </body>
    </html>
    """

    # Output path
    output_path = Path("output/resumes/tailored_resume.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate the PDF
    HTML(string=html_content).write_pdf(str(output_path))

    return str(output_path)
# src/resume_builder.py
# This function builds a resume PDF based on extracted keywords.