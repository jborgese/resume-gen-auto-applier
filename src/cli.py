#!/usr/bin/env python3
"""
Enhanced CLI for Resume Generator & Auto-Applicator

This module provides a modern command-line interface using Click and Rich
for improved user experience with colored output, progress bars, and tables.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from rich.syntax import Syntax

# Initialize Rich console first
console = Console()

# Redirect stderr to filter GLib warnings before any other imports
class GLibWarningFilter:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
    
    def write(self, text):
        # Filter out GLib-GIO warnings
        if 'GLib-GIO-WARNING' not in text and 'UWP app' not in text:
            self.original_stderr.write(text)
            self.original_stderr.flush()
    
    def flush(self):
        self.original_stderr.flush()

# Apply the filter
sys.stderr = GLibWarningFilter(sys.stderr)

# Global configuration
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def print_banner():
    """Print the application banner."""
    banner = """
===============================================================
                Resume Generator & Auto-Applicator           
                      Enhanced CLI v2.0                     
===============================================================
"""
    console.print(Panel(banner, style="bold blue"))


def check_environment() -> bool:
    """Check if the environment is properly configured."""
    issues = []
    
    # Check for .env file
    if not Path(".env").exists():
        issues.append("Missing .env file with LinkedIn credentials")
    
    # Check for personal_info.yaml
    if not Path("personal_info.yaml").exists():
        issues.append("Missing personal_info.yaml file")
    
    # Check LinkedIn credentials
    linkedin_email = os.getenv("LINKEDIN_EMAIL")
    linkedin_password = os.getenv("LINKEDIN_PASSWORD")
    
    if not linkedin_email or not linkedin_password:
        issues.append("LinkedIn credentials not configured")
    
    if issues:
        console.print("\n[red]ERROR: Environment Issues Found:[/red]")
        for issue in issues:
            console.print(f"  - {issue}")
        console.print("\n[yellow]TIP: Run 'resume-cli config setup' to configure your environment[/yellow]")
        return False
    
    return True


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, verbose, debug):
    """Resume Generator & Auto-Applicator - Enhanced CLI"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    # Set environment variables based on flags
    if debug:
        os.environ['DEBUG'] = 'true'
    if verbose:
        os.environ['VERBOSE'] = 'true'
    
    # Print banner
    print_banner()


@cli.command()
@click.option('--url', '-u', help='LinkedIn job search URL')
@click.option('--max-jobs', '-m', default=5, help='Maximum number of jobs to process')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--apply', is_flag=True, help='Automatically apply to jobs')
@click.pass_context
def scrape(ctx, url, max_jobs, headless, apply):
    """Scrape jobs from LinkedIn and optionally apply to them."""
    
    if not check_environment():
        sys.exit(1)
    
    # Default search URL if not provided
    if not url:
        url = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=United%20States"
    
    console.print(f"\n[bold blue]Scraping Jobs[/bold blue]")
    console.print(f"URL: {url}")
    console.print(f"Max Jobs: {max_jobs}")
    console.print(f"Headless: {headless}")
    console.print(f"Auto-Apply: {apply}")
    
    # Set environment variables
    if headless:
        os.environ['HEADLESS_MODE'] = 'true'
    
    try:
        # Import scraper dynamically to avoid import issues
        sys.path.insert(0, str(Path(__file__).parent))
        from scraper import scrape_jobs_from_search
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Scraping jobs...", total=None)
            
            # Scrape jobs
            jobs = scrape_jobs_from_search(
                search_url=url,
                email=os.getenv("LINKEDIN_EMAIL"),
                password=os.getenv("LINKEDIN_PASSWORD"),
                max_jobs=max_jobs
            )
            
            progress.update(task, description="Processing complete!")
        
        if not jobs:
            console.print("[yellow]WARNING: No jobs were processed[/yellow]")
            return
        
        # Display results
        display_job_results(jobs)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]STOPPED: Scraping stopped by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]ERROR: Scraping failed: {e}[/red]")
        if ctx.obj['debug']:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option('--template', '-t', help='Resume template to use')
