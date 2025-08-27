#!/bin/bash

# PolicyCraft Development Setup Script
# ===================================
# This script sets up the PolicyCraft development environment
# Compatible with: macOS, Linux, Windows (WSL2)

set -e  # Exit on any error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Function to print coloured output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "PolicyCraft Development Setup"
echo "=============================="

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   print_info "Please run as a regular user with sudo privileges"
   exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory (parent of scripts directory)
cd "$SCRIPT_DIR/.."

# Verify we're in the correct project directory
if [ ! -f "requirements.txt" ] || [ ! -f "app.py" ]; then
    print_error "Not in the correct project directory. Looking for requirements.txt and app.py..."
    echo "Current directory: $(pwd)"
    echo "Script directory: $SCRIPT_DIR"
    echo "Available files:"
    ls -la
    echo "Trying to navigate to the correct project directory..."
    # Try to find the project directory
    if [ -d "PolicyCraft" ]; then
        cd PolicyCraft
        echo "Changed to PolicyCraft subdirectory"
    fi
    # Check again
    if [ ! -f "requirements.txt" ] || [ ! -f "app.py" ]; then
        print_error "Still not in the correct directory. Current directory: $(pwd)"
        echo "Available files:"
        ls -la
        print_error "Please run this script from the PolicyCraft project root directory"
        exit 1
    fi
fi

print_status "Working directory: $(pwd)"

# Check Python installation
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    print_info "Please install Python 3.8+ first:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python@3.12"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install python3 python3-venv python3-pip"
    else
        echo "  Download from https://www.python.org/downloads/"
    fi
    exit 1
fi

# Determine Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_status "Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8+ is required, but found $PYTHON_VERSION"
    print_info "Please upgrade Python to version 3.8 or higher"
    exit 1
fi

# Check if venv module is available
if ! $PYTHON_CMD -c "import venv" 2>/dev/null; then
    print_error "Python venv module is not available"
    print_info "Please install python3-venv package:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install python3-venv"
    fi
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    print_error "pip is not installed or not in PATH"
    print_info "Please install pip first:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python@3.12"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install python3-pip"
    fi
    exit 1
fi

# Determine pip command
PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
fi

print_status "Using pip: $PIP_CMD"

# Create database directory structure
print_info "Creating database directories..."
mkdir -p PolicyCraft-Databases/{development,production,backups}
print_status "Database directories created"

