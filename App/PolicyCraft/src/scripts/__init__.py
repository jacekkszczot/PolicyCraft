"""
PolicyCraft Scripts Package.

This package contains utility scripts for batch processing, data cleaning,
and validation tasks within the PolicyCraft platform. These scripts are designed
to support various maintenance, data processing, and analysis workflows.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Import key components to make them available at package level
from .clean_dataset import process_new_upload
from .batch_analysis import run_batch_analysis
from .validate_sources import validate as validate_data_sources

# Define package version and exports
__version__ = '1.0.0'
__all__ = [
    'process_new_upload',
    'run_batch_analysis',
    'validate_data_sources'
]