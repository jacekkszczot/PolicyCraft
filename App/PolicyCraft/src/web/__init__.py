"""
PolicyCraft Web Application Module.

This package contains the core web application components for the PolicyCraft platform,
including route definitions, request handlers, and web-specific utilities. The module
integrates with the Flask web framework to provide a user-friendly interface for
interacting with the PolicyCraft policy analysis and recommendation system.

Key Components:
- Route handlers for web interface endpoints
- Form processing and validation
- User session management
- Template rendering and static file serving
- API endpoints for client-side interactivity
- Template filters for consistent data presentation

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Import key components to make them available at package level
from flask import Blueprint

# Create the main web Blueprint
web_bp = Blueprint('web', __name__)

def init_app(app):
    """Initialize the web application with the Flask app instance.
    
    Args:
        app: The Flask application instance
    """
    # Import and register template filters
    from .utils import template_utils
    template_utils.register_template_filters(app)
    
    # Register blueprints
    from . import routes  # Import here to avoid circular imports
    app.register_blueprint(web_bp)
    
    return app

# Define package version and exports
__version__ = '1.0.0'
__all__ = ['web_bp', 'init_app']