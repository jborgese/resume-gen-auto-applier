# PowerShell script to run main.py without GLib-GIO warnings
# This script filters out the GLib warnings while preserving other output

# Change to the project directory
Set-Location "C:\Users\Nipply Nathan\Documents\GitHub\resume-gen-auto-applier"

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\activate.ps1") {
    .\venv\Scripts\activate.ps1
}

# Run Python with output filtering
python main.py 2>&1 | Where-Object { 
    $_ -notmatch "GLib-GIO-WARNING" -and 
    $_ -notmatch "UWP app.*supports.*extensions" -and
    $_ -notmatch "Unexpectedly.*UWP app"
}


