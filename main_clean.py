#!/usr/bin/env python3
"""
Clean version of main.py that suppresses GLib-GIO warnings.

This script runs the original main.py but filters out GLib warnings.
"""

import subprocess
import sys
import re
from pathlib import Path

def filter_glib_warnings(text):
    """Filter out GLib-GIO warnings from text."""
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip lines containing GLib warnings
        if not any(pattern in line for pattern in [
            'GLib-GIO-WARNING',
            'UWP app',
            'supports.*extensions.*but has no verbs',
            'Unexpectedly.*UWP app'
        ]):
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def main():
    """Run the main script with filtered output."""
    try:
        # Run the original main.py
        result = subprocess.run(
            [sys.executable, 'main.py'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Filter stdout
        filtered_stdout = filter_glib_warnings(result.stdout)
        if filtered_stdout.strip():
            print(filtered_stdout)
        
        # Filter stderr
        filtered_stderr = filter_glib_warnings(result.stderr)
        if filtered_stderr.strip():
            print(filtered_stderr, file=sys.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"Error running main.py: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())


