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

# Remove old database files to ensure clean setup
echo "Removing old database files..."
rm -f PolicyCraft-Databases/development/*.db
rm -f instance/policycraft.db
rm -f instance/*.db
echo "✓ Old database files removed"

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

# Check MongoDB status and setup
echo "Checking MongoDB status and setup..."
if command -v mongod &> /dev/null; then
    # Detect MongoDB installation path
    MONGODB_BIN=$(which mongod)
    if [[ "$MONGODB_BIN" == "/opt/homebrew/bin/mongod" ]]; then
        # Apple Silicon (M1/M2)
        MONGODB_CONFIG="/opt/homebrew/etc/mongod.conf"
        MONGODB_VAR="/opt/homebrew/var"
        echo "Detected Apple Silicon MongoDB installation"
    elif [[ "$MONGODB_BIN" == "/usr/local/bin/mongod" ]]; then
        # Intel Mac
        MONGODB_CONFIG="/usr/local/etc/mongod.conf"
        MONGODB_VAR="/usr/local/var"
        echo "Detected Intel Mac MongoDB installation"
    else
        # Other systems
        MONGODB_CONFIG="/etc/mongod.conf"
        MONGODB_VAR="/var/lib/mongodb"
        echo "Detected other system MongoDB installation"
    fi
    
    # Create MongoDB directories if they don't exist
    echo "Creating MongoDB directories..."
    sudo mkdir -p "$MONGODB_VAR/log/mongodb"
    sudo mkdir -p "$MONGODB_VAR/mongodb"
    sudo chown -R $(whoami) "$MONGODB_VAR/log/mongodb"
    sudo chown -R $(whoami) "$MONGODB_VAR/mongodb"
    echo "MongoDB directories created"
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        echo "MongoDB is running"
    else
        echo "MongoDB is installed but not running"
        echo "Starting MongoDB..."
        
        # Try to start MongoDB with detected paths
        if [ -f "$MONGODB_CONFIG" ]; then
            echo "Using config file: $MONGODB_CONFIG"
            mongod --config "$MONGODB_CONFIG" --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" --fork
        else
            echo "No config file found, starting with default settings"
            mongod --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" --fork
        fi
        
        # Wait a moment and check if it's running
        sleep 2
        if pgrep -x "mongod" > /dev/null; then
            echo "MongoDB started successfully"
        else
            echo "Failed to start MongoDB"
            echo "Please start MongoDB manually:"
            echo "mongod --dbpath $MONGODB_VAR/mongodb --logpath $MONGODB_VAR/log/mongodb/mongo.log"
        fi
    fi
else
    echo "MongoDB is not installed"
    echo "Install MongoDB first:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "brew install mongodb/brew/mongodb-community"
        echo "Then start it: brew services start mongodb/brew/mongodb-community"
    else
        echo "Follow MongoDB installation guide for your system"
    fi
fi

# Initialize database using the new configuration
echo "Initializing database with new configuration..."
python -c "
import os, sys
from pathlib import Path
from flask import Flask
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, '.')

try:
    from config import get_config, create_secure_directories
    print('Config loaded successfully')
except ImportError as e:
    print(f'Error importing config: {e}')
    print('Make sure config.py exists and is properly configured')
    sys.exit(1)

# Get the current working directory as base path
BASE_DIR = Path(os.getcwd()).absolute()
print(f'Working directory: {BASE_DIR}')

# Create secure directories
try:
    create_secure_directories()
    print('Secure directories created')
except Exception as e:
    print(f'Warning creating secure directories: {e}')

# Configure database path using the new config structure
try:
    config = get_config()
    DB_URI = config.SQLALCHEMY_DATABASE_URI
    print(f'Database URI from config: {DB_URI}')
except Exception as e:
    print(f'Error getting config: {e}')
    # Fallback to default path
    DB_URI = f'sqlite:///{BASE_DIR}/PolicyCraft-Databases/development/policycraft_dev.db'
    print(f'Using fallback database URI: {DB_URI}')

# Create and configure the Flask application
app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEFAULT_ADMIN_EMAIL='admin@policycraft.ai',
    DEFAULT_ADMIN_PASSWORD='admin1'
)

# Initialise SQLAlchemy
try:
    from src.database.models import db, User
    db.init_app(app)
    print('SQLAlchemy initialized')
except Exception as e:
    print(f'Error initializing SQLAlchemy: {e}')
    sys.exit(1)

# Create all tables and set up admin user
with app.app_context():
    try:
        # Drop all tables first to ensure clean slate
        print('Dropping existing tables...')
        db.drop_all()
        print('Existing tables dropped')
        
        # Create tables with new model
        print('Creating database tables...')
        db.create_all()
        print('Database tables created')
        
        # Create admin user
        print('Creating admin user...')
        admin = User(
            username='admin',
            email='admin@policycraft.ai',
            password='admin1',  # This will be hashed by User.__init__
            first_name='Admin',
            last_name='User',
            role='admin',
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created with username: admin, password: admin1')
            
        # Update .env with database URI
        try:
            env_path = Path('.env')
            if not env_path.exists():
                env_path.touch()
            
            # Read existing content
            env_content = ''
            db_uri_updated = False
            
            if env_path.stat().st_size > 0:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('SQLALCHEMY_DATABASE_URI='):
                            env_content += f'SQLALCHEMY_DATABASE_URI={DB_URI}\n'
                            db_uri_updated = True
                        else:
                            env_content += line
            
            # Add SQLALCHEMY_DATABASE_URI if it wasn't in the file
            if not db_uri_updated:
                env_content += f'\n# Database configuration\nSQLALCHEMY_DATABASE_URI={DB_URI}\nSQLALCHEMY_TRACK_MODIFICATIONS=False\n'
            
            # Write back to .env
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            # Set proper permissions
            env_path.chmod(0o600)  # Only owner can read/write
            print('Database configuration updated in .env')
            print(f'Database URI: {DB_URI}')
            
        except Exception as e:
            print(f'Could not update .env: {e}')
            print(f'Please manually add to your .env file:')
            print(f'SQLALCHEMY_DATABASE_URI={DB_URI}')
            print('SQLALCHEMY_TRACK_MODIFICATIONS=False')
            
        print(f'Database initialized successfully')
        
    except Exception as e:
        import traceback
        print('Error during database initialization:')
        print(traceback.format_exc())
        print(f'Current working directory: {os.getcwd()}')
        sys.exit(1)
"

echo ""
echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Admin access:"
echo "- Email: admin@policycraft.ai"
echo "- Password: admin1"
echo ""
echo "Next steps:"
echo "1. Ensure MongoDB is running: brew services start mongodb/brew/mongodb-community"
echo "2. Run the application: python app.py"
echo "3. Access the application at: http://localhost:5001"
echo "4. Log in with admin credentials above"
echo "5. Change the default admin password after first login"
echo ""
echo "SECURITY WARNING: Change the default admin password immediately!"
echo ""
echo "Note: This setup uses the new dual-database configuration:"
echo "   - SQLite: User accounts and basic data"
echo "   - MongoDB: Policy analyses, recommendations, and knowledge base"
echo ""
echo "If you have login issues:"
echo "   - Make sure MongoDB is running"
echo "   - Check that the database was created successfully"
echo "   - Verify admin user exists in the database"
echo "========================================"
