@echo off
REM Resume Generator & Auto-Applicator CLI Launcher
REM This script activates the virtual environment and runs the enhanced CLI

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate.bat
    echo Finally: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the CLI
python resume_cli.py %*

pause