@click.option('--output', '-o', help='Output directory for resumes')
@click.pass_context
def build_resume(ctx, template, output):
    """Build a resume from personal information."""
    
    if not check_environment():
        sys.exit(1)
    
    console.print("\n[bold blue]Building Resume[/bold blue]")
    
    try:
        # Load personal info
        with open("personal_info.yaml", "r", encoding="utf-8") as f:
            personal_info = yaml.safe_load(f)
        
        # Import resume builder dynamically
        sys.path.insert(0, str(Path(__file__).parent))
        from resume_builder import ResumeBuilder
        
        # Build resume
        builder = ResumeBuilder(personal_info)
        output_path = builder.build_resume(
            template=template or "templates/base_resume.html",
            output_dir=output or "output/resumes"
        )
        
        console.print(f"[green]SUCCESS: Resume built successfully![/green]")
        console.print(f"Output: {output_path}")
        
    except Exception as e:
        console.print(f"[red]ERROR: Resume building failed: {e}[/red]")
        if ctx.obj['debug']:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', help='Job description file to analyze')
@click.option('--text', '-t', help='Job description text to analyze')
@click.pass_context
def analyze(ctx, file, text):
    """Analyze job description and extract keywords."""
    
    if not file and not text:
        console.print("[red]ERROR: Please provide either --file or --text option[/red]")
        sys.exit(1)
    
    console.print("\n[bold blue]Analyzing Job Description[/bold blue]")
    
    try:
        # Import keyword extractor dynamically
        sys.path.insert(0, str(Path(__file__).parent))
        from keyword_extractor import extract_keywords
        
        if file:
            with open(file, 'r', encoding='utf-8') as f:
                job_text = f.read()
        else:
            job_text = text
        
        # Extract keywords
        keywords = extract_keywords(job_text)
        
        # Display results in a table
        table = Table(title="Extracted Keywords")
        table.add_column("Keyword", style="cyan")
        table.add_column("Category", style="green")
        
        for keyword in keywords[:20]:  # Show top 20
            # Simple categorization based on common patterns
            if any(tech in keyword.lower() for tech in ['python', 'django', 'flask', 'fastapi', 'javascript', 'react', 'vue']):
                category = "Programming"
            elif any(tech in keyword.lower() for tech in ['aws', 'docker', 'kubernetes', 'devops', 'ci/cd']):
                category = "DevOps"
            elif any(tech in keyword.lower() for tech in ['sql', 'postgresql', 'mysql', 'database', 'mongodb']):
                category = "Database"
            elif any(tech in keyword.lower() for tech in ['api', 'rest', 'microservices', 'architecture']):
                category = "Architecture"
            else:
                category = "Other"
            
            table.add_row(keyword, category)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]ERROR: Analysis failed: {e}[/red]")
        if ctx.obj['debug']:
            console.print_exception()
        sys.exit(1)


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
def setup():
    """Interactive setup for configuration files."""
    console.print("\n[bold blue]Configuration Setup[/bold blue]")
    
    # Check existing files
    env_exists = Path(".env").exists()
    personal_exists = Path("personal_info.yaml").exists()
    
    if env_exists:
        console.print("[green]SUCCESS: .env file already exists[/green]")
    else:
        console.print("[yellow]WARNING: .env file not found[/yellow]")
        if Confirm.ask("Create .env file?"):
            create_env_file()
    
    if personal_exists:
        console.print("[green]SUCCESS: personal_info.yaml already exists[/green]")
    else:
        console.print("[yellow]WARNING: personal_info.yaml not found[/yellow]")
        if Confirm.ask("Create personal_info.yaml file?"):
            create_personal_info_file()
    
    console.print("\n[green]SUCCESS: Configuration setup complete![/green]")


@config.command()
def validate():
    """Validate current configuration."""
    console.print("\n[bold blue]Validating Configuration[/bold blue]")
    
    issues = []
    warnings = []
    
    # Check .env file
    if not Path(".env").exists():
        issues.append("Missing .env file")
    else:
        # Check required variables
        required_vars = ['LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD']
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Missing {var} in .env")
    
    # Check personal_info.yaml
    if not Path("personal_info.yaml").exists():
        issues.append("Missing personal_info.yaml")
    else:
        try:
            with open("personal_info.yaml", "r") as f:
                personal_info = yaml.safe_load(f)
            
            required_fields = ['first_name', 'last_name', 'email', 'phone']
            for field in required_fields:
                if not personal_info.get(field):
                    warnings.append(f"Missing {field} in personal_info.yaml")
        except Exception as e:
            issues.append(f"Invalid personal_info.yaml: {e}")
    
    # Display results
    if issues:
        console.print("[red]ERROR: Critical Issues:[/red]")
        for issue in issues:
            console.print(f"  - {issue}")
    
    if warnings:
        console.print("[yellow]WARNING: Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  - {warning}")
    
    if not issues and not warnings:
        console.print("[green]SUCCESS: Configuration is valid![/green]")


