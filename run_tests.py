#!/usr/bin/env python3
"""
Simple test runner for the PolicyCraft project.

Usage:
  python run_tests.py                # run all tests with project config
  python run_tests.py -q -k login    # pass any extra pytest args

This script ensures pytest runs in the PolicyCraft directory, so that
pytest.ini and the tests/ tree are discovered correctly.
"""
import os
import sys
import subprocess


def main() -> int:
    repo_root = os.path.dirname(os.path.abspath(__file__))
    policycraft_dir = os.path.join(repo_root, "PolicyCraft")

    if not os.path.isdir(policycraft_dir):
        print("ERROR: 'PolicyCraft' directory not found next to run_tests.py", file=sys.stderr)
        return 2

    # Build the command: python -m pytest [user args...]
    cmd = [sys.executable, "-m", "pytest"] + sys.argv[1:]

    try:
        # Run pytest with cwd set to PolicyCraft so pytest.ini is picked up
        completed = subprocess.run(cmd, cwd=policycraft_dir)
        return completed.returncode
    except FileNotFoundError:
        print("ERROR: pytest is not installed. Try: pip install -r PolicyCraft/requirements.txt", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Unexpected error while running tests: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
