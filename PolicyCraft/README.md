# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## Getting Started

### Quick start: full functionality (macOS/Windows/Linux)

The steps below get you from a fresh clone to a fully working application with all features enabled, including MongoDB, NLP resources, and tests.

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows PowerShell:  .\venv\Scripts\Activate.ps1
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start MongoDB**
   ```bash
   # macOS (Homebrew)
   brew tap mongodb/brew
   brew install mongodb-community
   brew services start mongodb-community
   ```
   If you previously had MongoDB 7.x installed on macOS, you may need to relink:
   ```bash
   brew unlink mongodb-community@7.0 && brew link --overwrite mongodb-community
   brew services start mongodb-community
   ```
   Windows/Linux alternatives:
   - Windows: install the "MongoDB Community Server" using the official installer (mongodb.com/try/download/community) and start the "MongoDB" service.
   - Linux: use your package manager (e.g. `sudo apt install mongodb-org`) or Docker (see below).

4. **Create a .env file (copy from example; loaded automatically)**
   Quick way:
   ```bash
   cp .env.example .env
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
6. - **Create required directories**  
  Before the first run, make sure the following directories exist (otherwise you may see `FileNotFoundError: logs/application.log`):  

  ```bash
  mkdir -p PolicyCraft/logs PolicyCraft/data/processed PolicyCraft/data/policies/pdf_originals

7. **Run the app**
   ```bash
   python app.py
   ```
   The site will be available at: `http://localhost:5001`.

8. **Run the tests (optional but recommended)**
   ```bash
   python -m pytest -q
   ```

### Configuration and first run

* __Automatic configuration fallback__
  - If `PolicyCraft/config.py` is not present, the application will automatically fall back to `PolicyCraft/config.example.py` at start‑up and print a warning in the console.
  - To provide local, machine‑specific settings (recommended), create your own config file based on the example:
    ```bash
    cp PolicyCraft/config.example.py PolicyCraft/config.py
    ```
    Then adjust values such as `DEFAULT_ADMIN_PASSWORD` and any database or integration parameters. Keep `config.py` out of version control.

* __Environment variables__
  - The app loads environment variables from `.env` automatically if present. You can copy the sample file and amend as needed:
    ```bash
    cp .env.example .env
    ```

* __First run on a new machine__
  1. Create and activate a virtual environment
  2. `pip install -r requirements.txt`
  3. Ensure MongoDB is installed and running (or use Docker)
  4. Optionally create `.env` from `.env.example`
  5. Optionally create `PolicyCraft/config.py` from `PolicyCraft/config.example.py`
  6. Start the application: `python app.py`

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
