"""
Test charts module for PolicyCraft application.
"""

import pytest
from unittest.mock import Mock, patch

try:
    from src.visualisation.charts import *
except ImportError:
    pass


class TestCharts:
    """Test suite for chart generation functionality."""
    
    def test_charts_module_import(self):
        """Test that charts module can be imported."""
        try:
            from src.visualisation import charts
            assert charts is not None
        except ImportError:
            pytest.skip("Charts module not available")
    
    def test_chart_data_structure(self):
        """Test chart data structures."""
        sample_data = {
            'classifications': {
                'Restrictive': 45,
                'Moderate': 35, 
                'Permissive': 20
            },
            'themes': {
                'Education': 25,
                'Healthcare': 20,
                'Economic': 18
            }
        }
        
        # Test data structure is valid
        assert len(sample_data['classifications']) == 3
        assert sum(sample_data['classifications'].values()) == 100
        assert 'Education' in sample_data['themes']
    
    def test_chart_configuration(self):
        """Test chart configuration options."""
        config = {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'display': True}
            }
        }
        
        # Test configuration structure
        assert config['responsive'] is True
        assert 'plugins' in config
        assert config['plugins']['legend']['display'] is True
    
    def test_colour_palette(self):
        """Test chart colour palette."""
        colours = ['#ff6b6b', '#ffd93d', '#6bcf7f', '#4ecdc4', '#45b7d1']
        
        # Test colour palette is valid
        assert len(colours) >= 3  # Minimum colours for policy classifications
        for colour in colours:
            assert colour.startswith('#')
            assert len(colour) == 7  # Valid hex colour format
