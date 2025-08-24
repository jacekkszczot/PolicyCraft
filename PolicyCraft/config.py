"""
Local configuration for PolicyCraft (overrides config.example.py).
This file is safe to commit for development; do not put secrets here.
"""
import os
from datetime import timedelta

# --- Base settings ---
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # SQLAlchemy (required by Flask-SQLAlchemy init)
    # SQLite file relative to repo root (created automatically)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///PolicyCraft-Databases/development/policycraft_dev.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads/processing
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'PolicyCraft', 'data', 'policies', 'pdf_originals')
    PROCESSED_FOLDER = os.path.join(os.getcwd(), 'PolicyCraft', 'data', 'processed')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Session/cookies
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Misc
    APP_NAME = "PolicyCraft"
    APP_VERSION = "1.0.0"
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    # Use in-memory DB for tests unless overridden
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env: str | None = None):
    import os as _os
    if env is None:
        env = _os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])


def create_secure_directories():
    """Ensure required directories exist (uploads, processed, logs, DB folder)."""
    import os as _os
    cfg_cls = get_config()
    cfg = cfg_cls()

    dirs = [
        cfg.UPLOAD_FOLDER,
        cfg.PROCESSED_FOLDER,
        _os.path.join(_os.getcwd(), 'PolicyCraft', 'logs'),
        _os.path.join(_os.getcwd(), 'PolicyCraft-Databases', 'development'),
    ]
    for d in dirs:
        _os.makedirs(d, exist_ok=True)
