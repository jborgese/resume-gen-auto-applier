# Resume Generator & Auto-Applicator - Enhanced CLI

## Overview

The Resume Generator & Auto-Applicator now features a modern, enhanced command-line interface built with **Click** and **Rich** for improved user experience. The CLI provides colored output, progress bars, tables, and interactive prompts.

## Features

- 🎨 **Rich Output**: Colored text, tables, progress bars, and panels
- ⚡ **Interactive Commands**: Easy-to-use commands with helpful options
- 🔧 **Configuration Management**: Built-in setup and validation tools
- 📊 **Progress Tracking**: Visual progress indicators for long-running operations
- 🛡️ **Error Handling**: Clear error messages with helpful suggestions
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

1. **Python 3.9+** (tested with 3.9.7)
2. **Virtual Environment** (recommended)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd resume-gen-auto-applier
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

## Quick Start

### 1. Configuration Setup

Run the interactive setup to configure your environment:

```bash
python resume_cli.py config setup
```

This will guide you through:
- Creating `.env` file with LinkedIn credentials
- Setting up `personal_info.yaml` with your information

### 2. Validate Configuration

Check if your configuration is properly set up:

```bash
python resume_cli.py config validate
```

### 3. View Configuration

See your current configuration (without sensitive data):

```bash
python resume_cli.py config show
```

## CLI Commands

### Main Commands

#### `scrape` - Scrape Jobs from LinkedIn

Scrape job listings and optionally apply to them:

```bash
# Basic scraping
python resume_cli.py scrape

# With custom URL and options
python resume_cli.py scrape --url "https://linkedin.com/jobs/search/?keywords=python" --max-jobs 10 --headless

# With auto-apply
python resume_cli.py scrape --apply --max-jobs 5
```

**Options:**
- `--url, -u`: LinkedIn job search URL
- `--max-jobs, -m`: Maximum number of jobs to process (default: 5)
- `--headless`: Run browser in headless mode
- `--apply`: Automatically apply to jobs

#### `build-resume` - Build Resume

Generate a resume from your personal information:

```bash
# Build with default template
python resume_cli.py build-resume

# With custom template and output directory
python resume_cli.py build-resume --template "custom_template.html" --output "my_resumes"
```

**Options:**
- `--template, -t`: Resume template to use
- `--output, -o`: Output directory for resumes

#### `analyze` - Analyze Job Description

Extract keywords and analyze job descriptions:

```bash
# Analyze text directly
python resume_cli.py analyze --text "We are looking for a Python developer with Django experience..."

# Analyze from file
python resume_cli.py analyze --file "job_description.txt"
```

**Options:**
- `--file, -f`: Job description file to analyze
- `--text, -t`: Job description text to analyze

### Configuration Commands

#### `config setup` - Interactive Setup

Set up configuration files interactively:

```bash
python resume_cli.py config setup
```

#### `config validate` - Validate Configuration

Check if your configuration is valid:

```bash
python resume_cli.py config validate
```

#### `config show` - Show Configuration

Display current configuration (without sensitive data):

```bash
python resume_cli.py config show
```

### Utility Commands

#### `version` - Show Version Information

Display version information and dependencies:

```bash
python resume_cli.py version
```

## Global Options

All commands support these global options:

- `--verbose, -v`: Enable verbose output
- `--debug, -d`: Enable debug mode
- `--help, -h`: Show help message

## Examples

### Complete Workflow

```bash
# 1. Setup (first time only)
python resume_cli.py config setup

# 2. Validate configuration
python resume_cli.py config validate

# 3. Scrape and apply to jobs
python resume_cli.py scrape --apply --max-jobs 10 --headless

# 4. Build a custom resume
python resume_cli.py build-resume --output "output/resumes"
```

### Debug Mode

Run with debug mode for detailed output:

```bash
python resume_cli.py --debug scrape --max-jobs 3
```

### Verbose Output

Get detailed information about operations:

```bash
python resume_cli.py --verbose config show
```

## Windows Support

### Batch File

Use the provided batch file for easy execution:

```cmd
run_cli.bat --help
run_cli.bat scrape --max-jobs 5
```

### PowerShell Script

Use the PowerShell script for better Windows support:

```powershell
.\run_cli.ps1 --help
.\run_cli.ps1 scrape --max-jobs 5
```

## Configuration Files

### `.env` File

Contains environment variables:

```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# Optional Settings
HEADLESS_MODE=false
DEBUG=false
VERBOSE=false
```

### `personal_info.yaml`

Contains your personal information for resume generation:

```yaml
first_name: John
last_name: Doe
email: john.doe@example.com
phone: "(555) 123-4567"
# ... more fields
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root directory
2. **Unicode Errors**: The CLI uses ASCII characters for Windows compatibility
3. **Configuration Issues**: Run `config validate` to check your setup
4. **Browser Issues**: Ensure Playwright browsers are installed

### Debug Mode

Enable debug mode for detailed error information:

```bash
python resume_cli.py --debug <command>
```

### Environment Variables

Set these environment variables for debugging:

```bash
export DEBUG=true
export VERBOSE=true
export HEADLESS_MODE=true
```

## Development

### Adding New Commands

To add new commands to the CLI:

1. Add the command function to `src/cli.py`
2. Use the `@cli.command()` decorator
3. Add appropriate options with `@click.option()`
4. Use Rich components for output formatting

### Testing

Run tests to ensure everything works:

```bash
python -m pytest tests/
```

## Migration from Old CLI

The old `main.py` script is still available for backward compatibility. To migrate:

1. **Old way**: `python main.py`
2. **New way**: `python resume_cli.py scrape`

The new CLI provides the same functionality with better user experience.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the CLI
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
