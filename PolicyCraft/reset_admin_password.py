#!/usr/bin/env python3
"""
Reset Admin Password Script for PolicyCraft

This script resets the admin password to 'admin1' in case of login issues.
Run this script if you cannot log in with the default admin credentials.

Usage:
    python reset_admin_password.py

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def reset_admin_password():
    """Reset admin password to 'admin1'."""
    try:
        from src.database.models import User, db
        from app import create_app
        from werkzeug.security import generate_password_hash
        
        print("Resetting admin password...")
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Find admin user
            admin = User.query.filter_by(email='admin@policycraft.ai').first()
            
            if not admin:
                print("Admin user not found!")
                print("   Make sure you have run setup_new_dev.sh first")
                return False
            
            # Reset password
            admin.password_hash = generate_password_hash('admin1')
            db.session.commit()
            
            print("Admin password reset successfully!")
            print("   Email: admin@policycraft.ai")
            print("   Password: admin1")
            print("")
            print("SECURITY WARNING: Change this password immediately after logging in!")
            
            return True
            
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("   Make sure you are in the PolicyCraft directory")
        print("   and have activated the virtual environment")
        return False
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False

def main():
    """Main function."""
    print("PolicyCraft - Admin Password Reset")
    print("==================================")
    print("")
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("Error: app.py not found!")
        print("   Please run this script from the PolicyCraft directory")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Virtual environment may not be activated")
        print("   Consider running: source venv/bin/activate")
        print("")
    
    # Reset password
    if reset_admin_password():
        print("")
        print("You can now log in with:")
        print("   Email: admin@policycraft.ai")
        print("   Password: admin1")
        print("")
        print("Next steps:")
        print("1. Start the application: python app.py")
        print("2. Go to: http://localhost:5001")
        print("3. Log in with the credentials above")
        print("4. Change the password immediately!")
    else:
        print("")
        print("Password reset failed!")
        print("   Please check the error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()
