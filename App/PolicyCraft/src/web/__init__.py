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

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Import key components to make them available at package level
from flask import Blueprint

# Create the main web Blueprint
web_bp = Blueprint('web', __name__)

# Import routes after creating the blueprint to avoid circular imports
from . import routes  # noqa: E402, F401

# Define package version and exports
__version__ = '1.0.0'
__all__ = ['web_bp']