# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB 6.0+
- Git
- pip (Python package manager)

### Quick Start (macOS/Linux)

1. **Clone the repository**
   
   For the main branch (stable version):
   ```bash
   git clone https://github.com/jacekkszczot/PolicyCraft.git
   cd PolicyCraft
   ```
   
   For the laboratory branch (development version):
   ```bash
   git clone -b laboratory https://github.com/jacekkszczot/PolicyCraft.git
   cd PolicyCraft
   ```
   
   Or switch to laboratory branch after cloning:
   ```bash
   git clone https://github.com/jacekkszczot/PolicyCraft.git
   cd PolicyCraft
   git checkout laboratory
   ```

2. **Set up Python environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   ```bash
   # Install MongoDB (macOS with Homebrew)
   brew tap mongodb/brew
   brew install mongodb-community
   
   # Start MongoDB service
   brew services start mongodb-community
   
   # Verify MongoDB is running
   mongosh --eval 'db.runCommand({ connectionStatus: 1 })'
   ```

4. **Configure the application**
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   
   # Generate a secure secret key
   python -c 'import secrets; print(f"SECRET_KEY={secrets.token_hex(32)}")' >> .env
   ```

5. **Initialize the database**
   ```bash
   # Create necessary database indexes and initial data
   python -c "from app import create_app; create_app().app_context().push(); from src.database.models import init_db; init_db()"
   ```

6. **Start the application**
   ```bash
   python app.py
   ```
   
   The application should now be running at http://localhost:5000

### Troubleshooting

#### MongoDB Connection Issues
If you see connection errors:

1. Check if MongoDB is running:
   ```bash
   brew services list | grep mongo
   ```

2. If not, start it manually:
   ```bash
   # Remove any lock files
   sudo rm -f /opt/homebrew/var/mongodb/mongod.lock
   sudo rm -f /opt/homebrew/var/mongodb/WiredTiger.lock
   
   # Start MongoDB
   mongod --config /opt/homebrew/etc/mongod.conf --fork --logpath /tmp/mongod.log
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
   - NLTK datasets:
     ```bash
     python - <<'PY'
     import nltk
     for pkg in ['wordnet','omw-1.4','punkt','stopwords','averaged_perceptron_tagger']:
         nltk.download(pkg, quiet=True)
     print('NLTK resources installed')
     PY
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

### Windows and Linux notes

- Windows: install MongoDB Community Server from the official installer or use Docker.
- Linux: use your package manager (e.g. `apt install mongodb-org`) or Docker.
- Docker alternative (any OS):
  ```bash
  docker run -d -p 27017:27017 --name mongo -v mongo_data:/data/db mongo:7
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

1. **Register Account**: Create user account for personalized analysis tracking
2. **Upload Policy**: Select AI policy document (PDF/DOCX/TXT format)
3. **View Analysis**: Review extracted themes, classification, and visualisations
4. **Generate Recommendations**: Access detailed, academic-grade improvement suggestions
5. **Export Results**: Download analysis results in multiple formats

### Batch Analysis

For institutions analyzing multiple policies:

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
- Username: `admin`

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
MSc Data Science & AI Student  
Leeds Trinity University  
Email: jacek.kszczot@icloud.com  
Project Repository: [[GitHub URL](https://github.com/jacekkszczot/PolicyCraft.git)]