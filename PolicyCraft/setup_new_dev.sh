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
from pathlib import Path
from flask import Flask
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, '.')
from config import get_config, create_secure_directories

# Get the current working directory as base path
BASE_DIR = Path(os.getcwd()).absolute()
# Ensure we're in the right directory by changing to the script's location
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
if script_dir != str(BASE_DIR):
    os.chdir(script_dir)
    BASE_DIR = Path(script_dir).absolute()

# Configure database path
INSTANCE_DIR = BASE_DIR / 'instance'
DB_PATH = INSTANCE_DIR / 'policycraft.db'
DB_URI = f'sqlite:///{DB_PATH}'

# Create instance directory with proper permissions
INSTANCE_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)

# Create and configure the Flask application
app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEFAULT_ADMIN_EMAIL='admin@policycraft.ai',
    DEFAULT_ADMIN_PASSWORD='admin1'
)

# Initialise SQLAlchemy
from src.database.models import db, User
db.init_app(app)

print(f'🔍 Database path: {DB_PATH}')
print(f'🔍 Instance directory exists: {INSTANCE_DIR.exists()}')
print(f'🔍 Instance directory permissions: {oct(INSTANCE_DIR.stat().st_mode & 0o777)}')

# Create all tables and set up admin user
with app.app_context():
    try:
        # Create tables
        print('🔄 Creating database tables...')
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@policycraft.ai').first()
        if not admin:
            print('🔄 Creating admin user...')
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
            print('✅ Admin user created with username: admin, password: admin1')
        else:
            print('ℹ️  Admin user already exists')
            
        print(f'✅ Database initialised successfully at {DB_PATH}')
        
    except Exception as e:
        import traceback
        print('❌ Error during database initialisation:')
        print(traceback.format_exc())
        print(f'Current working directory: {os.getcwd()}')
        if INSTANCE_DIR.exists():
            print(f'Instance directory contents: {os.listdir(INSTANCE_DIR)}')
        else:
            print('Instance directory does not exist')
        sys.exit(1)
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
