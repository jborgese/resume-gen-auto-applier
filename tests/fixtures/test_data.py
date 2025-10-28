"""
Test fixtures and mock data for resume-generator-auto-applier.

This module provides comprehensive test data, fixtures, and utilities
for testing the resume generator and auto-applicator system.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil


# Sample personal information for testing
SAMPLE_PERSONAL_INFO = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "linkedin": "https://linkedin.com/in/johndoe",
    "github": "https://github.com/johndoe",
    "address": "123 Main St, Anytown, ST 12345",
    "job_history": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "start_date": "2020-01",
            "end_date": "Present",
            "responsibilities": [
                "Developed scalable web applications using Python and React",
                "Led team of 5 engineers in agile development process",
                "Implemented CI/CD pipelines using Jenkins and Docker",
                "Designed microservices architecture on AWS cloud platform",
                "Mentored junior developers and conducted code reviews"
            ]
        },
        {
            "title": "Software Engineer",
            "company": "StartupXYZ",
            "start_date": "2018-06",
            "end_date": "2019-12",
            "responsibilities": [
                "Built REST APIs using Django and PostgreSQL",
                "Optimized database queries improving performance by 40%",
                "Collaborated with product team to define requirements",
                "Implemented automated testing with pytest and Selenium"
            ]
        },
        {
            "title": "Junior Developer",
            "company": "WebDev Solutions",
            "start_date": "2017-01",
            "end_date": "2018-05",
            "responsibilities": [
                "Developed frontend components using JavaScript and jQuery",
                "Maintained legacy PHP applications",
                "Participated in daily standups and sprint planning"
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "institution": "University of Technology",
            "graduation_date": "2016",
            "gpa": "3.8"
        },
        {
            "degree": "Master of Science",
            "field": "Software Engineering",
            "institution": "Tech Institute",
            "graduation_date": "2018",
            "gpa": "3.9"
        }
    ],
    "references": [
        {
            "name": "Jane Smith",
            "title": "Engineering Manager",
            "company": "Tech Corp",
            "contact": {
                "email": "jane.smith@techcorp.com",
                "phone": "+1-555-987-6543"
            }
        },
        {
            "name": "Mike Johnson",
            "title": "Senior Developer",
            "company": "StartupXYZ",
            "contact": {
                "email": "mike.johnson@startupxyz.com",
                "phone": "+1-555-456-7890"
            }
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "date": "2021-03",
            "expiry": "2024-03"
        },
        {
            "name": "Certified Kubernetes Administrator",
            "issuer": "Cloud Native Computing Foundation",
            "date": "2022-06",
            "expiry": "2025-06"
        }
    ],
    "projects": [
        {
            "name": "E-commerce Platform",
            "description": "Full-stack e-commerce solution with React frontend and Django backend",
            "technologies": ["Python", "Django", "React", "PostgreSQL", "AWS"],
            "url": "https://github.com/johndoe/ecommerce-platform"
        },
        {
            "name": "Machine Learning Pipeline",
            "description": "Automated ML pipeline for data processing and model training",
            "technologies": ["Python", "TensorFlow", "Docker", "Kubernetes", "Apache Airflow"],
            "url": "https://github.com/johndoe/ml-pipeline"
        }
    ]
}


# Sample job descriptions for testing
SAMPLE_JOB_DESCRIPTIONS = {
    "senior_software_engineer": """
    Senior Software Engineer - Full Stack Development
    
    Company: TechCorp Inc.
    Location: San Francisco, CA (Remote OK)
    Salary: $120,000 - $180,000
    
    We are seeking a Senior Software Engineer to join our dynamic team. 
    The ideal candidate will have extensive experience in modern web development 
    and cloud technologies.
    
    Required Skills:
    - 5+ years of Python development experience
    - Strong proficiency in React and JavaScript (ES6+)
    - Experience with AWS cloud services (EC2, S3, Lambda, RDS)
    - Docker containerization and Kubernetes orchestration
    - SQL database design and optimization (PostgreSQL, MySQL)
    - RESTful API development and GraphQL
    - Git version control and CI/CD pipelines
    - Agile development methodologies
    
    Preferred Qualifications:
    - Experience with Django or Flask frameworks
    - Knowledge of microservices architecture
    - Machine learning integration experience
    - Previous startup experience
    - Open source contributions
    
    Responsibilities:
    - Design and develop scalable web applications
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Participate in code reviews
    - Contribute to architectural decisions
    - Optimize application performance
    """,
    
    "frontend_developer": """
    Frontend Developer - React Specialist
    
    Company: WebSolutions LLC
    Location: New York, NY
    Salary: $90,000 - $130,000
    
    We're looking for a talented Frontend Developer to join our growing team.
    
    Requirements:
    - 3+ years of React development experience
    - Strong JavaScript and TypeScript skills
    - Experience with Redux or Context API
    - CSS3, HTML5, and responsive design
    - Webpack, Babel, and modern build tools
    - Jest and React Testing Library
    - Git and GitHub workflows
    
    Nice to have:
    - Next.js or Gatsby experience
    - GraphQL knowledge
    - Design system experience
    - Mobile development (React Native)
    """,
    
    "devops_engineer": """
    DevOps Engineer - Cloud Infrastructure
    
    Company: CloudTech Systems
    Location: Austin, TX (Hybrid)
    Salary: $110,000 - $160,000
    
    Join our DevOps team to build and maintain our cloud infrastructure.
    
    Required:
    - 4+ years of DevOps/Infrastructure experience
    - AWS, Azure, or GCP certification
    - Docker and Kubernetes expertise
    - Terraform or CloudFormation
    - Jenkins, GitLab CI, or GitHub Actions
    - Linux system administration
    - Monitoring tools (Prometheus, Grafana)
    
    Preferred:
    - Ansible or Chef experience
    - Security best practices
    - Database administration
    - Python or Go scripting
    """
}


# Sample job data for testing
SAMPLE_JOB_DATA = {
    "senior_software_engineer": {
        "title": "Senior Software Engineer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "url": "https://linkedin.com/jobs/view/123456789",
        "description": SAMPLE_JOB_DESCRIPTIONS["senior_software_engineer"],
        "keywords": ["Python", "React", "AWS", "Docker", "Kubernetes", "SQL", "Django", "Flask"],
        "matched_keywords": ["Python", "React", "AWS", "Docker", "Kubernetes"],
        "salary": "$120,000 - $180,000",
        "employment_type": "Full-time",
        "experience_level": "Senior",
        "remote_ok": True
    },
    "frontend_developer": {
        "title": "Frontend Developer",
        "company": "WebSolutions LLC",
        "location": "New York, NY",
        "url": "https://linkedin.com/jobs/view/987654321",
        "description": SAMPLE_JOB_DESCRIPTIONS["frontend_developer"],
        "keywords": ["React", "JavaScript", "TypeScript", "Redux", "CSS3", "HTML5"],
        "matched_keywords": ["React", "JavaScript", "TypeScript"],
        "salary": "$90,000 - $130,000",
        "employment_type": "Full-time",
        "experience_level": "Mid-level",
        "remote_ok": False
    },
    "devops_engineer": {
        "title": "DevOps Engineer",
        "company": "CloudTech Systems",
        "location": "Austin, TX",
        "url": "https://linkedin.com/jobs/view/456789123",
        "description": SAMPLE_JOB_DESCRIPTIONS["devops_engineer"],
        "keywords": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins", "Linux"],
        "matched_keywords": ["AWS", "Docker", "Kubernetes", "Terraform"],
        "salary": "$110,000 - $160,000",
        "employment_type": "Full-time",
        "experience_level": "Mid-level",
        "remote_ok": True
    }
}


# Sample tech dictionary for testing
SAMPLE_TECH_DICTIONARY = {
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl"
    ],
    "frameworks": [
        "React", "Angular", "Vue.js", "Django", "Flask", "Express", "Spring",
        "Laravel", "Ruby on Rails", "ASP.NET", "FastAPI", "Next.js", "Nuxt.js",
        "Svelte", "Ember.js", "Backbone.js"
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "DynamoDB", "SQLite", "Oracle", "SQL Server", "MariaDB", "Neo4j",
        "InfluxDB", "CouchDB", "RethinkDB"
    ],
    "cloud_platforms": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "OpenShift", "Terraform",
        "CloudFormation", "Heroku", "DigitalOcean", "Linode", "Vultr"
    ],
    "tools": [
        "Git", "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
        "Ansible", "Chef", "Puppet", "SaltStack", "Prometheus", "Grafana",
        "ELK Stack", "Splunk", "Datadog", "New Relic"
    ],
    "methodologies": [
        "Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "TDD", "BDD", "Microservices",
        "REST", "GraphQL", "SOA", "Event-driven architecture", "Domain-driven design"
    ],
    "testing": [
        "Jest", "Mocha", "Chai", "Cypress", "Selenium", "Pytest", "JUnit",
        "TestNG", "RSpec", "PHPUnit", "Karma", "Jasmine", "Enzyme", "React Testing Library"
    ],
    "mobile": [
        "React Native", "Flutter", "Ionic", "Xamarin", "Cordova", "PhoneGap",
        "Swift", "Kotlin", "Objective-C", "Java", "Dart"
    ],
    "ai_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Keras",
        "OpenCV", "NLTK", "spaCy", "Hugging Face", "MLflow", "Kubeflow"
    ]
}


# Sample stopwords for testing
SAMPLE_STOPWORDS = {
    "stopwords": [
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during",
        "before", "after", "above", "below", "between", "among", "against",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "must", "can", "this", "that", "these", "those", "i", "you", "he", "she",
        "it", "we", "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "her", "its", "our", "their", "mine", "yours", "hers", "ours",
        "theirs", "am", "is", "are", "was", "were", "be", "been", "being"
    ]
}


# Sample keyword weights for testing
SAMPLE_KEYWORD_WEIGHTS = {
    "Python": 1.0,
    "JavaScript": 0.95,
    "React": 0.9,
    "AWS": 0.85,
    "Docker": 0.8,
    "Kubernetes": 0.75,
    "SQL": 0.7,
    "Django": 0.65,
    "Flask": 0.6,
    "PostgreSQL": 0.55,
    "MySQL": 0.5,
    "MongoDB": 0.45,
    "Redis": 0.4,
    "Git": 0.35,
    "Jenkins": 0.3,
    "Terraform": 0.25,
    "Ansible": 0.2,
    "Prometheus": 0.15,
    "Grafana": 0.1,
    "ELK": 0.05
}


# Sample resume payload for testing
SAMPLE_RESUME_PAYLOAD = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "linkedin": "https://linkedin.com/in/johndoe",
    "github": "https://github.com/johndoe",
    "address": "123 Main St, Anytown, ST 12345",
    "summary": "Experienced software engineer with 5+ years of expertise in Python development, React frontend development, and AWS cloud technologies. Proven track record of building scalable applications and leading technical initiatives.",
    "skills": ["Python", "React", "AWS", "Docker", "Kubernetes", "SQL", "Django", "Flask", "PostgreSQL", "Git"],
    "matched_keywords": ["Python", "React", "AWS", "Docker", "Kubernetes"],
    "experiences": [
        {
            "role": "Senior Software Engineer",
            "company": "Tech Corp",
            "years": "2020-01 - Present",
            "responsibilities": [
                "Developed scalable web applications using Python and React",
                "Led team of 5 engineers in agile development process",
                "Implemented CI/CD pipelines using Jenkins and Docker"
            ]
        },
        {
            "role": "Software Engineer",
            "company": "StartupXYZ",
            "years": "2018-06 - 2019-12",
            "responsibilities": [
                "Built REST APIs using Django and PostgreSQL",
                "Optimized database queries improving performance by 40%",
                "Collaborated with product team to define requirements"
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "institution": "University of Technology",
            "graduation_date": "2016"
        }
    ],
    "references": [
        {
            "name": "Jane Smith",
            "title": "Engineering Manager",
            "company": "Tech Corp",
            "contact": {
                "email": "jane.smith@techcorp.com",
                "phone": "+1-555-987-6543"
            }
        }
    ],
    "title": "Senior Software Engineer",
    "company": "TechCorp Inc.",
    "location": "San Francisco, CA",
    "description": SAMPLE_JOB_DESCRIPTIONS["senior_software_engineer"]
}


# Sample LinkedIn selectors for testing
SAMPLE_LINKEDIN_SELECTORS = {
    "login": {
        "username": 'input[id="username"]',
        "password": 'input[id="password"]',
        "submit": 'button[type="submit"]'
    },
    "job_search": {
        "job_list": "div.scaffold-layout__list.jobs-semantic-search-list",
        "total_jobs": "div.t-black--light.pv4.text-body-small.mr2",
        "job_cards": "ul.semantic-search-results-list > li",
        "job_wrapper": "div.job-card-job-posting-card-wrapper"
    },
    "job_detail": {
        "title": ['h1.t-24.t-bold.inline', 'h1.jobs-unified-top-card__job-title'],
        "company": ['div.job-details-jobs-unified-top-card__company-name a'],
        "location": 'span.tvm__text.tvm__text--low-emphasis',
        "description": ['div.jobs-description__content', 'div.jobs-description-content__text']
    },
    "easy_apply": {
        "button": ['div.jobs-apply-button--top-card button.jobs-apply-button'],
        "modal": ['div.jobs-easy-apply-modal[role="dialog"]'],
        "submit": ['button[aria-label="Submit application"]'],
        "next": ['button[aria-label="Continue to next step"]'],
        "review": ['button[aria-label="Review your application"]']
    }
}


# Sample OpenAI responses for testing
SAMPLE_OPENAI_RESPONSES = {
    "valid_json": '{"summary": "Experienced software engineer with 5+ years of expertise in Python development, React frontend development, and AWS cloud technologies. Proven track record of building scalable applications and leading technical initiatives.", "keywords": "Python, React, AWS, Docker, Kubernetes, SQL"}',
    "with_code_fences": '```json\n{"summary": "Test summary", "keywords": "Python, React"}\n```',
    "truncated": '{"summary": "Experienced software engineer with strong technical skills',
    "malformed": '{"summary": "Test summary", "keywords": "Python, React"',  # Missing closing brace
    "empty": "",
    "non_json": "This is not JSON at all"
}


# Sample error scenarios for testing
SAMPLE_ERROR_SCENARIOS = {
    "network_timeout": "TimeoutError: Navigation timeout exceeded",
    "rate_limit": "HTTPError: 429 Too Many Requests",
    "invalid_credentials": "LoginError: Invalid username or password",
    "captcha_required": "SecurityError: CAPTCHA verification required",
    "job_unavailable": "JobError: Job posting is no longer available",
    "easy_apply_failed": "ApplyError: Easy Apply process failed",
    "pdf_generation_failed": "PDFError: Failed to generate PDF",
    "template_error": "TemplateError: Template rendering failed"
}


# Sample configuration for testing
SAMPLE_CONFIG = {
    "timeouts": {
        "page_load": 30000,
        "login": 30000,
        "search_page": 45000,
        "job_page": 30000,
        "easy_apply_click": 5000
    },
    "retry_config": {
        "max_attempts": 3,
        "retry_delay": 1.0,
        "max_scroll_passes": 15,
        "max_steps": 10
    },
    "delays": {
        "login_processing": 3.0,
        "ui_stability": 0.2,
        "easy_apply_hover": 0.5,
        "modal_wait": 1.2,
        "step_processing": 1.0
    },
    "scroll_config": {
        "base_speed": 350,
        "min_speed": 150,
        "max_speed": 500,
        "pause_between": 1.0,
        "jitter_range": 20
    }
}


def create_temp_personal_info_file(temp_dir: Path) -> Path:
    """Create a temporary personal info YAML file for testing."""
    personal_info_file = temp_dir / "personal_info.yaml"
    with open(personal_info_file, 'w', encoding='utf-8') as f:
        yaml.dump(SAMPLE_PERSONAL_INFO, f, default_flow_style=False)
    return personal_info_file


def create_temp_tech_dictionary_file(temp_dir: Path) -> Path:
    """Create a temporary tech dictionary JSON file for testing."""
    tech_dict_file = temp_dir / "tech_dictionary.json"
    with open(tech_dict_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_TECH_DICTIONARY, f, indent=2)
    return tech_dict_file


def create_temp_stopwords_file(temp_dir: Path) -> Path:
    """Create a temporary stopwords JSON file for testing."""
    stopwords_file = temp_dir / "stopwords.json"
    with open(stopwords_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_STOPWORDS, f, indent=2)
    return stopwords_file


def create_temp_keyword_weights_file(temp_dir: Path) -> Path:
    """Create a temporary keyword weights JSON file for testing."""
    weights_file = temp_dir / "keyword_weights.json"
    with open(weights_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_KEYWORD_WEIGHTS, f, indent=2)
    return weights_file


def create_temp_job_urls_file(temp_dir: Path, job_urls: List[str] = None) -> Path:
    """Create a temporary job URLs JSON file for testing."""
    if job_urls is None:
        job_urls = [
            "https://linkedin.com/jobs/view/123456789",
            "https://linkedin.com/jobs/view/987654321",
            "https://linkedin.com/jobs/view/456789123"
        ]
    
    job_urls_file = temp_dir / "job_urls.json"
    with open(job_urls_file, 'w', encoding='utf-8') as f:
        json.dump(job_urls, f, indent=2)
    return job_urls_file


def create_temp_resume_template(temp_dir: Path) -> Path:
    """Create a temporary resume HTML template for testing."""
    template_dir = temp_dir / "templates"
    template_dir.mkdir(exist_ok=True)
    
    template_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ name }} - Resume</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; border-bottom: 2px solid #0077b5; }
            h2 { color: #666; margin-top: 30px; }
            .contact { margin-bottom: 20px; }
            .skills { margin-bottom: 20px; }
            .experience { margin-bottom: 20px; }
            .education { margin-bottom: 20px; }
            .references { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>{{ name }}</h1>
        
        <div class="contact">
            <p><strong>Email:</strong> {{ email }}</p>
            <p><strong>Phone:</strong> {{ phone }}</p>
            {% if linkedin %}<p><strong>LinkedIn:</strong> {{ linkedin }}</p>{% endif %}
            {% if github %}<p><strong>GitHub:</strong> {{ github }}</p>{% endif %}
            {% if address %}<p><strong>Address:</strong> {{ address }}</p>{% endif %}
        </div>
        
        <h2>Professional Summary</h2>
        <p>{{ summary }}</p>
        
        <h2>Skills</h2>
        <div class="skills">
            {% for skill in skills %}
            <span style="background-color: #f0f0f0; padding: 5px 10px; margin: 5px; border-radius: 3px; display: inline-block;">{{ skill }}</span>
            {% endfor %}
        </div>
        
        {% if matched_keywords %}
        <h2>Matched Keywords</h2>
        <div class="skills">
            {% for keyword in matched_keywords %}
            <span style="background-color: #e6f3ff; padding: 5px 10px; margin: 5px; border-radius: 3px; display: inline-block;">{{ keyword }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        <h2>Experience</h2>
        {% for exp in experiences %}
        <div class="experience">
            <h3>{{ exp.role }} - {{ exp.company }}</h3>
            <p><em>{{ exp.years }}</em></p>
            <ul>
                {% for resp in exp.responsibilities %}
                <li>{{ resp }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
        
        <h2>Education</h2>
        {% for edu in education %}
        <div class="education">
            <h3>{{ edu.degree }} in {{ edu.field }}</h3>
            <p>{{ edu.school }} - {{ edu.year }}</p>
        </div>
        {% endfor %}
        
        {% if references %}
        <h2>References</h2>
        {% for ref in references %}
        <div class="references">
            <h3>{{ ref.name }}</h3>
            <p>{{ ref.title }} - {{ ref.company }}</p>
            <p>{{ ref.email }}</p>
        </div>
        {% endfor %}
        {% endif %}
        
        {% if title and company %}
        <div style="margin-top: 40px; padding: 20px; background-color: #f9f9f9; border-left: 4px solid #0077b5;">
            <h3>Targeted for: {{ title }} at {{ company }}</h3>
            {% if location %}<p><strong>Location:</strong> {{ location }}</p>{% endif %}
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    template_file = template_dir / "base_resume.html"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return template_file


def get_sample_job_data(job_type: str = "senior_software_engineer") -> Dict[str, Any]:
    """Get sample job data by type."""
    return SAMPLE_JOB_DATA.get(job_type, SAMPLE_JOB_DATA["senior_software_engineer"])


def get_sample_job_description(job_type: str = "senior_software_engineer") -> str:
    """Get sample job description by type."""
    return SAMPLE_JOB_DESCRIPTIONS.get(job_type, SAMPLE_JOB_DESCRIPTIONS["senior_software_engineer"])


def create_mock_playwright_page():
    """Create a mock Playwright page object for testing."""
    from unittest.mock import Mock
    
    page = Mock()
    page.url = "https://linkedin.com/jobs/view/123456789"
    page.title.return_value = "Senior Software Engineer - TechCorp Inc. | LinkedIn"
    page.locator.return_value.count.return_value = 1
    page.locator.return_value.inner_text.return_value = "Sample text"
    page.locator.return_value.all_inner_texts.return_value = ["Sample text"]
    page.locator.return_value.click.return_value = None
    page.locator.return_value.fill.return_value = None
    page.locator.return_value.clear.return_value = None
    page.locator.return_value.scroll_into_view_if_needed.return_value = None
    page.locator.return_value.hover.return_value = None
    page.locator.return_value.is_checked.return_value = False
    page.locator.return_value.get_attribute.return_value = "test-id"
    page.locator.return_value.set_input_files.return_value = None
    page.locator.return_value.select_option.return_value = None
    page.locator.return_value.nth.return_value = page.locator.return_value
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    page.wait_for_timeout.return_value = None
    page.hover.return_value = None
    page.mouse.wheel.return_value = None
    page.inner_text.return_value = "Page content"
    page.evaluate.return_value = True
    
    return page


def create_mock_playwright_context():
    """Create a mock Playwright context object for testing."""
    from unittest.mock import Mock
    
    context = Mock()
    context.new_page.return_value = create_mock_playwright_page()
    context.add_cookies.return_value = None
    context.cookies.return_value = []
    
    return context


def create_mock_playwright_browser():
    """Create a mock Playwright browser object for testing."""
    from unittest.mock import Mock
    
    browser = Mock()
    browser.contexts = [create_mock_playwright_context()]
    browser.close.return_value = None
    
    return browser


def create_mock_playwright():
    """Create a mock Playwright instance for testing."""
    from unittest.mock import Mock
    
    playwright = Mock()
    playwright.chromium.launch.return_value = create_mock_playwright_browser()
    playwright.chromium.launch_persistent_context.return_value = create_mock_playwright_context()
    
    return playwright
