# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## Live Application

**PolicyCraft is accessible online at:** [https://policycraft.jaai.co.uk](https://policycraft.jaai.co.uk)

The application has been successfully deployed and is available for use.

## Copyright and Legal Protection

**This work is protected under international copyright law and academic integrity policies.**

- **Copyright (c) 2025 Jacek Kszczot (jacekkszczot)**
- **All Rights Reserved**
- **Academic submission for Leeds Trinity University, Module COM7016**

See [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md) for detailed legal information and usage restrictions.

## Table of Contents
- [System Requirements](#system-requirements)
- [Quick Start (Automatic Setup)](#quick-start-automatic-setup)
- [Manual Installation Guide](#manual-installation-guide)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

## System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended for Windows)
- **Python**: 3.8 or higher (with venv module)
- **Database**: 
  - **SQLite** (SQLAlchemy) - for user authentication, accounts, and basic data
  - **MongoDB** (required) - for policy analyses, recommendations, literature management, and knowledge base
- **Git**: Latest stable version
- **Docker** (optional) - for easy MongoDB setup

**Note:** The application uses **two databases simultaneously**:
- **SQLite** handles user accounts, authentication, and basic application data
- **MongoDB** stores policy analyses, recommendations, literature, and knowledge base data

Both databases are required for the application to function properly.

## Quick Start (Automatic Setup)

**For most users, we recommend using the automated setup script.**

### Step 1: Download the Application

First, you need to download the application from GitHub:

**Important folder placement:**
- **macOS**: Place the folder outside of iCloud Drive, preferably directly on your main disk (e.g., `/Users/yourusername/Projects/PolicyCraft`)
- **Windows/Linux**: Place in any convenient location

```bash
# Clone the main branch 
git clone https://github.com/jacekkszczot/PolicyCraft.git
cd PolicyCraft
```

### Step 2: Open Terminal in Application Folder

Ensure your terminal is opened in the folder containing the application files:
- You should see files like `app.py`, `README.md`, `config.py`, and `setup_new_dev.sh`
- Verify with: `ls` (macOS/Linux) or `dir` (Windows)

### Step 3: Run the Automated Setup

The script will automatically:
1. Create a Python virtual environment (requires Python 3.8+ to be pre-installed)
2. Install all required Python dependencies
3. Set up both databases (SQLite and MongoDB)
4. Configure all environment variables automatically
5. Start MongoDB (local or Docker)
6. Create an admin account
7. Test the application

**One-command setup:**
```bash
chmod +x setup_new_dev.sh
./setup_new_dev.sh
```

**Note:** During setup, MongoDB may prompt you for a password. Enter a secure password of your choice when requested.

**After setup, run:**
```bash
python app.py
```

**Access:** http://localhost:5001
**Login credentials:** 
login: admin or admin@policycraft.ai 
password: admin1


## Manual Installation Guide

### 1. Clone the Repository

**Important folder placement:**
- **macOS**: Place the folder outside of iCloud Drive, preferably directly on your main disk (e.g., `/Users/yourusername/Projects/PolicyCraft`)
- **Windows/Linux**: Place in any convenient location

```bash
git clone https://github.com/jacekkszczot/PolicyCraft.git
cd PolicyCraft
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install MongoDB

**Note**: MongoDB is **required** for the application to function. It stores policy analyses, recommendations, literature, and knowledge base data.

#### macOS (using Homebrew)
```bash
# Install MongoDB
brew install mongodb/brew/mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

#### Linux (Ubuntu/Debian)
```bash
# Import the public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Create list file for MongoDB
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -sc)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org/6.0.list

# Update packages and install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Windows
1. Download the installer from [MongoDB Download Centre](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. MongoDB will be installed as a Windows Service and started automatically

#### (Optional, but especially recommended for Mac users) Using Docker (works on all platforms)
```bash
docker run -d -p 27017:27017 --name mongo -v mongo_data:/data/db mongo:7
```

### 4. Install NLP Dependencies

```bash
# Install spaCy English model
python -m spacy download en_core_web_sm

# Download NLTK datasets
python -c "
import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
print('NLTK resources installed')
"
```

### 5. Configure Application

```bash
# Copy example environment file (includes all required variables)
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env

# Edit the .env file to configure your settings
# nano .env  # or use your preferred text editor
```

### 6. Initialise Database

```bash
# Create database tables and indexes
python -c "
from app import create_app
from src.database.models import init_db
app = create_app()
with app.app_context():
    init_db()
"
```

### 7. Start the Application

```bash
# Run the Flask development server
python app.py
```

You'll find the application running at: [http://localhost:5001](http://localhost:5001)

## Troubleshooting

### Quick Fix

**If you're experiencing issues during manual setup, try the automated setup script first:**
```bash
./setup_new_dev.sh
```

This will automatically resolve most common configuration issues.

### Login Issues

If you cannot log in with the default admin credentials:

1. **Check MongoDB status:**
   ```bash
   brew services list | grep mongodb
   ```

2. **Reset admin password:**
   ```bash
   python reset_admin_password.py
   ```

3. **Re-run automated setup (RECOMMENDED):**
   ```bash
   ./setup_new_dev.sh
   ```

### Common Issues

**Most issues can be resolved automatically by running:**
```bash
./setup_new_dev.sh
```

**Manual fixes:**
- **MongoDB not running**: Start with `brew services start mongodb/brew/mongodb-community`
- **Database errors**: Remove old database files and re-run setup
- **Import errors**: Make sure virtual environment is activated
- **Port conflicts**: Application runs on port 5001
- **Environment variables missing**: Run setup script to auto-configure `.env`

### MongoDB Issues

**MongoDB service error:**
```bash
# Check MongoDB status
brew services list | grep mongodb

# Stop and restart MongoDB
brew services stop mongodb/brew/mongodb-community
brew services start mongodb/brew/mongodb-community
```

**Apple Silicon (M1/M2) specific:**
```bash
# MongoDB is installed in /opt/homebrew/ on Apple Silicon
which mongod
# Should show: /opt/homebrew/bin/mongod

# Create directories manually if needed
sudo mkdir -p /opt/homebrew/var/log/mongodb
sudo mkdir -p /opt/homebrew/var/mongodb
sudo chown -R $(whoami) /opt/homebrew/var/log/mongodb
sudo chown -R $(whoami) /opt/homebrew/var/mongodb

# Start MongoDB manually
mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log --fork
```

**or use Docker (easier):**
```bash
docker run -d -p 27017:27017 --name mongodb-policycraft mongo:latest
```

## Documentation

- [Architecture](docs/architecture.md)
- [Ethics](docs/ethics.md)
- [Model Card](docs/model_card.md)
- [WCAG Checklist](docs/wcag_checklist.md)
