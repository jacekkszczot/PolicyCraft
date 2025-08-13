from django import template
import re
import os

register = template.Library()

@register.filter(name='clean_literature_name')
def clean_literature_name(document_id: str, document_data: dict = None) -> str:
    """
    Template filter to format literature display names consistently.
    
    Args:
        document_id: The document ID to format
        document_data: Optional dictionary containing document metadata
        
    Returns:
        Formatted display name (e.g., "Title - Author")
    """
    if not document_data:
        return document_id
    
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
    
    # Fallback to document ID if no metadata is available
    return document_id

@register.filter(name='format_document_title')
def format_document_title(title: str) -> str:
    """
    Clean up and format a document title.
    
    Args:
        title: The title to format
        
    Returns:
        Formatted title with proper capitalization and spacing
    """
    if not title:
        return ""
    
    # Remove file extension if present
    title = os.path.splitext(title)[0]
    
    # Replace underscores and hyphens with spaces
    title = re.sub(r'[_-]', ' ', title)
    
    # Title case the string
    title = title.title()
    
    # Fix common acronyms and special cases
    title = title.replace('Ai', 'AI')
    title = title.replace('Nlp', 'NLP')
    title = title.replace('Uk', 'UK')
    title = title.replace('Usa', 'USA')
    
    return title.strip()
