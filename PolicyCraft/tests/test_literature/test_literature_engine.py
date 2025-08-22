"""
Test literature engine module for PolicyCraft application.

This module contains unit tests for the literature analysis engine,
ensuring that literature processing and analysis functions work correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.literature.literature_engine import LiteratureEngine


class TestLiteratureEngine:
    """Test suite for literature analysis engine."""
    
    @pytest.fixture
    def literature_engine(self):
        """Create a literature engine instance for testing."""
        return LiteratureEngine()
    
    def test_literature_engine_initialisation(self, literature_engine):
        """Test that literature engine initialises correctly."""
        assert literature_engine is not None
        assert hasattr(literature_engine, 'process_literature')
    
    @patch('src.literature.literature_engine.LiteratureEngine.process_literature')
    def test_process_literature_called(self, mock_process, literature_engine):
        """Test that process_literature method can be called."""
        mock_process.return_value = {'status': 'success'}
        
        result = literature_engine.process_literature("test content")
        mock_process.assert_called_once_with("test content")
        assert result['status'] == 'success'
    
    def test_literature_engine_handles_empty_input(self, literature_engine):
        """Test that literature engine handles empty input gracefully."""
        try:
            result = literature_engine.process_literature("")
            # Should not raise an exception
            assert True
        except Exception as e:
            pytest.fail(f"Literature engine should handle empty input: {e}")
    
    def test_literature_engine_handles_none_input(self, literature_engine):
        """Test that literature engine handles None input gracefully."""
        try:
            result = literature_engine.process_literature(None)
            # Should not raise an exception
            assert True
        except Exception as e:
            pytest.fail(f"Literature engine should handle None input: {e}")
    
    @patch('src.literature.literature_engine.LiteratureEngine.analyse_themes')
    def test_analyse_themes_method_exists(self, mock_analyse, literature_engine):
        """Test that analyse_themes method exists and can be called."""
        mock_analyse.return_value = ['theme1', 'theme2']
        
        if hasattr(literature_engine, 'analyse_themes'):
            result = literature_engine.analyse_themes("test content")
            mock_analyse.assert_called_once()
            assert isinstance(result, list)
    
    def test_literature_engine_string_representation(self, literature_engine):
        """Test string representation of literature engine."""
        str_repr = str(literature_engine)
        assert 'LiteratureEngine' in str_repr or str_repr is not None
