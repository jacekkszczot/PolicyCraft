"""
Configuration settings for PolicyCraft.
Secure database configuration with external storage.

Author: Jacek Robert Kszczot
"""

import os
from datetime import timedelta

class Config:
    """
    Base configuration class with default settings.
    Contains common configuration options for all environments.
    """
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data', 'policies', 'pdf_originals')
    PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data', 'processed')
    RESULTS_FOLDER = os.path.join(os.getcwd(), 'data', 'results')
    
    # Secure database configuration - OUTSIDE application folder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'PolicyCraft-Databases')
    
    # File size and type restrictions
    MAX_CONTENT_LENGTH = 128 * 1024 * 1024  # 128MB maximum file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'doc'}
    
    # Multi-file upload configuration
    MAX_FILES_PER_UPLOAD = 10  # Maximum 10 files at once
    UPLOAD_TIMEOUT = 300  # 5 minutes timeout for large files
    
    # Session configuration - FIXED for localhost consistency
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_DOMAIN = None  # Allow localhost and 127.0.0.1
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    
    # Logging configuration
    LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # NLP Processing configuration
    SPACY_MODEL = 'en_core_web_sm'
    MIN_THEME_FREQUENCY = 2
    MAX_THEMES_PER_DOCUMENT = 15
    
    # Classification thresholds
    RESTRICTIVE_THRESHOLD = 0.6
    PERMISSIVE_THRESHOLD = 0.4
    
    # Chart generation settings
    CHART_WIDTH = 800
    CHART_HEIGHT = 600
    CHART_DPI = 100
    CHART_FORMAT = 'png'
    
    # Application metadata
    APP_NAME = 'PolicyCraft'
    APP_VERSION = '1.0.0'
    APP_AUTHOR = 'Jacek Robert Kszczot'
    APP_DESCRIPTION = 'AI Policy Analysis for Higher Education'

class DevelopmentConfig(Config):
    """
    Development environment configuration with secure database location.
    """
    
    DEBUG = True
    TESTING = False
    
    # Secure development database - OUTSIDE application folder
    DATABASE_PATH = os.path.join(Config.DATABASE_DIR, 'development', 'policycraft_dev.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # FIXED: Development server settings - use localhost consistently
    HOST = 'localhost'  # Changed from 127.0.0.1
    PORT = 5001
    
    # Session configuration for development
    SESSION_COOKIE_SECURE = False  # HTTP in development
    
    # Disable CSRF in development for easier testing
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """
    Production environment configuration with secure database.
    """
    
    DEBUG = False
    TESTING = False
    
    # Secure production database - OUTSIDE application folder
    DATABASE_PATH = os.path.join(Config.DATABASE_DIR, 'production', 'policycraft_prod.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production server settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5001))

class TestingConfig(Config):
    """
    Testing environment configuration with temporary database.
    """
    
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# Configuration dictionary for easy selection
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """
    Get configuration class based on environment name.
    
    Args:
        config_name (str): Environment name ('development', 'production', 'testing')
    
    Returns:
        Config: Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)

def create_secure_directories():
    """
    Create necessary directories for secure database storage.
    Ensures all required folders exist outside the application directory.
    """
    config_obj = get_config()
    
    # Create database directories outside application folder
    database_dirs = [
        os.path.join(config_obj.DATABASE_DIR, 'development'),
        os.path.join(config_obj.DATABASE_DIR, 'production'), 
        os.path.join(config_obj.DATABASE_DIR, 'backups')
    ]
    
    # Create application directories
    app_dirs = [
        config_obj.UPLOAD_FOLDER,
        config_obj.PROCESSED_FOLDER,
        config_obj.RESULTS_FOLDER,
        config_obj.LOG_FOLDER
    ]
    
    all_dirs = database_dirs + app_dirs
    
    for directory in all_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created secure directory: {directory}")

def get_database_info():
    """
    Get information about database locations for security audit.
    
    Returns:
        dict: Database paths and security info
    """
    config_obj = get_config()
    
    return {
        'database_directory': config_obj.DATABASE_DIR,
        'database_path': getattr(config_obj, 'DATABASE_PATH', 'In-memory'),
        'is_outside_app': '../' in str(getattr(config_obj, 'DATABASE_PATH', '')),
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'host': getattr(config_obj, 'HOST', 'localhost'),
        'port': getattr(config_obj, 'PORT', 5001)
    }

if __name__ == '__main__':
    """
    Create all necessary directories and show security info.
    """
    create_secure_directories()
    
    # Show database security information
    db_info = get_database_info()
    print("\n=== Database Security Information ===")
    print(f"Environment: {db_info['environment']}")
    print(f"Database directory: {db_info['database_directory']}")
    print(f"Database path: {db_info['database_path']}")
    print(f"Outside application folder: {db_info['is_outside_app']}")
    print(f"Server will run on: http://{db_info['host']}:{db_info['port']}")
    print("=====================================")