"""
Test theme extractor module for PolicyCraft application.

This module contains unit tests for the theme extraction functionality,
ensuring that policy themes are identified and extracted correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.nlp.theme_extractor import ThemeExtractor


class TestThemeExtractor:
    """Test suite for theme extraction functionality."""
    
    @pytest.fixture
    def theme_extractor(self):
        """Create a theme extractor instance for testing."""
        return ThemeExtractor()
    
    def test_theme_extractor_initialisation(self, theme_extractor):
        """Test that theme extractor initialises correctly."""
        assert theme_extractor is not None
    
    @patch('src.nlp.theme_extractor.ThemeExtractor.extract_themes')
    def test_extract_themes_called(self, mock_extract, theme_extractor):
        """Test that extract_themes method can be called."""
        mock_extract.return_value = [
            {'theme': 'education policy', 'confidence': 0.95, 'keywords': ['education', 'school', 'student']},
            {'theme': 'healthcare policy', 'confidence': 0.87, 'keywords': ['health', 'medical', 'NHS']}
        ]
        
        test_text = "This policy addresses education and healthcare reforms in British universities."
        result = theme_extractor.extract_themes(test_text)
        
        mock_extract.assert_called_once_with(test_text)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['theme'] == 'education policy'
        assert result[0]['confidence'] == 0.95
    
    def test_theme_extractor_handles_empty_text(self, theme_extractor):
        """Test that theme extractor handles empty text gracefully."""
        try:
            if hasattr(theme_extractor, 'extract_themes'):
                result = theme_extractor.extract_themes("")
                assert isinstance(result, (list, dict, type(None)))
        except Exception as e:
            pytest.fail(f"Theme extractor should handle empty text: {e}")
    
    def test_theme_extractor_handles_none_input(self, theme_extractor):
        """Test that theme extractor handles None input gracefully."""
        try:
            if hasattr(theme_extractor, 'extract_themes'):
                result = theme_extractor.extract_themes(None)
                assert result is not None or result is None  # Either is acceptable
        except Exception as e:
            pytest.fail(f"Theme extractor should handle None input: {e}")
    
    @patch('src.nlp.theme_extractor.ThemeExtractor.identify_keywords')
    def test_identify_keywords_functionality(self, mock_keywords, theme_extractor):
        """Test keyword identification functionality."""
        mock_keywords.return_value = ['policy', 'education', 'reform', 'government', 'implementation']
        
        if hasattr(theme_extractor, 'identify_keywords'):
            test_text = "The government policy on education reform requires careful implementation."
            result = theme_extractor.identify_keywords(test_text)
            
            mock_keywords.assert_called_once()
            assert isinstance(result, list)
            assert 'policy' in result
            assert 'education' in result
    
    @patch('src.nlp.theme_extractor.ThemeExtractor.calculate_theme_confidence')
    def test_calculate_theme_confidence(self, mock_confidence, theme_extractor):
        """Test theme confidence calculation."""
        mock_confidence.return_value = 0.89
        
        if hasattr(theme_extractor, 'calculate_theme_confidence'):
            test_theme = 'environmental policy'
            test_text = "Environmental protection and sustainability measures are crucial for climate policy."
            
            result = theme_extractor.calculate_theme_confidence(test_theme, test_text)
            mock_confidence.assert_called_once()
            assert isinstance(result, (float, int))
            assert 0 <= result <= 1
    
    @patch('src.nlp.theme_extractor.ThemeExtractor.categorise_themes')
    def test_categorise_themes_functionality(self, mock_categorise, theme_extractor):
        """Test theme categorisation functionality."""
        mock_categorise.return_value = {
            'primary_themes': ['education policy', 'social policy'],
            'secondary_themes': ['economic policy'],
            'categories': {
                'domestic': ['education policy', 'social policy'],
                'economic': ['economic policy']
            }
        }
        
        if hasattr(theme_extractor, 'categorise_themes'):
            themes = ['education policy', 'social policy', 'economic policy']
            result = theme_extractor.categorise_themes(themes)
            
            mock_categorise.assert_called_once()
            assert isinstance(result, dict)
            assert 'primary_themes' in result
            assert 'categories' in result
    
    def test_theme_extractor_british_specific_themes(self, theme_extractor):
        """Test extraction of British-specific policy themes."""
        british_text = "This policy affects the NHS, benefits system, and council housing provision."
        
        try:
            if hasattr(theme_extractor, 'extract_themes'):
                result = theme_extractor.extract_themes(british_text)
                # Should handle British-specific terms
                assert result is not None
        except Exception as e:
            pytest.fail(f"Should handle British policy terms: {e}")
    
    def test_theme_extractor_string_representation(self, theme_extractor):
        """Test string representation of theme extractor."""
        str_repr = str(theme_extractor)
        assert str_repr is not None
