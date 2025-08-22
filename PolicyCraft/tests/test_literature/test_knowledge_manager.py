"""
Test knowledge manager module for PolicyCraft application.

This module contains unit tests for the knowledge management system,
ensuring that knowledge storage and retrieval functions work correctly.
"""

import pytest
from unittest.mock import patch
import os

from src.literature.knowledge_manager import KnowledgeBaseManager


class TestKnowledgeManager:
    """Test suite for knowledge base management system."""
    
    @pytest.fixture
    def knowledge_manager(self, tmp_path):
        """Create an isolated KnowledgeBaseManager instance for testing."""
        kb_path = tmp_path / "kb"
        os.makedirs(kb_path, exist_ok=True)
        return KnowledgeBaseManager(knowledge_base_path=str(kb_path))
    
    def test_knowledge_manager_initialisation(self, knowledge_manager):
        """Test that knowledge manager initialises correctly."""
        assert knowledge_manager is not None
    
    def test_integrate_new_document_workflow(self, knowledge_manager):
        """Integration returns a structured result for minimal valid input."""
        processing_results = {
            'document_id': 'doc1234',
            'metadata': {
                'title': 'Sample Study',
                'publication_date': '2024-05-01',
                'document_type': 'article',
            },
            'extracted_insights': ["Insight A", "Insight B"],
            'processing_recommendation': {'action': 'approve_new_document', 'confidence': 'high'}
        }
        result = knowledge_manager.integrate_new_document(processing_results)
        assert isinstance(result, dict)
        assert result.get('status') in {'success', 'error', 'rejected', 'manual_review_required'}
    
    @patch('src.literature.knowledge_manager.KnowledgeBaseManager._load_version_history')
    def test_version_history_loaded(self, mock_load, knowledge_manager):
        """Ensure manager attempts to load version history on init."""
        mock_load.return_value = []
        # Instantiate to trigger _load_version_history
        KnowledgeBaseManager(knowledge_base_path=knowledge_manager.knowledge_base_path)
        mock_load.assert_called_once()
    
    def test_handles_empty_processing_results(self, knowledge_manager):
        """Manager should not crash on empty processing input."""
        try:
            result = knowledge_manager.integrate_new_document({})
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Knowledge manager should handle empty data: {e}")
    
    def test_handles_none_input(self, knowledge_manager):
        """Manager should not crash on None input."""
        try:
            result = knowledge_manager.integrate_new_document(None)  # type: ignore[arg-type]
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Knowledge manager should handle None input: {e}")
    
    def test_filename_generation_is_stable(self, knowledge_manager):
        """Filename generation should produce deterministic, safe names."""
        pr = {
            'document_id': 'abc12345',
            'metadata': {
                'title': 'A Complex: Title/With*Chars',
                'publication_date': '2023-10-10',
                'document_type': 'Report',
            }
        }
        filename, display = knowledge_manager._generate_document_filename(pr)
        assert filename.endswith('_abc12345.md')
        assert ' ' not in filename
        assert isinstance(display, str)
    
    def test_string_representation(self, knowledge_manager):
        """__repr__/__str__ should include class name for debugging."""
        rep = repr(knowledge_manager)
        assert 'KnowledgeBaseManager' in rep