@config.command()
def show():
    """Show current configuration (without sensitive data)."""
    console.print("\n[bold blue]Current Configuration[/bold blue]")
    
    # Show environment variables (masked)
    env_table = Table(title="Environment Variables")
    env_table.add_column("Variable", style="cyan")
    env_table.add_column("Value", style="green")
    
    env_vars = ['LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'HEADLESS_MODE', 'DEBUG']
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if 'PASSWORD' in var or 'EMAIL' in var:
            value = "***" if value != "Not set" else value
        env_table.add_row(var, value)
    
    console.print(env_table)
    
    # Show personal info (if exists)
    if Path("personal_info.yaml").exists():
        try:
            with open("personal_info.yaml", "r") as f:
                personal_info = yaml.safe_load(f)
            
            personal_table = Table(title="Personal Information")
            personal_table.add_column("Field", style="cyan")
            personal_table.add_column("Value", style="green")
            
            fields = ['first_name', 'last_name', 'email', 'phone', 'linkedin', 'github']
            for field in fields:
                value = personal_info.get(field, "Not set")
                personal_table.add_row(field.replace('_', ' ').title(), value)
            
            console.print(personal_table)
        except Exception as e:
            console.print(f"[red]Error reading personal_info.yaml: {e}[/red]")


def create_env_file():
    """Create .env file interactively."""
    console.print("\n[bold]Creating .env file...[/bold]")
    
    linkedin_email = Prompt.ask("LinkedIn Email")
    linkedin_password = Prompt.ask("LinkedIn Password", password=True)
    
    env_content = f"""# LinkedIn Credentials
LINKEDIN_EMAIL={linkedin_email}
LINKEDIN_PASSWORD={linkedin_password}

# Optional Settings
HEADLESS_MODE=false
DEBUG=false
VERBOSE=false
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    console.print("[green]SUCCESS: .env file created[/green]")


def create_personal_info_file():
    """Create personal_info.yaml file interactively."""
    console.print("\n[bold]Creating personal_info.yaml file...[/bold]")
    
    # Copy from example
    if Path("personal_info.yaml.example").exists():
        import shutil
        shutil.copy("personal_info.yaml.example", "personal_info.yaml")
        console.print("[green]SUCCESS: personal_info.yaml created from example[/green]")
        console.print("[yellow]TIP: Please edit personal_info.yaml with your information[/yellow]")
    else:
        console.print("[red]ERROR: personal_info.yaml.example not found[/red]")


def display_job_results(jobs: List[Dict[str, Any]]):
    """Display job results in a formatted table."""
    if not jobs:
        return
    
    table = Table(title=f"Job Results ({len(jobs)} jobs)")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Title", style="white")
    table.add_column("Company", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Resume", style="yellow")
    
    for i, job in enumerate(jobs, 1):
        title = job.get("title", "N/A")[:50] + "..." if len(job.get("title", "")) > 50 else job.get("title", "N/A")
        company = job.get("company", "N/A")
        status = job.get("apply_status", "skipped")
        
        # Color code status
        if status == "applied":
            status_display = f"[green]{status}[/green]"
        elif status == "failed":
            status_display = f"[red]{status}[/red]"
        else:
            status_display = f"[yellow]{status}[/yellow]"
        
        resume_path = job.get("resume_pdf", "")
        resume_display = "YES" if resume_path else "NO"
        
        table.add_row(str(i), title, company, status_display, resume_display)
    
    console.print(table)
    
    # Summary
    applied_count = sum(1 for job in jobs if job.get("apply_status") == "applied")
    failed_count = sum(1 for job in jobs if job.get("apply_status") == "failed")
    skipped_count = len(jobs) - applied_count - failed_count
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  - Applied: [green]{applied_count}[/green]")
    console.print(f"  - Failed: [red]{failed_count}[/red]")
    console.print(f"  - Skipped: [yellow]{skipped_count}[/yellow]")


@cli.command()
def version():
    """Show version information."""
    console.print("\n[bold blue]Version Information[/bold blue]")
    
    version_info = {
        "Application": "Resume Generator & Auto-Applicator",
        "Version": "2.0.0",
        "Python": sys.version.split()[0],
        "Platform": sys.platform,
        "Click": click.__version__,
        "Rich": "14.2.0"
    }
    
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")
    
    for component, version in version_info.items():
        table.add_row(component, version)
    
    console.print(table)


if __name__ == "__main__":
    cli()