"""
Literature Processing Module for PolicyCraft AI Policy Analysis.

This module provides comprehensive academic literature processing capabilities
for the PolicyCraft system, enabling systematic updates to the knowledge base
with quality-assured academic insights.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from .literature_engine import LiteratureEngine
from .literature_processor import LiteratureProcessor
from .quality_validator import LiteratureQualityValidator
from .knowledge_manager import KnowledgeBaseManager

__all__ = [
    'LiteratureEngine',
    'LiteratureProcessor', 
    'LiteratureQualityValidator',
    'KnowledgeBaseManager'
]