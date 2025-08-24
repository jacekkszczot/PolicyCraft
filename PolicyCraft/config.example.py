"""
Configuration template for PolicyCraft.
Copy this file to config.py and update the values as needed.

Note: Never commit sensitive information to version control.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration with default settings."""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB configuration
    MONGODB_SETTINGS = {
        'db': os.environ.get('MONGODB_DB', 'policycraft'),
        'host': os.environ.get('MONGODB_HOST', 'localhost'),
        'port': int(os.environ.get('MONGODB_PORT', 27017)),
        'username': os.environ.get('MONGODB_USERNAME', ''),
        'password': os.environ.get('MONGODB_PASSWORD', '')
    }

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data', 'policies', 'pdf_originals')
    PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data', 'processed')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dev-salt-change-in-production'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')

    # Application settings
    APP_NAME = "PolicyCraft"
    APP_VERSION = "1.0.0"
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
    TESTING = False

    # API Keys (if any)
    # Example: OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'policycraft_dev',
        'host': 'localhost',
        'port': 27017
    }

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    MONGODB_SETTINGS = {
        'db': 'policycraft_test',
        'host': 'localhost',
        'port': 27017
    }
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    # Add production-specific settings here

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
