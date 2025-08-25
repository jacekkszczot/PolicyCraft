#!/bin/bash
echo "PolicyCraft Development Setup"
echo "=============================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script's directory
cd "$SCRIPT_DIR"

# Create database directory structure (your security architecture)
mkdir -p PolicyCraft-Databases/{development,production,backups}
echo "✓ Database directories created"

# Setup virtual environment
echo "Setting up Python virtual environment..."

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
python -m venv venv

# Activate the virtual environment
if [ "$OSTYPE" = "msys" ] || [ "$OSTYPE" = "cygwin" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS
    source venv/bin/activate
fi

echo "✓ Virtual environment created and activated"
echo "Python path: $(which python)"

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
from werkzeug.security import generate_password_hash

sys.path.insert(0, '.')
from config import get_config, create_secure_directories

# First, create and configure the Flask application
app = Flask(__name__)
app.config.from_object(get_config())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/policycraft.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEFAULT_ADMIN_EMAIL'] = 'admin@policycraft.ai'
app.config['DEFAULT_ADMIN_PASSWORD'] = 'admin1'

create_secure_directories()

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

# Initialise SQLAlchemy with the application
from src.database.models import db, User, init_db

db.init_app(app)

# Create all tables and set up admin user
with app.app_context():
    # Initialize database and create tables
    db_initialized = False
    try:
        # Try to create tables
        db.create_all()
        db_initialized = True
    except Exception as e:
        print(f'⚠ Error initializing database: {str(e)}')
    
    if not db_initialized:
        # If tables couldn't be created, try with checkfirst=False
        try:
            db.create_all(checkfirst=False)
            db_initialized = True
        except Exception as e:
            print(f'⚠ Second attempt to initialize database failed: {str(e)}')
    
    if db_initialized:
        # Create admin user if it does not exist
        admin = User.query.filter_by(email='admin@policycraft.ai').first()
        if not admin:
            try:
                admin = User(
                    username='admin',
                    email='admin@policycraft.ai',
                    password=generate_password_hash('admin1'),
                    first_name='Admin',
                    last_name='User',
                    role='admin',
                    is_verified=True
                )
                db.session.add(admin)
                db.session.commit()
                print('✓ Admin user created with username: admin, password: admin1')
            except Exception as e:
                print(f'⚠ Error creating admin user: {str(e)}')
        else:
            print('✓ Admin user already exists')
    
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
