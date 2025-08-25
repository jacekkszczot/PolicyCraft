#!/bin/bash
echo "PolicyCraft Development Setup"
echo "=============================="

# Create database directory structure (your security architecture)
mkdir -p PolicyCraft-Databases/{development,production,backups}
echo "✓ Database directories created"

# Setup virtual environment
cd PolicyCraft
python -m venv venv
source venv/bin/activate
echo "✓ Virtual environment created"

# Install dependencies
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Download required NLTK data
python -c "
import nltk
print('Downloading NLTK data...')
try:
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('✓ NLTK data downloaded')
except:
    print('⚠ NLTK download failed - will try during runtime')
"

# Copy environment template
cp .env.example .env
echo "✓ Environment file created"

# Create logs directory
mkdir -p logs
touch logs/.gitkeep
echo "✓ Logs directory created"

# Initialize empty SQLite database
python -c "
import os, sys
from flask import Flask
sys.path.insert(0, '.')
from config import get_config, create_secure_directories

app = Flask(__name__)
app.config.from_object(get_config())
create_secure_directories()

from flask_sqlalchemy import SQLAlchemy
with app.app_context():
    db = SQLAlchemy(app)
    db.create_all()
    print('✓ SQLite database structure created')
"

echo ""
echo "Setup complete! Next steps:"
echo "1. Configure .env file if needed"
echo "2. Start MongoDB: brew services start mongodb/brew/mongodb-community"
echo "3. Run: python app.py"
