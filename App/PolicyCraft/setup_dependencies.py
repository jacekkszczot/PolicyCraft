#!/usr/bin/env python3
"""
PolicyCraft Dependency Setup Script
===================================

This script automatically installs and configures all dependencies required
for full PolicyCraft functionality, including NLP models and data.

Usage:
    python setup_dependencies.py

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import subprocess
import sys
import os
import ssl
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors gracefully."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_ssl_context():
    """Setup SSL context for downloads."""
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

def main():
    """Main setup function."""
    print("🚀 PolicyCraft Dependency Setup")
    print("=" * 50)
    print("This script will install and configure all dependencies")
    print("required for full PolicyCraft functionality.\n")
    
    setup_ssl_context()
    
    # 1. Install Python packages
    if not run_command("pip install -r requirements.txt", 
                      "Installing Python packages from requirements.txt"):
        print("❌ Failed to install Python packages. Please check your pip installation.")
        sys.exit(1)
    
    # 2. Download spaCy model
    if not run_command("python -m spacy download en_core_web_sm", 
                      "Downloading spaCy English model"):
        print("⚠️  spaCy model download failed. You may need to install manually.")
    
    # 3. Download NLTK data
    print("🔧 Downloading NLTK data...")
    try:
        import nltk
        nltk_downloads = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        for package in nltk_downloads:
            try:
                nltk.download(package, quiet=True)
                print(f"✅ NLTK {package} downloaded")
            except Exception as e:
                print(f"⚠️  NLTK {package} download failed: {e}")
    except ImportError:
        print("⚠️  NLTK not available for data download")
    
    # 4. Setup environment variables
    env_file = Path(".env")
    if not env_file.exists():
        print("🔧 Creating .env file with advanced features enabled...")
        with open(env_file, "w") as f:
            f.write("# PolicyCraft Configuration\n")
            f.write("FEATURE_ADVANCED_ENGINE=1\n")
        print("✅ .env file created")
    else:
        # Check if advanced engine is enabled
        with open(env_file, "r") as f:
            content = f.read()
        
        if "FEATURE_ADVANCED_ENGINE" not in content:
            print("🔧 Adding advanced engine configuration to .env...")
            with open(env_file, "a") as f:
                f.write("\n# Enable advanced analysis engine\n")
                f.write("FEATURE_ADVANCED_ENGINE=1\n")
            print("✅ Advanced engine enabled in .env")
        else:
            print("✅ .env file already configured")
    
    # 5. Test installation
    print("\n🧪 Testing installation...")
    
    test_imports = [
        ("import spacy; spacy.load('en_core_web_sm')", "spaCy with English model"),
        ("from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')", "SentenceTransformers"),
        ("import nltk; nltk.data.find('tokenizers/punkt')", "NLTK punkt"),
        ("import pandas, numpy, flask, pymongo", "Core packages")
    ]
    
    all_passed = True
    for test_code, description in test_imports:
        try:
            exec(test_code)
            print(f"✅ {description}")
        except Exception as e:
            print(f"❌ {description}: {e}")
            all_passed = False
    
    # 6. Summary
    print("\n📊 Setup Summary")
    print("=" * 50)
    
    if all_passed:
        print("🎉 SUCCESS! All dependencies installed and configured correctly.")
        print("\nPolicyCraft is ready to run with full functionality:")
        print("• Advanced NLP analysis with spaCy")
        print("• Semantic embeddings with SentenceTransformers")
        print("• Enhanced text processing with NLTK")
        print("• Advanced analysis engine enabled")
        print("\nYou can now start the application with:")
        print("  python app.py")
    else:
        print("⚠️  PARTIAL SUCCESS: Some components may not work correctly.")
        print("\nPlease review the errors above and install missing components manually.")
        print("See requirements.txt for detailed installation instructions.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()