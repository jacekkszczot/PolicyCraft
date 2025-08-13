"""
Template filters for the PolicyCraft Flask application.
"""
import re

def register_template_filters(app):
    """Register all template filters with the Flask app."""
    
    @app.template_filter('clean_literature_name')
    def clean_literature_name(document_data, default="Untitled Document"):
        """
        Format literature display names consistently.
        
        Args:
            document_data: Dictionary containing document metadata
            default: Default value if no valid name can be generated
            
        Returns:
            str: Formatted display name (e.g., "Title - Author")
        """
        if not document_data:
            return default
            
        # Get title and author from metadata
        title = document_data.get('title', '')
        author = document_data.get('author', '')
        
        # If we have both title and author, format as "Title - Author"
        if title and author:
            return f"{title} - {author}"
        
        # If we only have title, return that
        if title:
            return title
        
        # If we only have author, return that
        if author:
            return author
        
        # Fallback to document ID if available
        return document_data.get('document_id', default)
    
    @app.template_filter('format_document_title')
    def format_document_title(title, default="Untitled"):
        """
        Clean up and format a document title.
        
        Args:
            title: The title to format
            default: Default value if title is empty
            
        Returns:
            str: Formatted title with proper capitalization and spacing
        """
        if not title:
            return default
            
        # Clean up the title
        title = str(title).strip()
        
        # Remove any file extensions
        title = re.sub(r'\.[a-zA-Z0-9]+$', '', title)
        
        # Replace underscores and hyphens with spaces
        title = re.sub(r'[_-]', ' ', title)
        
        # Title case the string
        title = title.title()
        
        # Clean up any double spaces
        title = ' '.join(title.split())
        
        return title or default
