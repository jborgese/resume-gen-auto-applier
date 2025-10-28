#!/usr/bin/env python3
"""
Test runner script for resume-generator-auto-applier.

This script provides convenient commands for running different types of tests
and generating test reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for resume-generator-auto-applier")
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "integration", "web", "api", "coverage", "lint", "quick"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        default=1,
        help="Number of parallel test processes (default: 1)"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    parser.add_argument(
        "--coverage-report",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = "python -m pytest"
    
    # Add verbose flag if requested
    if args.verbose:
        base_cmd += " -v"
    
    # Add parallel processing if requested
    if args.parallel > 1:
        base_cmd += f" -n {args.parallel}"
    
    # Add HTML report if requested
    if args.html_report:
        base_cmd += " --html=htmlcov/report.html --self-contained-html"
    
    # Add coverage if requested
    if args.coverage_report:
        base_cmd += " --cov=src --cov-report=html:htmlcov --cov-report=term-missing"
    
    # Test type specific commands
    commands = {
        "all": f"{base_cmd} tests/",
        "unit": f"{base_cmd} tests/unit/ -m unit",
        "integration": f"{base_cmd} tests/integration/ -m integration",
        "web": f"{base_cmd} tests/ -m web",
        "api": f"{base_cmd} tests/ -m api",
        "coverage": f"{base_cmd} tests/ --cov=src --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml",
        "lint": "python -m flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503",
        "quick": f"{base_cmd} tests/unit/ -m unit --tb=short -x"
    }
    
    # Run the appropriate command
    command = commands[args.test_type]
    description = f"{args.test_type.title()} tests"
    
    success = run_command(command, description)
    
    if success:
        print(f"\n🎉 All {args.test_type} tests passed!")
        
        # Show additional information based on test type
        if args.test_type == "coverage":
            print("\n📊 Coverage report generated in htmlcov/index.html")
        elif args.html_report:
            print("\n📄 HTML report generated in htmlcov/report.html")
    else:
        print(f"\n💥 {args.test_type.title()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