# Remove old database files to ensure clean setup
print_info "Removing old database files..."
rm -f PolicyCraft-Databases/development/*.db
rm -f instance/policycraft.db
rm -f instance/*.db
print_status "Old database files removed"

# Setup virtual environment
print_info "Setting up Python virtual environment..."

# Remove existing venv if it exists
if [ -d "venv" ]; then
    print_info "Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
print_info "Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate the virtual environment
print_info "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS
    source venv/bin/activate
fi

# Verify we're in the right directory and requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in current directory: $(pwd)"
    echo "Available files:"
    ls -la
    exit 1
fi

print_status "Virtual environment created and activated"
print_status "Python path: $(which python)"

# Verify virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_error "Virtual environment is not active"
    exit 1
fi

# Upgrade pip
print_info "Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install dependencies
print_info "Installing dependencies from requirements.txt..."
if ! $PIP_CMD install -r requirements.txt; then
    print_error "Failed to install dependencies"
    print_info "Please check your internet connection and try again"
    print_info "You can also try installing dependencies manually:"
    echo "  $PIP_CMD install -r requirements.txt"
    exit 1
fi
print_status "Dependencies installed successfully"

# Download required NLTK data
print_info "Downloading NLTK data..."
python -c "
import nltk
print('Downloading NLTK data...')
try:
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    print('✓ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠ NLTK download failed: {e}')
    print('Will try during runtime')
"

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    print_warning ".env.example not found, creating basic .env file"
    cat > .env << EOF
# PolicyCraft Environment Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production
HOST=localhost
PORT=5001

# Database Configuration
SQLALCHEMY_TRACK_MODIFICATIONS=false

# MongoDB Configuration (required for full functionality)
MONGODB_URI=mongodb://localhost:27017/policycraft

# Feature Flags (enable full functionality)
FEATURE_ADVANCED_ENGINE=true

# Default Admin Credentials
DEFAULT_ADMIN_EMAIL=admin@policycraft.ai
DEFAULT_ADMIN_PASSWORD=admin1
EOF
    print_status "Basic .env file created"
else
    # Copy environment template
    print_info "Copying environment template..."
    cp .env.example .env
    print_status "Environment file created from template"
fi

# Add default admin credentials to .env if not already present
if ! grep -q "DEFAULT_ADMIN_EMAIL" .env; then
    echo "" >> .env
    echo "# Default admin credentials" >> .env
    echo "DEFAULT_ADMIN_EMAIL=admin@policycraft.ai" >> .env
    echo "DEFAULT_ADMIN_PASSWORD=admin1" >> .env
    print_status "Default admin credentials added to .env"
fi

# Add required environment variables if not already present
print_info "Checking and adding required environment variables..."

# Add FEATURE_ADVANCED_ENGINE if not present
if ! grep -q "FEATURE_ADVANCED_ENGINE" .env; then
    echo "" >> .env
    echo "# Feature Flags (enable full functionality)" >> .env
    echo "FEATURE_ADVANCED_ENGINE=true" >> .env
    print_status "FEATURE_ADVANCED_ENGINE=true added to .env"
fi

# Add MONGODB_URI if not present
if ! grep -q "MONGODB_URI" .env; then
    echo "" >> .env
    echo "# MongoDB Configuration (required for full functionality)" >> .env
    echo "MONGODB_URI=mongodb://localhost:27017/policycraft" >> .env
    print_status "MONGODB_URI added to .env"
fi

# Add SECRET_KEY if not present
if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your-secret-key-here" .env; then
    # Generate a secure random key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "24054ea12ad3c218bfe4c492b62598b85b893aac596e306a56a18330db2bc85f")
    
    # Replace existing SECRET_KEY or add new one
    if grep -q "SECRET_KEY=" .env; then
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        rm -f .env.bak
    else
        echo "" >> .env
        echo "# Security Configuration" >> .env
        echo "SECRET_KEY=$SECRET_KEY" >> .env
    fi
    print_status "Secure SECRET_KEY generated and added to .env"
fi

# Create logs directory
print_info "Creating logs directory..."
mkdir -p logs
touch logs/.gitkeep
print_status "Logs directory created"

# Check MongoDB status and setup
print_info "Checking MongoDB status and setup..."
if command -v mongod &> /dev/null; then
    # Detect MongoDB installation path
    MONGODB_BIN=$(which mongod)
    if [[ "$MONGODB_BIN" == "/opt/homebrew/bin/mongod" ]]; then
        # Apple Silicon (M1/M2)
        MONGODB_CONFIG="/opt/homebrew/etc/mongod.conf"
        MONGODB_VAR="/opt/homebrew/var"
        print_info "Detected Apple Silicon MongoDB installation"
    elif [[ "$MONGODB_BIN" == "/usr/local/bin/mongod" ]]; then
        # Intel Mac
        MONGODB_CONFIG="/usr/local/etc/mongod.conf"
        MONGODB_VAR="/usr/local/var"
        print_info "Detected Intel Mac MongoDB installation"
    else
        # Other systems
        MONGODB_CONFIG="/etc/mongod.conf"
        MONGODB_VAR="/var/lib/mongodb"
        print_info "Detected other system MongoDB installation"
    fi
    
    # Create MongoDB directories if they don't exist
    print_info "Creating MongoDB directories..."
    if ! sudo mkdir -p "$MONGODB_VAR/log/mongodb" 2>/dev/null; then
        print_warning "Could not create MongoDB log directory with sudo"
        print_info "You may need to create MongoDB directories manually"
    fi
    if ! sudo mkdir -p "$MONGODB_VAR/mongodb" 2>/dev/null; then
        print_warning "Could not create MongoDB data directory with sudo"
        print_info "You may need to create MongoDB directories manually"
    fi
    
    # Try to set ownership
    if sudo chown -R $(whoami) "$MONGODB_VAR/log/mongodb" 2>/dev/null; then
        print_status "MongoDB log directory ownership set"
    fi
    if sudo chown -R $(whoami) "$MONGODB_VAR/mongodb" 2>/dev/null; then
        print_status "MongoDB data directory ownership set"
    fi
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        print_status "MongoDB is already running"
    else
        print_info "MongoDB is installed but not running"
        print_info "Starting MongoDB..."
        
        # Try to start MongoDB with detected paths
        if [ -f "$MONGODB_CONFIG" ]; then
            print_info "Using config file: $MONGODB_CONFIG"
            # On macOS, don't use --fork as it's incompatible
            if [[ "$OSTYPE" == "darwin"* ]]; then
                print_info "macOS detected - starting MongoDB without fork (will run in background)"
                mongod --config "$MONGODB_CONFIG" --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" &
            else
                mongod --config "$MONGODB_CONFIG" --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" --fork
            fi
        else
            print_info "No config file found, starting with default settings"
            # On macOS, don't use --fork as it's incompatible
            if [[ "$OSTYPE" == "darwin"* ]]; then
                print_info "macOS detected - starting MongoDB without fork (will run in background)"
                mongod --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" &
            else
                mongod --dbpath "$MONGODB_VAR/mongodb" --logpath "$MONGODB_VAR/log/mongodb/mongo.log" --fork
            fi
        fi
        
        # Wait a moment and check if it's running
        sleep 3
        if pgrep -x "mongod" > /dev/null; then
            print_status "MongoDB started successfully"
        else
            print_warning "Failed to start MongoDB automatically"
            print_info "Please start MongoDB manually:"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "  mongod --dbpath $MONGODB_VAR/mongodb --logpath $MONGODB_VAR/log/mongodb/mongo.log &"
                echo "  Or use brew services: brew services start mongodb/brew/mongodb-community"
            else
                echo "  mongod --dbpath $MONGODB_VAR/mongodb --logpath $MONGODB_VAR/log/mongodb/mongo.log"
            fi
        fi
    fi
else
    print_warning "MongoDB is not installed"
    print_info "Install MongoDB first:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install mongodb/brew/mongodb-community"
        echo "  Then start it: brew services start mongodb/brew/mongodb-community"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install mongodb-org"
        echo "  sudo systemctl start mongod"
        echo "  sudo systemctl enable mongod"
    else
        echo "  Follow MongoDB installation guide for your system:"
        echo "  https://docs.mongodb.com/manual/installation/"
    fi
    
    # Offer to start MongoDB with Docker
    print_info "Starting MongoDB with Docker as alternative..."
    if command -v docker &> /dev/null; then
        # Check if Docker is running
        if docker info &> /dev/null; then
            print_info "Docker is available and running"
            # Check if MongoDB container already exists
            if docker ps -a --format "table {{.Names}}" | grep -q "mongodb-policycraft"; then
                print_info "MongoDB container already exists, starting it..."
                docker start mongodb-policycraft
                if docker ps --format "table {{.Names}}" | grep -q "mongodb-policycraft"; then
                    print_status "MongoDB container started successfully"
                else
                    print_warning "Failed to start existing MongoDB container"
                fi
            else
                print_info "Creating new MongoDB container..."
                docker run -d --name mongodb-policycraft -p 27017:27017 -v mongodb_data:/data/db mongo:latest
                if docker ps --format "table {{.Names}}" | grep -q "mongodb-policycraft"; then
                    print_status "MongoDB container created and started successfully"
                else
                    print_warning "Failed to create MongoDB container"
                fi
            fi
        else
            print_warning "Docker is not running. Start Docker Desktop first."
        fi
    else
        print_info "Docker is not installed. You can also use Docker: docker run -d -p 27017:27017 --name mongodb-policycraft mongo:latest"
    fi
fi

# Initialize database using the new configuration
print_info "Initializing database with new configuration..."
python -c "
import os, sys
from pathlib import Path
from flask import Flask
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, '.')

try:
    from config import get_config, create_secure_directories
    print('✓ Config loaded successfully')
except ImportError as e:
    print(f'✗ Error importing config: {e}')
    print('Make sure config.py exists and is properly configured')
    sys.exit(1)

# Get the current working directory as base path
BASE_DIR = Path(os.getcwd()).absolute()
print(f'ℹ Working directory: {BASE_DIR}')

# Create secure directories
try:
    create_secure_directories()
    print('✓ Secure directories created')
except Exception as e:
    print(f'⚠ Warning creating secure directories: {e}')

# Configure database path using the new config structure
try:
    config = get_config()
    DB_URI = config.SQLALCHEMY_DATABASE_URI
    print(f'✓ Database URI from config: {DB_URI}')
except Exception as e:
    print(f'⚠ Error getting config: {e}')
    # Fallback to default path
    DB_URI = f'sqlite:///{BASE_DIR}/PolicyCraft-Databases/development/policycraft_dev.db'
    print(f'ℹ Using fallback database URI: {DB_URI}')

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
    print('✓ SQLAlchemy initialized')
except Exception as e:
    print(f'✗ Error initializing SQLAlchemy: {e}')
    print('Please check that all dependencies are installed correctly')
    sys.exit(1)

# Create all tables and set up admin user
with app.app_context():
    try:
        # Drop all tables first to ensure clean slate
        print('ℹ Dropping existing tables...')
        db.drop_all()
        print('✓ Existing tables dropped')
        
        # Create tables with new model
        print('ℹ Creating database tables...')
        db.create_all()
        print('✓ Database tables created')
        
        # Create admin user
        print('ℹ Creating admin user...')
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
        print('✓ Admin user created with username: admin, password: admin1')
            
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
            print('✓ Database configuration updated in .env')
            print(f'ℹ Database URI: {DB_URI}')
            
        except Exception as e:
            print(f'⚠ Could not update .env: {e}')
            print(f'Please manually add to your .env file:')
            print(f'SQLALCHEMY_DATABASE_URI={DB_URI}')
            print('SQLALCHEMY_TRACK_MODIFICATIONS=False')
            
        print('✓ Database initialized successfully')
        
    except Exception as e:
        import traceback
        print('✗ Error during database initialization:')
        print(traceback.format_exc())
        print(f'ℹ Current working directory: {os.getcwd()}')
        print('ℹ Please check the error above and try again')
        sys.exit(1)
"

# Test MongoDB connection
print_info "Testing MongoDB connection..."
if command -v mongod &> /dev/null && pgrep -x "mongod" > /dev/null; then
    print_status "MongoDB is running locally"
elif docker ps --format "table {{.Names}}" | grep -q "mongodb-policycraft"; then
    print_status "MongoDB is running in Docker"
else
    print_warning "MongoDB is not running. Please start it manually:"
    print_info "  - Local: brew services start mongodb/brew/mongodb-community (macOS)"
    print_info "  - Docker: docker run -d -p 27017:27017 --name mongodb-policycraft mongo:latest"
fi

# Test the application
print_info "Testing application startup..."
if python -c "
import sys
sys.path.insert(0, '.')
try:
    from app import create_app
    app = create_app()
    print('✓ Application created successfully')
    print('✓ All modules imported correctly')
except Exception as e:
    print(f'✗ Error creating application: {e}')
    sys.exit(1)
"; then
    print_status "Application test passed"
else
    print_warning "Application test failed - there may be configuration issues"
fi

echo ""
echo ""
echo "========================================"
echo "🎉 Setup complete!"
echo ""
echo "🔐 Admin access:"
echo "   - Email: admin@policycraft.ai"
echo "   - Password: admin1"
echo ""
echo "📋 Next steps:"
echo "1. Ensure MongoDB is running:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   brew services start mongodb/brew/mongodb-community"
    echo "   Or manually: mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log &"
else
    echo "   sudo systemctl start mongod"
    echo "   sudo systemctl enable mongod"
fi
echo "2. Run the application: python app.py"
echo "3. Access the application at: http://localhost:5001"
echo "4. Log in with admin credentials above"
echo "5. Change the default admin password after first login"
echo ""
echo "⚠️  SECURITY WARNING: Change the default admin password immediately!"
echo ""
echo "ℹ️  Note: This setup uses the new dual-database configuration:"
echo "   - SQLite: User accounts and basic data"
echo "   - MongoDB: Policy analyses, recommendations, and knowledge base"
echo ""
echo "🔧 If you have login issues:"
echo "   - Make sure MongoDB is running"
echo "   - Check that the database was created successfully"
echo "   - Verify admin user exists in the database"
echo "   - Check the logs directory for error messages"
echo ""
echo "🐳 Alternative MongoDB setup (Docker):"
echo "   docker run -d -p 27017:27017 --name mongodb-policycraft mongo:7"
echo "   docker logs mongodb-policycraft"
echo ""
echo "📚 For more help, see:"
echo "   - docs/troubleshooting_guide.md"
echo "   - README.md"
echo "========================================"
