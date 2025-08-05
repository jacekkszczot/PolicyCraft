"""
Admin Interface Module for PolicyCraft AI Policy Analysis Platform.

This package provides administrative functionality for the PolicyCraft application,
including user management, system monitoring, and administrative controls.

Key Features:
- User account management (view, update, delete)
- System health monitoring
- Access control and permissions management
- Administrative dashboard
- System configuration

Security Features:
- Role-based access control (RBAC)
- Secure administrative endpoints
- Audit logging of all administrative actions
- CSRF protection for all admin forms

Dependencies:
- Flask-Admin for administrative interface
- Flask-Login for authentication
- SQLAlchemy for database operations

Example Usage:
    from flask import Flask
    from admin import admin_bp
    
    app = Flask(__name__)
    # Configure app with required settings
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    if __name__ == '__main__':
        app.run()

Note:
    This module is part of the PolicyCraft AI Policy Analysis Platform
    and should only be accessible to users with administrative privileges.
"""

from .routes import admin_bp
