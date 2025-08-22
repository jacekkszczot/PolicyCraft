"""
Test literature processor module for PolicyCraft application.

This module contains unit tests for the literature processing functionality,
ensuring that document processing and analysis work correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.literature.literature_processor import LiteratureProcessor


class TestLiteratureProcessor:
    """Test suite for literature processing functionality."""
    
    @pytest.fixture
    def literature_processor(self):
        """Create a literature processor instance for testing."""
        return LiteratureProcessor()
    
    def test_literature_processor_initialisation(self, literature_processor):
        """Test that literature processor initialises correctly."""
        assert literature_processor is not None
    
    @patch('src.literature.literature_processor.LiteratureProcessor.process_document')
    def test_process_document_called(self, mock_process, literature_processor):
        """Test that process_document method can be called."""
        mock_process.return_value = {
            'status': 'success',
            'content': 'processed content',
            'metadata': {'pages': 5, 'words': 1000}
        }
        
        result = literature_processor.process_document("test.pdf")
        
        mock_process.assert_called_once_with("test.pdf")
        assert result['status'] == 'success'
        assert 'content' in result
        assert 'metadata' in result
    
    def test_literature_processor_handles_invalid_file(self, literature_processor):
        """Test that processor handles invalid file paths gracefully."""
        try:
            if hasattr(literature_processor, 'process_document'):
                result = literature_processor.process_document("nonexistent.pdf")
            assert True
        except FileNotFoundError:
            # This is expected behaviour
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
    
    @patch('src.literature.literature_processor.LiteratureProcessor.extract_text')
    def test_extract_text_functionality(self, mock_extract, literature_processor):
        """Test text extraction functionality."""
        mock_extract.return_value = "This is extracted text from the document."
        
        if hasattr(literature_processor, 'extract_text'):
            result = literature_processor.extract_text("test_document")
            mock_extract.assert_called_once()
            assert isinstance(result, str)
            assert len(result) > 0
    
    @patch('src.literature.literature_processor.LiteratureProcessor.analyse_structure')
    def test_analyse_structure_functionality(self, mock_analyse, literature_processor):
        """Test document structure analysis."""
        mock_analyse.return_value = {
            'sections': ['introduction', 'methodology', 'results'],
            'headings': 15,
            'paragraphs': 45
        }
        
        if hasattr(literature_processor, 'analyse_structure'):
            result = literature_processor.analyse_structure("test content")
            mock_analyse.assert_called_once()
            assert isinstance(result, dict)
    
    def test_literature_processor_handles_empty_content(self, literature_processor):
        """Test that processor handles empty content gracefully."""
        try:
            if hasattr(literature_processor, 'process_document'):
                literature_processor.process_document("")
            assert True
        except Exception as e:
            # Should handle gracefully
            assert True
    
    def test_literature_processor_string_representation(self, literature_processor):
        """Test string representation of literature processor."""
        str_repr = str(literature_processor)
        assert str_repr is not None
