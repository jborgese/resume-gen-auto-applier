#!/usr/bin/env python3
"""
CLI Demo Script

This script demonstrates the enhanced CLI features and capabilities.
Run this to see the CLI in action with sample data.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_demo_files():
    """Create demo files for testing."""
    
    # Create demo .env file
    env_content = """# Demo LinkedIn Credentials
LINKEDIN_EMAIL=demo@example.com
LINKEDIN_PASSWORD=demo_password

# Optional Settings
HEADLESS_MODE=false
DEBUG=false
VERBOSE=false
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    # Create demo personal_info.yaml
    personal_content = """first_name: Demo
last_name: User
email: demo@example.com
phone: "(555) 123-4567"
address:
  street: 123 Demo Street
  city: Demo City
  state: DC
  zip: "12345"
  country: USA
linkedin: https://www.linkedin.com/in/demo-user
github: https://github.com/demo-user

job_history:
  - title: Senior Software Engineer
    company: Demo Corp
    location: Demo City, DC
    start_date: 2022-01
    end_date: present
    responsibilities:
      - Developed web applications using Python and JavaScript
      - Led team of developers
      - Implemented CI/CD pipelines

education:
  - degree: Bachelor of Science in Computer Science
    institution: Demo University
    graduation_date: 05-2020
    location: Demo City, DC
"""
    
    with open("personal_info.yaml", "w") as f:
        f.write(personal_content)
    
    # Create demo job description
    job_desc = """We are looking for a Senior Python Developer to join our team.

Requirements:
- 5+ years of Python development experience
- Experience with Django, Flask, or FastAPI
- Knowledge of SQL databases (PostgreSQL, MySQL)
- Experience with REST APIs
- Git version control
- Docker containerization
- AWS cloud services
- Agile development methodology

Responsibilities:
- Develop and maintain web applications
- Design and implement REST APIs
- Work with databases and data processing
- Collaborate with cross-functional teams
- Write clean, maintainable code
- Participate in code reviews

Nice to have:
- Machine learning experience
- DevOps knowledge
- Frontend development (React, Vue.js)
- Microservices architecture
"""
    
    with open("demo_job_description.txt", "w") as f:
        f.write(job_desc)

def run_demo():
    """Run the CLI demo."""
    
    print("=" * 60)
    print("Resume Generator & Auto-Applicator CLI Demo")
    print("=" * 60)
    print()
    
    # Create demo files
    print("Creating demo files...")
    create_demo_files()
    print("SUCCESS: Demo files created")
    print()
    
    # Import CLI
    from cli import cli
    
    print("Available CLI commands:")
    print("1. python resume_cli.py --help")
    print("2. python resume_cli.py version")
    print("3. python resume_cli.py config validate")
    print("4. python resume_cli.py config show")
    print("5. python resume_cli.py analyze --file demo_job_description.txt")
    print("6. python resume_cli.py build-resume")
    print()
    
    print("Try running these commands to see the CLI in action!")
    print()
    
    # Show version info
    print("Running version command...")
    try:
        cli(['version'])
    except SystemExit:
        pass
    
    print()
    print("Demo complete! The CLI is ready to use.")
    print("Run 'python resume_cli.py --help' to see all available commands.")

if __name__ == "__main__":
    run_demo()
