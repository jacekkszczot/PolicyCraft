#!/bin/bash
set -e

# Create database directories
mkdir -p PolicyCraft-Databases/sqlite-databases
mkdir -p PolicyCraft-Databases/graph-databases

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK resources
python - <<EOF
import nltk
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
EOF

# Copy default environment variables if missing
if [ ! -f .env ]; then
  cp .env.example .env
fi

# Ensure logs directory exists
mkdir -p logs

# Initialise database and create default admin
python - <<EOF
import sys
import os
from pathlib import Path

# Debug: Show current working directory and Python path
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

# Add current directory to Python path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    print("Attempting to import modules...")
    
    # Import with debug
    from src import create_app
    print("✅ Successfully imported create_app")
    
    from src.database import db
    print("✅ Successfully imported db")
    
    from src.database.models import User
    print("✅ Successfully imported User model")
    
    from werkzeug.security import generate_password_hash
    print("✅ Successfully imported generate_password_hash")

    print("Creating Flask app...")
    app = create_app()
    print(f"✅ Flask app created: {app}")
    print(f"✅ App config keys: {list(app.config.keys())}")
    
    # Check if db is properly bound to app
    print(f"✅ Database instance: {db}")
    print(f"✅ Database engines: {hasattr(db, 'engines')}")
    
    print("Entering app context...")
    with app.app_context():
        print("✅ Inside app context")
        
        # Try to create tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Check if admin user already exists
        print("Checking for existing admin user...")
        try:
            existing_admin = User.query.filter_by(email="admin@policycraft.ai").first()
            print(f"✅ Query executed successfully. Existing admin: {existing_admin}")
        except Exception as query_error:
            print(f"❌ Query error: {query_error}")
            print("This might be a database configuration issue.")
            raise
        
        if not existing_admin:
            print("Creating new admin user...")
            admin = User(
                email="admin@policycraft.ai",
                password=generate_password_hash("admin1"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully")
        else:
            print("ℹ️  Admin user already exists")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Check your project structure:")
    print(f"  - Does src/__init__.py exist? {Path('src/__init__.py').exists()}")
    print(f"  - Does src/database/__init__.py exist? {Path('src/database/__init__.py').exists()}")
    print(f"  - Does src/database/models.py exist? {Path('src/database/models.py').exists()}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during setup: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🎉 Setup completed successfully!")
print("")
print("⚠️  SECURITY WARNING: Change the default admin password immediately!")
print("========================================")
print("Default login:")
print("  Email: admin@policycraft.ai")
print("  Password: admin1")
print("")
EOF
