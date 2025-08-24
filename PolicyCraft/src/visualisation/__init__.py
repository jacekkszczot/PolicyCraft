"""
PolicyCraft Visualisation Module.

This package provides data visualisation components for the PolicyCraft platform,
enabling the creation of interactive charts, graphs, and other visual representations
of policy analysis data. The module is built on top of modern visualisation libraries
and is designed to be both powerful and easy to use.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Import key components to make them available at package level
from .charts import ChartGenerator

# Define package version and exports
__version__ = '1.0.0'
__all__ = ['ChartGenerator']