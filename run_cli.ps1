# Resume Generator & Auto-Applicator CLI Launcher (PowerShell)
# This script activates the virtual environment and runs the enhanced CLI

# Set execution policy for this session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Navigate to script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: .\venv\Scripts\activate.ps1" -ForegroundColor Yellow
    Write-Host "Finally: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\activate.ps1"

# Run the CLI
Write-Host "Starting Resume Generator CLI..." -ForegroundColor Green
python resume_cli.py $args

Read-Host "Press Enter to exit"
