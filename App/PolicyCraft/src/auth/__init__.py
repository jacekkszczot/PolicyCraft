"""
Authentication and Authorisation Module for PolicyCraft AI Policy Analysis Platform.

This package provides comprehensive user authentication and authorisation services
for the PolicyCraft application. It handles user registration, login, session
management, and account operations with a strong emphasis on security and
user experience.

Key Components:
- User authentication (login/logout)
- Account management (registration, profile updates, deletion)
- Password security and reset functionality
- Session management
- Role-based access control
- Security middleware and decorators

Security Features:
- Secure password hashing using industry-standard algorithms
- CSRF protection for all forms
- Secure session management with configurable timeouts
- Rate limiting for authentication attempts
- Comprehensive audit logging
- Protection against common web vulnerabilities (XSS, CSRF, etc.)

Dependencies:
- Flask-Login for session management
- Flask-WTF for form handling and CSRF protection
- SQLAlchemy for database operations
- Werkzeug for password hashing and security utilities

Example Usage:
    from flask import Flask
    from auth import init_auth
    
    app = Flask(__name__)
    # Configure app with required settings
    init_auth(app)
    
    if __name__ == '__main__':
        app.run()

Note:
    This module is part of the PolicyCraft AI Policy Analysis Platform
    and is designed to work within the larger application ecosystem.
"""
