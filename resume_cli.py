#!/usr/bin/env python3
"""
Main entry point for Resume Generator & Auto-Applicator CLI

This script provides the enhanced CLI interface using Click and Rich.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set PYTHONPATH to include src directory
os.environ['PYTHONPATH'] = str(Path(__file__).parent / "src")

# Import and run the CLI
try:
    from cli import cli
    if __name__ == "__main__":
        cli()
except ImportError as e:
    print(f"Error importing CLI: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)
