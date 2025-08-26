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
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up Python Environment](#2-set-up-python-environment)
  - [3. Install MongoDB](#3-install-mongodb)
  - [4. Configure MongoDB](#4-configure-mongodb)
  - [5. Install NLP Dependencies](#5-install-nlp-dependencies)
  - [6. Configure Application](#6-configure-application)
  - [7. Initialize Database](#7-initialize-database)
  - [8. Start the Application](#8-start-the-application)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
  - [Configuration and first run](#configuration-and-first-run)
  - [Environment Variables](#environment-variables)
- [Development](#development)
- [Testing](#testing)
- [Documentation](#documentation)

## System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended for Windows)
- **Python**: 3.8 or higher (with venv module)
- **Database**: 
  - **SQLite** (SQLAlchemy) - for user authentication, accounts, and basic data
  - **MongoDB** (required) - for policy analyses, recommendations, literature management, and knowledge base
- **Git**: Latest stable version

**Note**: The application uses **two databases simultaneously**:
- **SQLite** handles user accounts, authentication, and basic application data
- **MongoDB** stores policy analyses, recommendations, literature, and knowledge base data

Both databases are required for the application to function properly.

## Quick Start (Automatic Setup)

For most users, we recommend using the automated setup script. The script will:
1. Create a Python virtual environment (requires Python 3.8+ to be pre-installed)
2. Install all required Python dependencies
3. Set up both databases (SQLite and MongoDB)
4. Create an admin account



### Before You Begin

Ensure you have completed all prerequisites above, then verify the venv module is available:

```bash
# On Debian/Ubuntu
sudo apt-get install python3-venv

# On RHEL/CentOS
sudo yum install python3-venv

# On macOS (if not already installed with Python)
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip

# On Windows (usually included with Python installation)
python -m ensurepip --upgrade
```

### Setting Up the Development Environment

1. **Clone the repository**
   ```bash
   git clone -b laboratory https://github.com/jacekkszczot/PolicyCraft.git
   cd PolicyCraft
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows Command Prompt:
   # venv\Scripts\activate.bat
   # On Windows PowerShell:
   # .\venv\Scripts\Activate.ps1
   
   # You should see (venv) in your command prompt
   ```

3. **Run the setup script**
   ```bash
   # Make the script executable (Linux/macOS)
   chmod +x setup_new_dev.sh
   
   # Run the setup script
   ./setup_new_dev.sh
   ```

### Default Admin Account

After running the setup script, you can log in with the following credentials:

- **Email:** `admin@policycraft.ai`
- **Password:** `admin1`

**Important:** For security reasons, please change the default password after your first login.

### Start the Application

1. **Activate the virtual environment** (required every time you open a new terminal):
   ```bash
   # Navigate to the project directory if you're not already there
   cd PolicyCraft

   # Activate the virtual environment
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows (Command Prompt)
   # venv\Scripts\activate.bat
   
   # On Windows (PowerShell)
   # .\venv\Scripts\Activate.ps1
   
   # You should see (venv) at the beginning of your command prompt
   # indicating the virtual environment is active
   ```

2. Start MongoDB (if not already running):
   ```bash
   # On macOS with Homebrew
   brew services start mongodb-community
   
   # On Linux with systemd
   # sudo systemctl start mongod
   ```

3. Start the application:
   ```bash
   cd PolicyCraft
   python app.py
   ```

3. Open your browser and go to: http://localhost:5001

## Manual Installation Guide

Follow these steps if you prefer manual setup or need custom configuration:

### 1. Clone the Repository

#### Stable Version (Main Branch)
```bash
git clone https://github.com/jacekkszczot/PolicyCraft.git
cd PolicyCraft
```

#### Development Version (Laboratory Branch)
```bash
git clone -b laboratory https://github.com/jacekkszczot/PolicyCraft.git
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

**For Apple Silicon (M1/M2):**
```bash
# Install MongoDB
brew install mongodb/brew/mongodb-community

# Create required directories
sudo mkdir -p /opt/homebrew/var/log/mongodb
sudo mkdir -p /opt/homebrew/var/mongodb
sudo chown -R $(whoami) /opt/homebrew/var/log/mongodb
sudo chown -R $(whoami) /opt/homebrew/var/mongodb

# Start MongoDB
mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log --fork
```

**For Intel Mac:**
```bash
# Install MongoDB
brew install mongodb/brew/mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

**Alternative - Manual start:**
```bash
# Start MongoDB manually
mongod --config /usr/local/etc/mongod.conf
```

#### Linux (Ubuntu/Debian)
```bash
# Import the public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Create list file for MongoDB
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -sc)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update packages and install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Windows
1. Download the installer from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. MongoDB will be installed as a Windows Service and started automatically

#### Using Docker (all platforms)
```bash
docker run -d -p 27017:27017 --name mongo -v mongo_data:/data/db mongo:7
```

### 4. Configure MongoDB

#### Automated Setup (Recommended)
```bash
# Make the setup script executable and run it
chmod +x setup_mongodb.sh
./setup_mongodb.sh

# Start MongoDB with the new configuration
~/start_mongodb.sh
```

#### Manual Setup
```bash
# Create data and log directories
mkdir -p ~/mongodb_data ~/mongodb_logs

# Start MongoDB with custom data directory
mongod --dbpath ~/mongodb_data --logpath ~/mongodb_logs/mongod.log --fork

# Verify MongoDB is running
mongosh --eval 'db.runCommand({ connectionStatus: 1 })'
```

### 5. Install NLP Dependencies

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

## 5A. Troubleshooting NLTK Installation

If you see warnings such as:
WARNING: NLTK resource missing: wordnet
WARNING: NLTK resource missing: punkt
WARNING: NLTK resource missing: stopwords
WARNING: NLTK resource missing: averaged_perceptron_tagger


…it means the application cannot find the required NLTK datasets.  
This sometimes happens when `nltk.download()` fails due to network restrictions or permissions.  

Follow these steps to install the resources manually:  

---

### 1. Open a terminal and go to your application’s folder
```bash
cd path/to/your/application

### Create a new shell script:
nano install_nltk_resources.sh

### Paste the following content into the file:

!/bin/bash
set -e

# Base directory for NLTK data
NLTK_DIR="$HOME/nltk_data"
CORPORA_DIR="$NLTK_DIR/corpora"
TAGGERS_DIR="$NLTK_DIR/taggers"
TOKENIZERS_DIR="$NLTK_DIR/tokenizers"

echo "Creating directories..."
mkdir -p "$CORPORA_DIR" "$TAGGERS_DIR" "$TOKENIZERS_DIR"

# URLs of NLTK packages
WORDNET_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip"
STOPWORDS_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip"
TAGGER_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger.zip"
PUNKT_URL="https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip"

# Download resources
echo "Downloading WordNet..."
curl -L -o /tmp/wordnet.zip "$WORDNET_URL"

echo "Downloading Stopwords..."
curl -L -o /tmp/stopwords.zip "$STOPWORDS_URL"

echo "Downloading Averaged Perceptron Tagger..."
curl -L -o /tmp/averaged_perceptron_tagger.zip "$TAGGER_URL"

echo "Downloading Punkt..."
curl -L -o /tmp/punkt.zip "$PUNKT_URL"

# Unpack into the correct folders
echo "Unpacking WordNet..."
unzip -o /tmp/wordnet.zip -d "$CORPORA_DIR"

echo "Unpacking Stopwords..."
unzip -o /tmp/stopwords.zip -d "$CORPORA_DIR"

echo "Unpacking Averaged Perceptron Tagger..."
unzip -o /tmp/averaged_perceptron_tagger.zip -d "$TAGGERS_DIR"

echo "Unpacking Punkt..."
unzip -o /tmp/punkt.zip -d "$TOKENIZERS_DIR"

echo "✓ NLTK resources installed in $NLTK_DIR"
echo "If your application still cannot find them, run:"
echo "   export NLTK_DATA=\"$NLTK_DIR\""

### 3. Make the script executable
chmod +x install_nltk_resources.sh

###4. Run the script
./install_nltk_resources.sh


### 6. Configure Application

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env

# Edit the .env file to configure your settings
# nano .env  # or use your preferred text editor
```

### 7. Initialise Database

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

### 8. Start the Application

```bash
# Run the Flask development server
python app.py
```

The application will be available at: [http://localhost:5001](http://localhost:5001)

## Troubleshooting

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

3. **Re-run setup:**
   ```bash
   ./setup_new_dev.sh
   ```

4. **Check database:**
   ```bash
   python -c "
   from src.database.models import User, db
   from app import create_app
   app = create_app()
   with app.app_context():
       admin = User.query.filter_by(email='admin@policycraft.ai').first()
       if admin:
           print(f'Admin exists: {admin.username}, role: {admin.role}')
       else:
           print('Admin user not found')
   "
   ```

### Common Issues

- **MongoDB not running**: Start with `brew services start mongodb/brew/mongodb-community`
- **Database errors**: Remove old database files and re-run setup
- **Import errors**: Make sure virtual environment is activated
- **Port conflicts**: Application runs on port 5001, not 5000

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

**Check MongoDB logs:**
```bash
# Apple Silicon
tail -f /opt/homebrew/var/log/mongodb/mongo.log

# Intel Mac
tail -f /usr/local/var/log/mongodb/mongo.log
```

## Configuration

### Configuration and first run

* __Configuration file (included)__
  - The repository now includes `PolicyCraft/config.py` with a safe development default: **SQLite database** at `PolicyCraft-Databases/development/policycraft_dev.db`.
  - The app will still fall back to `PolicyCraft/config.example.py` only if `PolicyCraft/config.py` is missing.
  - **SQLite handles user accounts and basic data** - automatically created
  - **MongoDB is required** - stores policy analyses, recommendations, literature, and knowledge base
  - Do not place secrets in `PolicyCraft/config.py`. For production, override via environment variables (e.g. `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`).
  - You can override the DB with an env var, e.g.:
    ```bash
    export SQLALCHEMY_DATABASE_URI="postgresql://user:pass@host:5432/dbname"
    ```

* __Database Architecture__
  - **SQLite (SQLAlchemy)**: File-based database for user accounts, authentication, and basic application data
  - **MongoDB**: Document database for policy analyses, recommendations, literature management, and knowledge base
  - **Both databases are required** - the application cannot function without either one

* __Environment variables__
  - The app loads environment variables from `.env` automatically if present. You can copy the sample file and amend as needed:
  ```bash
  cp .env.example .env
  ```

* __First run on a new machine__
  1. Create and activate a virtual environment
  2. `pip install -r requirements.txt`
  3. **Install and configure MongoDB** (required for application functionality)
  4. Optionally create `.env` from `.env.example`
  5. Start the application: `python app.py` (SQLite DB file and required folders are created automatically)

### Environment Variables

Edit the `.env` file to configure:

```env
# Application
HOST=localhost
PORT=5001
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
MONGODB_URI=mongodb://localhost:27017/policycraft

# Optional: Email settings
# MAIL_SERVER=smtp.example.com
# MAIL_PORT=587
# MAIL_USE_TLS=true
# MAIL_USERNAME=your-email@example.com
# MAIL_PASSWORD=your-email-password
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_module.py

# Run with coverage report
coverage run -m pytest
coverage report -m
```

### Code Style

```bash
# Run linter
flake8 .

# Auto-format code
black .

# Sort imports
isort .
```

## Documentation

- [API Documentation](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting Guide](docs/troubleshooting_guide.md)
- [User Manual](docs/user_manual.md)
- [Model Card](docs/model_card.md)