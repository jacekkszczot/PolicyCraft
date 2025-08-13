"""
Template utilities for the PolicyCraft application.

This module provides template filters and other template-related utilities
that can be registered with the Flask application.
"""
from typing import Dict, Optional


def clean_literature_name(data, default: str = 'Untitled Document') -> str:
    """
    Generate a clean display name for literature from metadata or document ID.

    Args:
        data: Dictionary containing document metadata with 'title' and/or 'author' keys, or a string document ID
        default: Default name to return if no valid metadata is found

    Returns:
        Formatted string in the format "Title - Author" or a variation based on available data
    """
    if not data:
        return default
    
    # If data is a string (document ID), return it cleaned up
    if isinstance(data, str):
        # Remove file extensions and clean up the name
        cleaned = data.replace('.pdf', '').replace('.docx', '').replace('.txt', '').replace('.md', '')
        # Replace underscores and hyphens with spaces, capitalize words
        cleaned = cleaned.replace('_', ' ').replace('-', ' ')
        # Capitalize each word
        return ' '.join(word.capitalize() for word in cleaned.split())
    
    # If data is a dictionary (metadata), use the original logic
    if isinstance(data, dict):
        title = data.get('title', '').strip()
        author = data.get('author', '').strip()

        if title and author:
            return f"{title} - {author}"
        return title or author or default
    
    return default


def format_document_title(metadata: Optional[Dict[str, str]]) -> str:
    """
    Format a document title from metadata.

    Args:
        metadata: Dictionary containing document metadata with 'title' and/or 'author' keys

    Returns:
        Formatted title string
    """
    if not metadata:
        return 'Untitled Document'

    title = metadata.get('title', '').strip()
    author = metadata.get('author', '').strip()

    if title and author:
        return f"{title} - {author}"
    return title or author or 'Untitled Document'


def register_template_filters(app):
    """
    Register template filters with the Flask application.

    Args:
        app: The Flask application instance
    """
    app.jinja_env.filters['clean_literature_name'] = clean_literature_name
    app.jinja_env.filters['format_document_title'] = format_document_title
    return app
