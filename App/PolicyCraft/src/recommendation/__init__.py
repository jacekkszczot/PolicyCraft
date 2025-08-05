"""
PolicyCraft Recommendation Engine Module.

This package contains the core components for generating AI policy recommendations
and analyses within the PolicyCraft platform. It includes the ethical framework
analyser, recommendation generator, and supporting utilities for evaluating and
improving AI usage policies in higher education.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Import key components to make them available at package level
from .engine import EthicalFrameworkAnalyzer, RecommendationGenerator

# Define package version and exports
__version__ = '1.0.0'
__all__ = ['EthicalFrameworkAnalyzer', 'RecommendationGenerator']