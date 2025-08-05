"""
Natural Language Processing (NLP) Module for PolicyCraft AI Policy Analysis Platform.

This package provides core natural language processing capabilities for analysing and processing
policy documents within the PolicyCraft platform. It includes components for text classification,
theme extraction, and other NLP tasks specific to policy document analysis.

Key Components:
    - policy_classifier.py: Implements policy document classification
    - theme_extractor.py: Extracts key themes and topics from policy documents
    - text_processor.py: Handles text preprocessing and normalisation

Features:
    - Custom policy document classification
    - Theme and topic extraction
    - Text preprocessing and normalisation
    - Entity recognition for policy-specific terminology
    - Sentiment and tone analysis for policy language

Dependencies:
    - spaCy: For advanced NLP processing
    - scikit-learn: For machine learning components
    - NLTK: For text processing utilities
    - Gensim: For topic modelling (if implemented)

Example Usage:
    >>> from nlp.policy_classifier import PolicyClassifier
    >>> classifier = PolicyClassifier()
    >>> result = classifier.classify_policy("Sample policy text...")
    
    >>> from nlp.theme_extractor import ThemeExtractor
    >>> extractor = ThemeExtractor()
    >>> themes = extractor.extract_themes("Policy document text...")

Note:
    This module is a core component of the PolicyCraft AI Policy Analysis Platform
    and is designed to handle the specific challenges of policy document analysis.
    It leverages state-of-the-art NLP techniques while maintaining a focus on
    accuracy, interpretability, and performance.
"""

# Import key components for easier access
from .policy_classifier import PolicyClassifier
from .theme_extractor import ThemeExtractor
from .text_processor import TextProcessor

__all__ = ['PolicyClassifier', 'ThemeExtractor', 'TextProcessor']
