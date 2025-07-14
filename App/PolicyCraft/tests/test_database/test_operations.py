"""
Tests for database operations module.
Tests JSON storage functionality.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from src.database.operations import DatabaseOperations


class TestDatabaseOperations:
    """Test database operations functionality."""
    
    @pytest.fixture
    def temp_storage_file(self):
        """Create temporary storage file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                'documents': [],
                'analyses': [],
                'recommendations': []
            }, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @pytest.fixture
    def db_ops(self, temp_storage_file):
        """Create DatabaseOperations instance with temporary storage."""
        with patch.object(DatabaseOperations, '__init__', lambda x: None):
            db = DatabaseOperations()
            db.storage = {
                'documents': [],
                'analyses': [],
                'recommendations': []
            }
            db.storage_file = temp_storage_file
            return db
    
    def test_store_document(self, db_ops):
        """Test document storage functionality."""
        doc_id = db_ops.store_document(
            user_id=1,
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            extracted_text='Sample text content',
            metadata={'source': 'test'}
        )
        
        assert doc_id.startswith('doc_')
        assert len(db_ops.storage['documents']) == 1
        
        doc = db_ops.storage['documents'][0]
        assert doc['user_id'] == 1
        assert doc['filename'] == 'test.pdf'
        assert doc['extracted_text'] == 'Sample text content'
        assert doc['metadata']['source'] == 'test'

    def test_store_user_analysis_results(self, db_ops):
        """Test analysis results storage."""
        themes = [
            {'name': 'AI Ethics', 'score': 5.5, 'confidence': 55},
            {'name': 'Academic Integrity', 'score': 3.5, 'confidence': 35}
        ]
        classification = {
            'classification': 'Moderate',
            'confidence': 75,
            'method': 'hybrid'
        }
        
        analysis_id = db_ops.store_user_analysis_results(
            user_id=1,
            filename='test_policy.pdf',
            original_text='Original policy text',
            cleaned_text='Cleaned policy text',
            themes=themes,
            classification=classification
        )
        
        assert analysis_id.startswith('analysis_')
        assert len(db_ops.storage['analyses']) == 1
        
        analysis = db_ops.storage['analyses'][0]
        assert analysis['user_id'] == 1
        assert analysis['filename'] == 'test_policy.pdf'
        assert len(analysis['themes']) == 2
        assert analysis['classification']['classification'] == 'Moderate'

    def test_get_user_analyses(self, db_ops):
        """Test retrieving user analyses."""
        # Store test analyses
        for i in range(3):
            db_ops.store_user_analysis_results(
                user_id=1,
                filename=f'test_{i}.pdf',
                original_text=f'Text {i}',
                cleaned_text=f'Clean text {i}',
                themes=[],
                classification={'classification': 'Moderate', 'confidence': 75}
            )
        
        user_analyses = db_ops.get_user_analyses(user_id=1)
        assert len(user_analyses) == 3
        assert all(analysis['user_id'] == 1 for analysis in user_analyses)

    def test_get_analysis_statistics(self, db_ops):
        """Test analysis statistics generation."""
        # Test with no analyses
        stats = db_ops.get_analysis_statistics()
        assert stats['total_analyses'] == 0
        
        # Add test analyses
        themes = [{'name': 'Theme_1', 'score': 1}]
        db_ops.store_user_analysis_results(
            user_id=1,
            filename='test.pdf',
            original_text='Text',
            cleaned_text='Clean text',
            themes=themes,
            classification={'classification': 'Moderate', 'confidence': 75}
        )
        
        stats = db_ops.get_analysis_statistics()
        assert stats['total_analyses'] == 1
        assert stats['avg_confidence'] == 75

    def test_get_storage_info(self, db_ops):
        """Test storage information retrieval."""
        db_ops.storage['documents'] = [{'id': 1}, {'id': 2}]
        db_ops.storage['analyses'] = [{'id': 1}]
        
        info = db_ops.get_storage_info()
        
        assert info['storage_type'] == 'JSON'
        assert info['total_documents'] == 2
        assert info['total_analyses'] == 1

    def test_get_user_analysis_by_id(self, db_ops):
        """Test retrieving specific analysis by ID."""
        analysis_id = db_ops.store_user_analysis_results(
            user_id=1,
            filename='test.pdf',
            original_text='Text',
            cleaned_text='Clean text',
            themes=[],
            classification={'classification': 'Moderate', 'confidence': 75}
        )
        
        # Test successful retrieval
        analysis = db_ops.get_user_analysis_by_id(user_id=1, analysis_id=analysis_id)
        assert analysis is not None
        assert analysis['_id'] == analysis_id
        
        # Test retrieval with wrong user ID
        analysis = db_ops.get_user_analysis_by_id(user_id=2, analysis_id=analysis_id)
        assert analysis is None

    def test_store_recommendations(self, db_ops):
        """Test recommendation storage."""
        recommendations = [
            {'title': 'Improve Transparency', 'priority': 'high'}
        ]
        
        rec_id = db_ops.store_recommendations(
            user_id=1,
            analysis_id='analysis_123',
            recommendations=recommendations
        )
        
        assert rec_id.startswith('rec_')
        assert len(db_ops.storage['recommendations']) == 1

    def test_initialization_and_storage(self):
        """Test initialization and file operations."""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs'), \
             patch.object(DatabaseOperations, '_save_storage'):
            
            db = DatabaseOperations()
            assert hasattr(db, 'storage')
            assert 'documents' in db.storage
