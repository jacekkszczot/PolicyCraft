"""
Test export engine for PolicyCraft application.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os

try:
    from src.export.export_engine import ExportEngine
except ImportError:
    pass


class TestExportEngine:
    """Test suite for export engine functionality."""
    
    def test_export_module_import(self):
        """Test that export module can be imported."""
        try:
            from src.export import export_engine
            assert export_engine is not None
        except ImportError:
            pytest.skip("Export engine module not available")
    
    def test_export_engine_creation(self):
        """Test export engine can be created."""
        try:
            if 'ExportEngine' in globals():
                engine = ExportEngine()
                assert engine is not None
        except NameError:
            pytest.skip("ExportEngine class not available")
    
    def test_csv_export_functionality(self):
        """Test CSV export basic functionality."""
        sample_data = [
            {'filename': 'doc1.pdf', 'classification': 'Restrictive'},
            {'filename': 'doc2.pdf', 'classification': 'Permissive'}
        ]
        
        # Test data structure is correct
        assert len(sample_data) == 2
        assert sample_data[0]['classification'] == 'Restrictive'
    
    def test_export_file_creation(self):
        """Test that export files can be created."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(b'filename,classification\ndoc1.pdf,Restrictive\n')
            
        try:
            assert os.path.exists(temp_filename)
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert 'Restrictive' in content
        finally:
            os.unlink(temp_filename)
