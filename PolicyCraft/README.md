# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

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
- [Development](#development)
- [Testing](#testing)
- [Documentation](#documentation)

## System Requirements

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended for Windows)
- **Python**: 3.8 or higher (with venv module)
- **MongoDB**: 6.0 or higher (see installation instructions below)
- **Git**: Latest stable version

## Quick Start (Automatic Setup)

For most users, we recommend using the automated setup script. The script will:
1. Create a Python virtual environment (requires Python 3.8+ to be pre-installed)
2. Install all required Python dependencies
3. Set up the database
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

### Running the Setup Script

```bash
# 1. Clone the repository
git clone -b laboratory https://github.com/jacekkszczot/PolicyCraft.git
cd PolicyCraft

# 2. Make the setup script executable and run it
chmod +x setup_new_dev.sh
./setup_new_dev.sh

# The script will automatically create and activate a virtual environment
# and install all required dependencies
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

#### macOS (using Homebrew)
```bash
# Install MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community
```

#### Ubuntu/Debian
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

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
pgrep -l mongod

# Check MongoDB logs
tail -f ~/mongodb_logs/mongod.log

# If MongoDB fails to start, try removing lock files
rm -f ~/mongodb_data/mongod.lock
rm -f ~/mongodb_data/WiredTiger.lock
```

### Python Dependencies

```bash
# Ensure pip is up to date
pip install --upgrade pip setuptools wheel

# Reinstall requirements
pip install -r requirements.txt
```

## Configuration

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

### Troubleshooting

#### MongoDB Connection Issues
If you see connection errors:

1. Check if MongoDB is running:
   ```bash
   # On macOS with Homebrew
   brew services list | grep mongo
   
   # On Linux with systemd
   # sudo systemctl status mongod
   ```

2. If not, start it manually:
   ```bash
   # On macOS with Homebrew
   brew services start mongodb-community
   
   # On Linux with systemd
   # sudo systemctl start mongod
   
   # If you encounter lock files:
   # macOS: sudo rm -f /opt/homebrew/var/mongodb/mongod.lock
   # Linux: sudo rm -f /var/lib/mongodb/mongod.lock
   ```

#### Python Dependencies
If you encounter dependency issues:
```bash
# Ensure pip is up to date
pip install --upgrade pip setuptools wheel

# Reinstall requirements
pip install -r requirements.txt
```
   Then adjust the values in `PolicyCraft/.env` (example below):
   ```env
   HOST=localhost
   PORT=5001
   FLASK_ENV=development
   FEATURE_ADVANCED_ENGINE=1
   ANALYSIS_MODE=student_centric
   SECRET_KEY=change_me_to_a_long_random_value
   MONGODB_URI=mongodb://localhost:27017/policycraft
   ```
   Notes:
   - The application loads `.env` on start; no extra steps needed.
   - Generate a strong key, for example: `python -c "import secrets; print(secrets.token_hex(32))"`.

5. **Download required NLP resources**
   - spaCy English model:
     ```bash
     python -m spacy download en_core_web_sm
     ```
   - NLTK datasets (run in Python shell):
     ```bash
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
     
     Or alternatively, download them one by one:
     ```bash
     python -m nltk.downloader wordnet omw-1.4 punkt stopwords averaged_perceptron_tagger
     ```

6. **Run the app**
   ```bash
   python app.py
   ```
   The site will be available at: `http://localhost:5001`.

7. **Run the tests (optional but recommended)**
   ```bash
   python -m pytest -q
   ```
   Or from the repository root, you can use the helper script:
   ```bash
   python run_tests.py
   ```

### Configuration and first run

* __Configuration file (included)__
  - The repository now includes `PolicyCraft/config.py` with a safe development default: SQLite database at `PolicyCraft-Databases/development/policycraft_dev.db`.
  - The app will still fall back to `PolicyCraft/config.example.py` only if `PolicyCraft/config.py` is missing.
  - Do not place secrets in `PolicyCraft/config.py`. For production, override via environment variables (e.g. `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`).
  - You can override the DB with an env var, e.g.:
    ```bash
    export SQLALCHEMY_DATABASE_URI="postgresql://user:pass@host:5432/dbname"
    ```

* __Environment variables__
  - The app loads environment variables from `.env` automatically if present. You can copy the sample file and amend as needed:
  ```bash
  cp .env.example .env
  ```

* __First run on a new machine__
  1. Create and activate a virtual environment
  2. `pip install -r requirements.txt`
  3. Ensure MongoDB is installed and running (or use Docker) for features that use MongoDB.
  4. Optionally create `.env` from `.env.example`
  5. Start the application: `python app.py` (SQLite DB file and required folders are created automatically)

### Troubleshooting

- **Port 5001 already in use**
  ```bash
  lsof -n -P -iTCP:5001 -sTCP:LISTEN   # find the PID
  kill <PID>
  # or start on a different port
  PORT=5002 python app.py
  ```

- **Static image exports with Plotly/Kaleido**
  If you need `fig.write_image()` ensure compatible versions (e.g. Plotly ≥ 6.1.1 or Kaleido 0.2.1). Adjust in `requirements.txt` if necessary.

- **MongoDB connection**
  Confirm the service is running and the URI matches your `.env`:
  `brew services list` and `MONGODB_URI=mongodb://localhost:27017/policycraft`.

### Verifying MongoDB Installation

After installation, verify MongoDB is running:

```bash
mongod --version
mongo --version
```

To check if the MongoDB service is running:

```bash
# On macOS
brew services list | grep mongo

# On Linux
sudo systemctl status mongod

# On Windows
Get-Service -Name MongoDB
  ```

#### Windows command equivalents

- Virtual environment activation
  - PowerShell: `./venv/Scripts/Activate.ps1`
  - CMD: `venv\Scripts\activate.bat`
  - Git Bash: `source venv/Scripts/activate`

- Environment variables (current session)
  - PowerShell: `$env:PORT=5002; $env:HOST="localhost"`
  - CMD: `set PORT=5002 && set HOST=localhost`
  - Bash (WSL/Git Bash): `export PORT=5002; export HOST=localhost`

- Unset variable
  - PowerShell: `Remove-Item Env:PORT`
  - CMD: `set PORT=`
  - Bash: `unset PORT`

- Run on a custom port
  - PowerShell: `$env:PORT=5002; python app.py`
  - CMD: `set PORT=5002 && python app.py`
  - Bash: `PORT=5002 python app.py`

- Make variable persistent (user)
  - PowerShell/CMD: `setx PORT 5002`  (takes effect in new terminals)


## Usage Guide

### Getting Started

1. **Register Account**: Create user account for personalised analysis tracking
2. **Upload Policy**: Select AI policy document (PDF/DOCX/TXT format)
3. **View Analysis**: Review extracted themes, classification, and visualisations
4. **Generate Recommendations**: Access detailed, academic-grade improvement suggestions
5. **Export Results**: Download analysis results in multiple formats

### Batch Analysis

For institutions analysing multiple policies:

1. Navigate to Upload page
2. Select multiple files (up to 10 simultaneously)
3. System automatically processes all documents
4. View comparative dashboard with aggregated insights
5. Export comprehensive batch report

### Dashboard Features

- **Recent Analyses**: Quick access to previously processed policies
- **Comparative Charts**: Visual comparison across multiple documents
- **Statistical Overview**: Key metrics and trends
- **Recommendation Tracking**: Monitor implementation progress

## Administrator guide

### Create the first admin

The app can auto‑create a default admin user if an admin password is provided at initialisation (`src/database/models.py::init_db()`):

- Email: `admin@policycraft.ai`
- Username: `admin1`

Option A — one‑off initialisation command:

```bash
python - <<'PY'
from src.database.models import init_db
from app import create_app
app = create_app()
app.config['DEFAULT_ADMIN_PASSWORD'] = 'change_me_now'  # set a strong password
init_db(app)
print('Default admin initialised: admin@policycraft.ai')
PY
```

Option B — via configuration (before first run): add `DEFAULT_ADMIN_PASSWORD` to your `config.py` or environment, then start the app; `init_db()` will create the admin automatically.

### Promote an existing user to admin

```bash
python - <<'PY'
from app import create_app
from src.database.models import db, User
app = create_app()
with app.app_context():
    u = User.query.filter_by(email='user@example.com').first()
    if not u:
        raise SystemExit('User not found')
    u.role = 'admin'
    db.session.commit()
    print(f"Promoted {u.email} to admin")
PY
```

### Accessing the Admin area

- Sign in from the home page (index) as normal. If your account has the `admin` role, the admin dashboard will be available.
- Admin routes are protected by `admin_required` (`src/admin/routes.py::admin_required`); you can also navigate directly to `/admin` if you have permissions.

### Admin tools (overview)

- User management: list users, reset passwords, delete non‑admin users (`/admin/users`).
- Baselines and recommendations maintenance: reset global baselines and recommendations.
- Literature management: upload, review, clean up knowledge base documents.

Security notes:

- Change the default admin password immediately after creation.
- Admin accounts cannot be deleted via the UI.

## Smoke test (manual)

Use this brief sequence to confirm a fresh install works end‑to‑end without running unit tests:

1. Ensure MongoDB is running (e.g. `brew services list` → `mongodb-community` started, or Docker container healthy).
2. Activate your virtual environment and start the app:
   ```bash
   source venv/bin/activate
   python app.py
   ```
   Visit `http://localhost:5001`.
3. Register a user and sign in.
4. Upload a small policy file (PDF/DOCX/TXT). Wait for processing to complete.
5. Verify you see extracted themes, classification, and charts without errors.
6. Open the Recommendations view and confirm items render.
7. Export results (e.g. CSV or PDF if enabled) and verify the file downloads and opens.

## Further reading

For system internals, methodology, and validation details, see the architecture notes in `docs/architecture.md`.

## Quality assurance

The project includes a comprehensive test suite and follows robust engineering practices. For high‑level system architecture and essential development commands, see `docs/architecture.md`.

## Technical implementation

A concise overview of pipelines, engines, and security features is available in `docs/architecture.md`.

## Development

### Project Structure

```
PolicyCraft/
├── app.py
├── config.py
├── requirements.txt
├── clean_dataset.py
├── batch_analysis.py
├── src/
│   ├── auth/
│   ├── nlp/
│   ├── recommendation/
│   ├── database/
│   ├── visualisation/
│   └── web/
├── data/
│   ├── policies/
│   ├── processed/
│   └── results/
└── tests/
```

## Academic foundation

See academic and ethical context in `docs/architecture.md`.

## Future development

Roadmap highlights are maintained outside this README to keep it concise.

## License

This project is licensed under the MIT License. See LICENSE file for details.

 

## Further Documentation

- [Architecture diagram](docs/architecture.md)
- [Ethical considerations](docs/ethics.md)
- [WCAG compliance checklist](docs/wcag_checklist.md)
- [Security policy](SECURITY.md)

## Contact

**Jacek Robert Kszczot**  
MSc Data Science & AI   
Leeds Trinity University  
Email: jacek.kszczot@icloud.com  
Project Repository: [[GitHub URL](https://github.com/jacekkszczot/PolicyCraft.git)]