"""
Test suite for PolicyCraft Text Processing functionality
Tests PDF/DOCX extraction, text cleaning, and statistics generation.

Author: Jacek Robert Kszczot  
Project: MSc AI & Data Science - COM7016

Priority: HIGH - Foundation for all NLP processing
"""

import pytest
import tempfile
import os
from src.nlp.text_processor import TextProcessor

class TestTextProcessor:
    """Test the text processing functionality."""
    
    def test_initialization(self):
        """Test that TextProcessor initializes correctly."""
        processor = TextProcessor()
        assert processor is not None
        # Test that any required attributes are set
        
    def test_extract_text_from_txt_file(self, temp_policy_file):
        """Test text extraction from plain text files."""
        processor = TextProcessor()
        
        extracted_text = processor.extract_text_from_file(temp_policy_file)
        
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0
        assert "University AI Policy" in extracted_text
        assert "Disclosure Requirements" in extracted_text
        
    def test_extract_text_from_nonexistent_file(self):
        """Test handling of nonexistent files."""
        processor = TextProcessor()
        
        result = processor.extract_text_from_file("nonexistent_file.txt")
        
        # Should return empty string or None for nonexistent files
        assert result is None or result == ""
        
    def test_extract_text_from_pdf_file(self, temp_pdf_file):
        """Test text extraction from PDF files."""
        processor = TextProcessor()
        
        # Note: This test uses a minimal PDF created in conftest.py
        # In a real implementation, you'd want a proper PDF with text content
        extracted_text = processor.extract_text_from_file(temp_pdf_file)
        
        # For the minimal PDF, we might get empty or minimal content
        assert extracted_text is None or extracted_text == "" or isinstance(extracted_text, str)
        assert isinstance(extracted_text, str)
        
    def test_extract_text_from_unsupported_format(self):
        """Test handling of unsupported file formats."""
        processor = TextProcessor()
        
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            result = processor.extract_text_from_file(temp_path)
            
            # Should handle gracefully - return None/empty or raise appropriate exception
            assert result is None or result == ""
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_clean_text_basic_functionality(self, sample_policy_text):
        """Test basic text cleaning functionality."""
        processor = TextProcessor()
        
        # Add some noise to the sample text
        noisy_text = f"   \n\n{sample_policy_text}\n\n   \t\t  "
        
        cleaned_text = processor.clean_text(noisy_text)
        
        assert isinstance(cleaned_text, str)
        assert len(cleaned_text) > 0
        assert len(cleaned_text) <= len(noisy_text)  # Should be same or shorter
        
        # Should remove leading/trailing whitespace
        assert not cleaned_text.startswith(" ")
        assert not cleaned_text.endswith(" ")
        
        # Should preserve meaningful content
        assert "University AI Policy" in cleaned_text
        assert "Disclosure Requirements" in cleaned_text

    def test_clean_text_removes_extra_whitespace(self):
        """Test that text cleaning removes excessive whitespace."""
        processor = TextProcessor()
        
        text_with_extra_spaces = "This  has    too     many      spaces."
        cleaned = processor.clean_text(text_with_extra_spaces)
        
        # Should normalize whitespace
        assert "  " not in cleaned  # No double spaces
        assert "This has too many spaces." in cleaned or "This has" in cleaned

    def test_clean_text_handles_special_characters(self):
        """Test text cleaning with special characters and encoding."""
        processor = TextProcessor()
        
        text_with_special = "AI policy — includes 'smart quotes' and bullet points • item 1"
        cleaned = processor.clean_text(text_with_special)
        
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
        # Should handle special characters gracefully

    def test_clean_text_empty_input(self):
        """Test text cleaning with empty or None input."""
        processor = TextProcessor()
        
        # Test empty string
        assert processor.clean_text("") == ""
        
        # Test None input
        result = processor.clean_text(None)
        assert result is None or result == ""
        
        # Test whitespace-only string
        whitespace_only = "   \n\t   "
        cleaned = processor.clean_text(whitespace_only)
        assert cleaned == "" or cleaned.strip() == ""

    def test_get_text_statistics_comprehensive(self, sample_policy_text):
        """Test comprehensive text statistics generation."""
        processor = TextProcessor()
        
        stats = processor.get_text_statistics(sample_policy_text)
        
        assert isinstance(stats, dict)
        
        # Check required statistics fields
        required_fields = ['word_count', 'character_count', 'paragraph_count', 'sentence_count']
        for field in required_fields:
            assert field in stats, f"Statistics should include {field}"
            assert isinstance(stats[field], int), f"{field} should be an integer"
            assert stats[field] >= 0, f"{field} should be non-negative"
        
        # Sanity checks on values
        assert stats['character_count'] > stats['word_count'], "Character count should exceed word count"
        assert stats['word_count'] > 0, "Should count words in sample text"
        assert stats['sentence_count'] > 0, "Should count sentences in sample text"
        assert stats['paragraph_count'] > 0, "Should count paragraphs in sample text"

    def test_get_text_statistics_edge_cases(self):
        """Test text statistics with edge case inputs."""
        processor = TextProcessor()
        
        # Empty text
        empty_stats = processor.get_text_statistics("")
        assert all(count == 0 for count in empty_stats.values())
        
        # Single word
        single_word_stats = processor.get_text_statistics("AI")
        assert single_word_stats['word_count'] >= 0
        assert single_word_stats['character_count'] == 2
        
        # Single sentence
        single_sentence = "This is a test sentence."
        single_stats = processor.get_text_statistics(single_sentence)
        assert single_stats['sentence_count'] == 1
        assert single_stats['word_count'] >= 3  # Tokenizer dependent

    def test_get_text_statistics_consistency(self, sample_policy_text):
        """Test that statistics are consistent across multiple calls."""
        processor = TextProcessor()
        
        stats1 = processor.get_text_statistics(sample_policy_text)
        stats2 = processor.get_text_statistics(sample_policy_text)
        
        # Should get identical results
        assert stats1 == stats2

    def test_extract_and_clean_workflow(self, temp_policy_file):
        """Test the complete extract -> clean workflow."""
        processor = TextProcessor()
        
        # Extract text
        extracted = processor.extract_text_from_file(temp_policy_file)
        assert extracted is not None
        assert len(extracted) > 0
        
        # Clean extracted text
        cleaned = processor.clean_text(extracted)
        assert cleaned is not None
        assert len(cleaned) > 0
        
        # Get statistics on cleaned text
        stats = processor.get_text_statistics(cleaned)
        assert stats['word_count'] > 0
        assert stats['character_count'] > 0

    def test_large_text_handling(self):
        """Test processing of large text documents."""
        processor = TextProcessor()
        
        # Create a large text (simulate large policy document)
        large_text = "AI policy statement. " * 1000  # 1000 repetitions
        
        # Should handle large text without issues
        cleaned = processor.clean_text(large_text)
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
        
        stats = processor.get_text_statistics(cleaned)
        assert stats['word_count'] > 1000  # Should count many words
        assert stats['sentence_count'] > 500  # Should count many sentences

    def test_multilingual_content_handling(self):
        """Test handling of non-English content (if applicable)."""
        processor = TextProcessor()
        
        # Test with some non-English characters
        multilingual_text = "AI policy règlement política 政策"
        
        cleaned = processor.clean_text(multilingual_text)
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
        
        stats = processor.get_text_statistics(cleaned)
        assert stats['word_count'] > 0

    def test_text_processor_error_handling(self):
        """Test error handling in text processor methods."""
        processor = TextProcessor()
        
        # Test with invalid file path
        invalid_path = "/nonexistent/path/to/file.pdf"
        result = processor.extract_text_from_file(invalid_path)
        
        # Should handle gracefully without crashing
        assert result is None or result == ""

    def test_different_file_encodings(self):
        """Test handling of different text file encodings."""
        processor = TextProcessor()
        
        # Create a file with UTF-8 content
        test_content = "AI policy with special chars: café, naïve, résumé"
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            extracted = processor.extract_text_from_file(temp_path)
            assert isinstance(extracted, str)
            assert "café" in extracted or "caf" in extracted  # Should handle special chars
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_performance_with_realistic_document_size(self):
        """Test performance with realistic policy document size."""
        processor = TextProcessor()
        
        # Simulate realistic policy document (5-10 pages, ~2000-4000 words)
        realistic_policy = """
        University Artificial Intelligence Policy
        
        1. Introduction and Purpose
        This policy establishes comprehensive guidelines for the responsible use of artificial intelligence 
        technologies within our academic institution. The purpose is to ensure ethical, transparent, 
        and educationally beneficial integration of AI tools while maintaining academic integrity.
        
        2. Scope and Applicability  
        This policy applies to all students, faculty, staff, and researchers within the university
        who utilize AI technologies for academic, research, or administrative purposes.
        """ * 100  # Multiply to create substantial document
        
        import time
        start_time = time.time()
        
        cleaned = processor.clean_text(realistic_policy)
        stats = processor.get_text_statistics(cleaned)
        
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (< 5 seconds for large doc)
        assert processing_time < 5.0, f"Processing took too long: {processing_time:.2f} seconds"
        
        # Should produce meaningful results
        assert stats['word_count'] > 1000
        assert len(cleaned) > 5000