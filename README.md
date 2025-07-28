# Dynamic Resume Generator with LinkedIn Easy Apply Automation

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)

## 📌 Overview
This project is a **single-user automation tool** that:
- Scrapes job listings from sites like LinkedIn or Indeed.
- Extracts **keywords** and job requirements from the listing.
- Uses an **LLM** (OpenAI, Anthropic, etc.) to tailor your resume content.
- Generates an **ATS-friendly PDF resume** for each job (using WeasyPrint).
- (Optional) Automates the **LinkedIn Easy Apply** process via Playwright.

> ⚠️ **Requires Python 3.9+**  
> Tested and confirmed working with **Python 3.9.7**.  
> Python 3.13 is **not yet supported** due to spaCy dependency issues.

---

## 📦 Prerequisites

- **Python 3.9, 3.10, or 3.11**  
  (Confirmed stable with 3.9.7; newer versions may break spaCy)
- [pip](https://pip.pypa.io/en/stable/) for package management
- [Playwright](https://playwright.dev/python/) installed (and browsers via `playwright install`)
- **Windows users only:** [GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) for PDF generation with WeasyPrint

---

## ⚙️ Architecture

1️⃣ **Job Listing Scraper**  
- Uses [Playwright](https://playwright.dev/python/) to scrape job descriptions from LinkedIn, Indeed, etc.

2️⃣ **Keyword Extraction**  
- Uses `spaCy` or an LLM to identify **skills**, **technologies**, and **keywords** in the job description.

3️⃣ **Resume Generation**  
- Generates a **PDF resume** using **WeasyPrint** and a Jinja2 HTML template.

4️⃣ **Easy Apply Automation** *(Optional)*  
- Playwright logs into LinkedIn, navigates to the job, clicks **Easy Apply**, and fills out required fields automatically.

---

## 🛠 Tech Stack

- **Python 3.9+**
- [Playwright](https://playwright.dev/python/) → Job scraping & LinkedIn automation
- [OpenAI API](https://platform.openai.com/) or [Anthropic API](https://www.anthropic.com/) → Resume tailoring
- [spaCy](https://spacy.io/) → Keyword extraction
- [WeasyPrint](https://weasyprint.org/) → PDF generation
- [Jinja2](https://jinja.palletsprojects.com/) → HTML template rendering
- [dotenv](https://pypi.org/project/python-dotenv/) → Secure storage of credentials & settings

---

## 📂 Project Structure

resume-generator/
│── src/
│ ├── scraper.py # Playwright job scraper
│ ├── keyword_extractor.py # Keyword & skills parser
│ ├── resume_builder.py # Resume generation logic
│ ├── easy_apply.py # LinkedIn Easy Apply automation
│ ├── prompts/ # LLM prompt templates
│── templates/
│ ├── master_resume.docx # Base resume template
│── output/
│ ├── resumes/ # Generated resumes
│── .env # API keys, LinkedIn credentials
│── requirements.txt
│── README.md
└── main.py

---

## 🚀 Installation & Setup

1️⃣ **Clone the repo**

git clone https://github.com/YOUR_USERNAME/resume-generator.git
cd resume-generator

2️⃣ **Create activate a virtual environment**

python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3️⃣ **Install dependencies**

pip install -r requirements.txt
playwright install

4️⃣ **(Windows only) Install GTK for WeasyPrint**

Download and install GTK3 from:
👉 https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
Add GTK’s /bin folder to your PATH and restart PowerShell.

5️⃣ **Create .env file**

Copy .env.example → .env and fill in your details:
`cp .env.example .env`
Edit .env:
`NAME=Your Name`
`EMAIL=your.email@example.com`
`PHONE=(555) 555-5555`
`LINKEDIN=https://linkedin.com/in/yourprofile`
`AUTO_APPLY=false`
`DEFAULT_TEMPLATE=base_resume.html`



▶️ Usage

1️⃣ Run the script with a job link

python main.py

✅ A tailored PDF resume will be generated in:

output/resumes/tailored_resume.pdf

If AUTO_APPLY=true in .env, LinkedIn Easy Apply automation will run (future feature).
