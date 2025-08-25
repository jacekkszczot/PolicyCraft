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

# Set default admin credentials
DEFAULT_ADMIN_EMAIL="admin@policycraft.ai"
DEFAULT_ADMIN_PASSWORD="admin1"

# Copy environment template
cp .env.example .env

# Add default admin credentials to .env
echo "\n# Default admin credentials" >> .env
echo "DEFAULT_ADMIN_EMAIL=$DEFAULT_ADMIN_EMAIL" >> .env
echo "DEFAULT_ADMIN_PASSWORD=$DEFAULT_ADMIN_PASSWORD" >> .env
echo "✓ Environment file created with default admin credentials"

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
from src.database.models import User, db as models_db

# Initialize the database
with app.app_context():
    # Initialize SQLAlchemy
    db = SQLAlchemy(app)
    
    # Create all tables
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@policycraft.ai').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@policycraft.ai',
            password='admin1',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✓ Admin user created with username: admin, password: admin1')
    
    print('✓ Database initialization complete')
"

echo ""
echo ""
echo "========================================"
echo "🚀 Setup complete!"
echo ""
echo "Admin access:"
echo "- Email: admin@policycraft.ai"
echo "- Password: admin1"
echo ""
echo "Next steps:"
echo "1. Start MongoDB: brew services start mongodb/brew/mongodb-community"
echo "2. Run the application: python app.py"
echo "3. Access the admin panel at: http://localhost:5000/admin"
echo "4. Change the default admin password after first login"
echo ""
echo "⚠️  SECURITY WARNING: Change the default admin password immediately!"
echo "========================================"
