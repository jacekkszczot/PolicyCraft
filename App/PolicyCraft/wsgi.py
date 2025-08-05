"""
WSGI configuration for PolicyCraft production deployment.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Set environment to production
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Import the Flask application
from app import app

# Set configuration for production
app.config.from_object('config.ProductionConfig')

# WSGI callable
application = app

if __name__ == "__main__":
    application.run()
