#!/usr/bin/env python3
"""
PolicyCraft Setup Checker

This script verifies that all required components are properly installed
and configured for new users downloading the application from GitHub.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path

def print_header():
    """Display the setup checker header."""
    print("🔍 PolicyCraft Setup Checker")
    print("=" * 50)
    print("Verifying your installation...\n")

def check_python_version():
    """Check if Python version meets requirements."""
    print("🐍 Python Version Check")
    print("-" * 30)
    
    version = sys.version_info
    print(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✅ Python version is compatible (3.9+ required)")
        return True
    else:
        print("❌ Python version too old. Please upgrade to Python 3.9 or higher.")
        return False

def check_core_dependencies():
    """Check if core dependencies are installed."""
    print("\n📦 Core Dependencies Check")
    print("-" * 30)
    
    core_packages = [
        'flask', 'pymongo', 'pandas', 'numpy', 'requests', 'dotenv'
    ]
    
    missing = []
    for package in core_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All core dependencies are installed")
    return True

def check_nlp_dependencies():
    """Check if NLP dependencies are installed."""
    print("\n🧠 NLP Dependencies Check")
    print("-" * 30)
    
    nlp_packages = [
        'spacy', 'sklearn', 'nltk', 'sentence_transformers', 'contractions'
    ]
    
    missing = []
    for package in nlp_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing NLP packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All NLP dependencies are installed")
    return True

def check_spacy_model():
    """Check if spaCy English model is downloaded."""
    print("\n📚 spaCy Model Check")
    print("-" * 30)
    
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✅ spaCy English model (en_core_web_sm) is available")
        return True
    except OSError:
        print("❌ spaCy English model not found")
        print("   Run: python -m spacy download en_core_web_sm")
        return False
    except Exception as e:
        print(f"❌ Error loading spaCy model: {e}")
        return False

def check_nltk_data():
    """Check if NLTK data is downloaded."""
    print("\n📖 NLTK Data Check")
    print("-" * 30)
    
    try:
        import nltk
        required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        missing_data = []
        for item in required_data:
            try:
                if item == 'punkt':
                    nltk.data.find('tokenizers/punkt')
                elif item in ['stopwords', 'wordnet']:
                    nltk.data.find(f'corpora/{item}')
                else:
                    nltk.data.find(f'taggers/{item}')
                print(f"✅ {item}")
            except LookupError:
                print(f"❌ {item} - MISSING")
                missing_data.append(item)
        
        if missing_data:
            print(f"\n⚠️  Missing NLTK data: {', '.join(missing_data)}")
            print("   Run: python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')\"")
            return False
        
        print("\n✅ All NLTK data is available")
        return True
        
    except Exception as e:
        print(f"❌ Error checking NLTK data: {e}")
        return False

def check_directories():
    """Check if required directories exist."""
    print("\n📁 Directory Structure Check")
    print("-" * 30)
    
    required_dirs = [
        'src', 'docs', 'data', 'logs', 'PolicyCraft-Databases'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - MISSING")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"\n⚠️  Missing directories: {', '.join(missing_dirs)}")
        print("   These should be created automatically when you run the application")
        return False
    
    print("\n✅ All required directories exist")
    return True

def check_config_files():
    """Check if configuration files exist."""
    print("\n⚙️  Configuration Files Check")
    print("-" * 30)
    
    config_files = [
        'config.py', 'app.py', 'requirements.txt'
    ]
    
    missing_files = []
    for file_name in config_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - MISSING")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️  Missing configuration files: {', '.join(missing_files)}")
        return False
    
    print("\n✅ All configuration files exist")
    return True

def run_validation():
    """Run the complete setup validation."""
    print_header()
    
    checks = [
        check_python_version(),
        check_core_dependencies(),
        check_nlp_dependencies(),
        check_spacy_model(),
        check_nltk_data(),
        check_directories(),
        check_config_files()
    ]
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 CONGRATULATIONS! Your PolicyCraft installation is complete.")
        print("   You can now run: python app.py")
        print("   Then open: http://localhost:5001")
        return True
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please resolve the issues above.")
        print("   Refer to the README.md for detailed installation instructions.")
        return False

if __name__ == "__main__":
    try:
        success = run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup check: {e}")
        sys.exit(1)
