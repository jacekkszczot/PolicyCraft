"""
Test quality validator module for PolicyCraft application.

This module contains unit tests for the quality validation system,
ensuring that literature quality assessment functions work correctly.
"""

import pytest
from unittest.mock import patch

from src.literature.quality_validator import LiteratureQualityValidator


class TestQualityValidator:
    """Test suite for literature quality validation."""
    
    @pytest.fixture
    def quality_validator(self):
        """Create a quality validator instance for testing."""
        return LiteratureQualityValidator()
    
    def test_quality_validator_initialisation(self, quality_validator):
        """Test that quality validator initialises correctly."""
        assert quality_validator is not None
    
    @patch('src.literature.quality_validator.LiteratureQualityValidator.assess_document_quality')
    def test_assess_document_quality_called(self, mock_assess, quality_validator):
        """Test that assess_document_quality method can be called."""
        mock_assess.return_value = {
            'total_score': 0.85,
            'dimension_scores': {
                'source_credibility': 0.9,
                'content_quality': 0.8,
                'methodology_quality': 0.85,
                'policy_relevance': 0.75
            },
            'confidence_level': 'high',
            'auto_approve': True,
            'recommendation': 'Integrate document into knowledge base.'
        }
        
        result = quality_validator.assess_document_quality(
            {'title': 'Test'},
            'This is a test document with policy content.',
            ['Insight 1']
        )
        
        mock_assess.assert_called_once()
        assert result['total_score'] == 0.85
        assert result['confidence_level'] == 'high'
        assert 'dimension_scores' in result
    
    def test_source_credibility_scoring(self, quality_validator):
        """Source credibility score should be within [0,1]."""
        score = quality_validator._assess_source_credibility({
            'title': 'UNESCO Guidelines',
            'author': 'UNESCO',
            'source_url': 'https://unesco.org/policy',
            'publisher': 'UNESCO'
        })
        assert 0.0 <= score <= 1.0
    
    def test_methodology_quality_scoring(self, quality_validator):
        """Methodology quality score should be within [0,1]."""
        test_content = "This study describes methodology, data, results and validation procedures."
        score = quality_validator._assess_methodology_quality(test_content)
        assert 0.0 <= score <= 1.0
    
    def test_quality_validator_handles_empty_document(self, quality_validator):
        """Validator should handle empty documents gracefully."""
        try:
            result = quality_validator.assess_document_quality({}, "", [])
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Quality validator should handle empty documents: {e}")
    
    def test_quality_validator_handles_none_input(self, quality_validator):
        """Validator should handle None input gracefully."""
        try:
            result = quality_validator.assess_document_quality(None, None, None)  # type: ignore[arg-type]
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Quality validator should handle None input: {e}")
    
    def test_overall_score_with_real_assessment(self, quality_validator):
        """End-to-end assessment should yield a total score in [0,1]."""
        meta = {'title': 'Sample', 'author': 'Univ.', 'source_url': 'https://example.org'}
        result = quality_validator.assess_document_quality(meta, "policy research methodology data", ["insight"])
        assert 'total_score' in result
        assert 0.0 <= result['total_score'] <= 1.0
    
    def test_quality_validator_string_representation(self, quality_validator):
        """Test string representation of quality validator."""
        assert str(quality_validator) is not None
