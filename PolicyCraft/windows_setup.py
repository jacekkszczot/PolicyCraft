#!/usr/bin/env python3
# Windows Setup Script for PolicyCraft
# This script automates the setup process on Windows using WSL2

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Command output: {e.stderr}")
        sys.exit(1)

def check_wsl():
    """Check if WSL is installed and running."""
    try:
        # Check WSL version
        wsl_version = run_command("wsl -l -v")
        if "VERSION" not in wsl_version:
            print("WSL is not properly installed or running.")
            print("Please enable WSL2 first by following the WINDOWS_INSTALL.md guide.")
            sys.exit(1)
        print("✓ WSL is installed and running")
        return True
    except Exception as e:
        print(f"Error checking WSL: {e}")
        return False

def check_python():
    """Check if Python is installed and accessible from WSL."""
    try:
        python_version = run_command("python3 --version")
        print(f"✓ Found {python_version}")
        return True
    except:
        print("Python 3 is not installed or not in PATH.")
        print("Please install Python 3.8 or later and ensure it's in your PATH.")
        return False

def setup_venv():
    """Set up a Python virtual environment."""
    if not os.path.exists("venv"):
        print("Creating Python virtual environment...")
        run_command("python3 -m venv venv")
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")

    # Activate venv and upgrade pip
    if os.name == 'nt':  # Windows
        activate_cmd = ".\\venv\\Scripts\\activate.bat && python -m pip install --upgrade pip"
    else:  # Unix/Linux/WSL
        activate_cmd = "source venv/bin/activate && python -m pip install --upgrade pip"
    
    run_command(activate_cmd)
    print("✓ Pip upgraded")

def install_dependencies():
    """Install required Python packages."""
    print("Installing Python dependencies for Windows...")
    run_command("pip install -r requirements_windows.txt")
    
    # Install spacy model in a way that works on Windows
    print("Downloading language model...")
    run_command("python -m spacy download en_core_web_sm")
    
    print("✓ Dependencies installed")
    print("Note: If you encounter any issues with python-magic, you may need to install the Windows binary manually.")

def setup_mongodb():
    """Check MongoDB installation and start the service."""
    print("Checking MongoDB...")
    try:
        # Check if MongoDB is installed
        run_command("mongod --version")
        print("✓ MongoDB is installed")
        
        # Start MongoDB service
        print("Starting MongoDB service...")
        run_command("sudo service mongod start")
        print("✓ MongoDB service started")
        return True
    except:
        print("MongoDB is not installed or not in PATH.")
        print("Please install MongoDB Community Edition and add it to your PATH.")
        return False

def setup_database():
    """Initialize the database and create admin user."""
    print("Setting up database...")
    try:
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Initialize database
        run_command("python -c """
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created')
""")
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

def main():
    print("""
========================================
  PolicyCraft Windows Setup Assistant
========================================
""")
    
    # Check system requirements
    print("\n[1/5] Checking system requirements...")
    if not check_wsl() or not check_python():
        print("\nPlease fix the above issues and try again.")
        sys.exit(1)
    
    # Setup virtual environment
    print("\n[2/5] Setting up Python virtual environment...")
    setup_venv()
    
    # Install dependencies
    print("\n[3/5] Installing dependencies...")
    install_dependencies()
    
    # Setup MongoDB
    print("\n[4/5] Configuring MongoDB...")
    if not setup_mongodb():
        print("Skipping MongoDB setup. You'll need to install it manually.")
    
    # Initialize database
    print("\n[5/5] Initializing database...")
    if not setup_database():
        print("There were issues initializing the database.")
    
    print("""
========================================
  Setup Complete!
========================================

To start the application, run:

  python app.py

Then open your browser to:
  http://localhost:5001

Default login:
  Email: admin@policycraft.ai
  Password: admin1

For troubleshooting, see WINDOWS_INSTALL.md
""")

if __name__ == "__main__":
    main()
