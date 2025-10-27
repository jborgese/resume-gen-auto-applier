#!/usr/bin/env python3
"""
Wrapper script to run main.py without GLib-GIO warnings.

This script redirects stderr to filter out GLib-GIO warnings while preserving
other important error messages.
"""

import sys
import subprocess
import re
from io import StringIO


def filter_glib_warnings(line):
    """Filter out GLib-GIO warnings while preserving other output."""
    # Patterns to filter out
    glib_patterns = [
        r'.*GLib-GIO-WARNING.*',
        r'.*UWP app.*supports.*extensions.*',
        r'.*Unexpectedly.*UWP app.*',
    ]
    
    for pattern in glib_patterns:
        if re.match(pattern, line):
            return None
    
    return line


def run_with_filtered_output():
    """Run main.py with filtered stderr output."""
    try:
        # Run the main script
        process = subprocess.Popen(
            [sys.executable, 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Process stdout in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            sys.stdout.flush()
        
        # Process stderr and filter out GLib warnings
        stderr_output = process.stderr.read()
        for line in stderr_output.splitlines():
            filtered_line = filter_glib_warnings(line)
            if filtered_line:
                print(f"STDERR: {filtered_line}", file=sys.stderr)
        
        # Wait for process to complete
        return_code = process.wait()
        return return_code
        
    except Exception as e:
        print(f"Error running main.py: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = run_with_filtered_output()
    sys.exit(exit_code)


