#!/usr/bin/env python3
"""
Simple test runner for the PolicyCraft project.

Usage:
  python run_tests.py                # run all tests with project config
  python run_tests.py -q -k login    # pass any extra pytest args

This script ensures pytest runs in the current PolicyCraft directory, so that
pytest.ini and the tests/ tree are discovered correctly.
"""
import os
import sys
import subprocess


def main() -> int:
    # We're already in the PolicyCraft directory
    policycraft_dir = os.getcwd()

    if not os.path.isfile("pytest.ini"):
        print("ERROR: pytest.ini not found. Make sure you're in the PolicyCraft directory.", file=sys.stderr)
        return 2

    # Build the command: python -m pytest [user args...]
    cmd = [sys.executable, "-m", "pytest"] + sys.argv[1:]

    try:
        # Run pytest with current working directory
        completed = subprocess.run(cmd, cwd=policycraft_dir)
        return completed.returncode
    except FileNotFoundError:
        print("ERROR: pytest is not installed. Try: pip install -r requirements.txt", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Unexpected error while running tests: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
