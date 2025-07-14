# !/usr/bin/env python3
"""
Test execution script for PolicyCraft
Runs comprehensive test suite with coverage reporting and detailed output.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --fast       # Run only critical tests
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --verbose    # Detailed output

Author: Jacek Robert Kszczot
Project: MSc AI & Data Science - COM7016
"""

import subprocess
import sys
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with error handling."""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Please ensure pytest is installed: pip install pytest pytest-cov")
        return False

def check_test_environment():
    """Check if test environment is properly set up."""
    print("🔍 Checking test environment...")
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    
    # Check if src modules are importable
    try:
        sys.path.insert(0, str(Path.cwd()))
        from src.nlp.text_processor import TextProcessor
        print("✅ PolicyCraft modules importable")
    except ImportError as e:
        print(f"❌ Cannot import PolicyCraft modules: {e}")
        print("Ensure you're running from the project root directory")
        return False
    
    # Check if test directory exists
    if not Path("tests").exists():
        print("❌ tests/ directory not found")
        return False
    
    print("✅ Test environment ready")
    return True

def run_critical_tests():
    """Run only the most critical tests (for fast validation)."""
    critical_test_files = [
        "tests/test_recommendation/test_engine.py::TestRecommendationEngine::test_full_recommendation_generation_workflow",
        "tests/test_nlp/test_text_processor.py::TestTextProcessor::test_extract_and_clean_workflow",
        "tests/test_nlp/test_policy_classifier.py::TestPolicyClassifier::test_classify_moderate_policy",
        "tests/test_integration/test_analysis_pipeline.py::TestAnalysisPipeline::test_full_analysis_workflow"
    ]
    
    cmd = ["python", "-m", "pytest"] + critical_test_files + ["-v", "--tb=short"]
    return run_command(cmd, "Critical Tests")

def run_all_tests(verbose=False, coverage=False):
    """Run complete test suite."""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always use verbose for better output
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    cmd.extend(["--tb=short", "--durations=10"])
    
    return run_command(cmd, "Complete Test Suite")

def run_specific_module(module_name):
    """Run tests for specific module."""
    test_path = f"tests/test_{module_name}/"
    if not Path(test_path).exists():
        test_path = f"tests/test_{module_name}.py"
    
    if not Path(test_path).exists():
        print(f"❌ Test path not found: {test_path}")
        return False
    
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
    return run_command(cmd, f"Module Tests: {module_name}")

def generate_test_report():
    """Generate comprehensive test report."""
    print("\n📊 Generating Test Report...")
    
    # Run tests with coverage and JUnit XML output
    cmd = [
        "python", "-m", "pytest", "tests/",
        "--cov=src",
        "--cov-report=html:test_reports/coverage",
        "--cov-report=xml:test_reports/coverage.xml",
        "--cov-report=term",
        "--junit-xml=test_reports/junit.xml",
        "-v"
    ]
    
    # Create reports directory
    Path("test_reports").mkdir(exist_ok=True)
    
    success = run_command(cmd, "Test Report Generation")
    
    if success:
        print("\n📋 Test Reports Generated:")
        print("  📊 Coverage HTML: test_reports/coverage/index.html")
        print("  📄 Coverage XML: test_reports/coverage.xml")
        print("  🔧 JUnit XML: test_reports/junit.xml")
    
    return success

def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Run PolicyCraft test suite")
    parser.add_argument("--fast", action="store_true", help="Run only critical tests")
    parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--module", help="Run tests for specific module (e.g., 'nlp', 'recommendation')")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    
    args = parser.parse_args()
    
    print("🧪 PolicyCraft Test Suite")
    print("=" * 50)
    
    # Check environment
    if not check_test_environment():
        sys.exit(1)
    
    success = True
    
    if args.report:
        success = generate_test_report()
    elif args.fast:
        success = run_critical_tests()
    elif args.module:
        success = run_specific_module(args.module)
    else:
        success = run_all_tests(verbose=args.verbose, coverage=args.coverage)
    
    # Print summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test execution completed successfully!")
        print("\n💡 Next steps:")
        print("  - Review any failed tests above")
        print("  - Check coverage report if generated")
        print("  - Run 'python run_tests.py --report' for detailed analysis")
    else:
        print("❌ Test execution failed!")
        print("\n🔧 Troubleshooting:")
        print("  - Check error messages above")
        print("  - Ensure all dependencies are installed")
        print("  - Verify you're in the project root directory")
        sys.exit(1)

if __name__ == "__main__":
    main()