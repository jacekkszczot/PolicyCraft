"""
Configuration for PolicyCraft.
This file contains the actual configuration settings for the application.

Note: Never commit sensitive information to version control.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration with default settings."""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQLAlchemy configuration (required by Flask-SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        f'sqlite:///{os.path.join(os.getcwd(), "PolicyCraft-Databases", "development", "policycraft_dev.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB configuration
    MONGODB_SETTINGS = {
        'db': os.environ.get('MONGODB_DB', 'policycraft'),
        'host': os.environ.get('MONGODB_HOST', 'localhost'),
        'port': int(os.environ.get('MONGODB_PORT', 27017)),
        'username': os.environ.get('MONGODB_USERNAME', ''),
        'password': os.environ.get('MONGODB_PASSWORD', ''),
        'connectTimeoutMS': 10000,  # 10 seconds connection timeout
        'socketTimeoutMS': 30000,   # 30 seconds socket timeout
        'serverSelectionTimeoutMS': 5000,  # 5 seconds server selection timeout
        'connect': False,  # Use connect=False to handle connection errors gracefully
        'retryWrites': True,
        'w': 'majority'
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
    
    # Flask-WTF configuration
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'false').lower() in ('true', '1', 't')

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
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
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

# Helper functions for application bootstrap
def get_config(env: str | None = None):
    """Return the appropriate configuration class based on environment.

    This function is intentionally self-contained so that it works when this file
    is imported dynamically as a fallback (i.e. without relying on config.py).
    """
    import os as _os

    if env is None:
        env = _os.environ.get("FLASK_ENV", "default")
    return config.get(env, config['default'])


def create_secure_directories():
    """Ensure required directories exist for runtime operation.

    Creates upload, processed and logs directories if they do not already exist.
    Safe to call multiple times.
    """
    import os as _os

    cfg_cls = get_config()
    cfg = cfg_cls()
    dirs = [
        cfg.UPLOAD_FOLDER,
        cfg.PROCESSED_FOLDER,
        _os.path.join(_os.getcwd(), "logs"),
        # Create database directory for SQLite
        os.path.dirname(cfg.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) if cfg.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///') else None,
    ]
    for d in dirs:
        if d:  # Skip None values
            _os.makedirs(d, exist_ok=True)
