# Dynamic Resume Generator with LinkedIn Easy Apply Automation

## 📌 Overview
This project is a **single-user automation tool** that:
- Scrapes job listings from sites like LinkedIn or Indeed.
- Extracts **keywords** and job requirements from the listing.
- Uses an **LLM** (OpenAI, Anthropic, etc.) to tailor your resume content.
- Generates an **ATS-friendly Word/PDF resume** for each job.
- (Optional) Automates the **LinkedIn Easy Apply** process via Playwright.


![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)

> ⚠️ **Requires Python 3.9+**  
> Tested and confirmed working with **Python 3.9.7**.  
> Python 3.13 is **not yet supported** due to spaCy dependency issues.


## 📦 Prerequisites

- **Python 3.9 or 3.10 or 3.11**  
  (Confirmed stable with 3.9.7; newer versions may break spaCy)
- [pip](https://pip.pypa.io/en/stable/) for package management
- [Playwright](https://playwright.dev/python/) browsers installed (via `playwright install`)


---

## ⚙️ Architecture

1️⃣ **Job Listing Scraper**  
- Uses [Playwright](https://playwright.dev/python/) to scrape job descriptions from LinkedIn, Indeed, etc.

2️⃣ **Keyword Extraction**  
- Uses `spaCy` or an LLM to identify **skills**, **technologies**, and **keywords** in the job description.

3️⃣ **Resume Generation**  
- Tailors a **master resume** with job-specific bullet points and formats it into Word/PDF (`python-docx`).

4️⃣ **Easy Apply Automation** *(Optional)*  
- Playwright logs into LinkedIn, navigates to the job, clicks **Easy Apply**, and fills out required fields automatically.

---

## 🛠 Tech Stack

- **Python 3.11+**
- [Playwright](https://playwright.dev/python/) → Job scraping + LinkedIn automation
- [OpenAI API](https://platform.openai.com/) or [Anthropic API](https://www.anthropic.com/) → Resume rephrasing & keyword matching
- [spaCy](https://spacy.io/) → Keyword/skills extraction
- [python-docx](https://python-docx.readthedocs.io/en/latest/) → Word document generation
- [WeasyPrint](https://weasyprint.org/) *(optional)* → PDF generation
- [dotenv](https://pypi.org/project/python-dotenv/) → Secure storage of credentials

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

4️⃣  **Create .env file**

OPENAI_API_KEY=your_openai_key_here
LINKEDIN_EMAIL=your_email_here
LINKEDIN_PASSWORD=your_password_here


▶️ Usage

1️⃣ Run the script with a job link

python main.py --job "https://www.linkedin.com/jobs/view/123456"


