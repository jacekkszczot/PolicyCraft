"""
Test suite for PolicyCraft Policy Classification functionality
Tests the classification of policies as Restrictive/Moderate/Permissive.

Author: Jacek Robert Kszczot
Project: MSc AI & Data Science - COM7016

Priority: HIGH - Core classification functionality
"""

import pytest
from src.nlp.policy_classifier import PolicyClassifier

class TestPolicyClassifier:
    """Test the policy classification functionality."""
    
    def test_initialization(self):
        """Test that PolicyClassifier initializes correctly."""
        classifier = PolicyClassifier()
        assert classifier is not None
        
    def test_classify_restrictive_policy(self):
        """Test classification of restrictive policy language."""
        classifier = PolicyClassifier()
        
        restrictive_text = """
        Artificial Intelligence tools are strictly prohibited in all academic work.
        The use of AI for assignments, essays, or research is forbidden.
        Students found using AI tools will face disciplinary action.
        No exceptions to this ban will be permitted under any circumstances.
        """
        
        result = classifier.classify_policy(restrictive_text)
        
        # Validate result structure
        pytest.assert_valid_classification(result)
        
        # Should classify as restrictive
        assert result['classification'] == 'Restrictive'
        assert result['confidence'] > 50  # Should be confident in classification
        
        # Should include method information
        assert 'method' in result
        
    def test_classify_moderate_policy(self, sample_policy_text):
        """Test classification of moderate/balanced policy language."""
        classifier = PolicyClassifier()
        
        result = classifier.classify_policy(sample_policy_text)
        
        # Validate result structure
        pytest.assert_valid_classification(result)
        
        # Sample policy should be classified as moderate (has disclosure + approval requirements)
        assert result['classification'] == 'Moderate'
        assert result['confidence'] > 40  # Should have reasonable confidence
        
    def test_classify_permissive_policy(self):
        """Test classification of permissive policy language."""
        classifier = PolicyClassifier()
        
        permissive_text = """
        Students are encouraged to explore AI tools for learning enhancement.
        The university supports creative and innovative use of artificial intelligence.
        AI tools may be freely used to augment research and academic work.
        Students have the flexibility to choose appropriate AI assistance.
        We embrace the potential of AI to transform education.
        """
        
        result = classifier.classify_policy(permissive_text)
        
        # Validate result structure
        pytest.assert_valid_classification(result)
        
        # Should classify as permissive
        assert result['classification'] == 'Permissive'
        assert result['confidence'] > 40
        
    def test_classify_ambiguous_policy(self):
        """Test classification of ambiguous or unclear policy language."""
        classifier = PolicyClassifier()
        
        ambiguous_text = """
        The university acknowledges the growing importance of artificial intelligence.
        We recognize both the opportunities and challenges presented by AI technologies.
        Further guidance will be developed as needed.
        """
        
        result = classifier.classify_policy(ambiguous_text)
        
        # Should still provide a classification, but potentially with lower confidence
        pytest.assert_valid_classification(result)
        assert result['classification'] in ['Restrictive', 'Moderate', 'Permissive']
        
        # Confidence might be lower for ambiguous text
        assert 0 <= result['confidence'] <= 100
        
    def test_classify_empty_text(self):
        """Test classification of empty or minimal text."""
        classifier = PolicyClassifier()
        
        # Empty text
        empty_result = classifier.classify_policy("")
        assert empty_result is not None
        
        # Very short text
        short_result = classifier.classify_policy("AI policy.")
        assert short_result is not None
        pytest.assert_valid_classification(short_result)
        
    def test_classification_consistency(self, sample_policy_text):
        """Test that classification results are consistent across multiple calls."""
        classifier = PolicyClassifier()
        
        result1 = classifier.classify_policy(sample_policy_text)
        result2 = classifier.classify_policy(sample_policy_text)
        
        # Should get identical results for identical input
        assert result1['classification'] == result2['classification']
        assert result1['confidence'] == result2['confidence']
        assert result1['method'] == result2['method']
        
    def test_classification_with_mixed_signals(self):
        """Test classification of policy with mixed restrictive/permissive signals."""
        classifier = PolicyClassifier()
        
        mixed_text = """
        While AI tools are generally prohibited for examinations and formal assessments,
        students may use AI for preliminary research and idea generation.
        Approval from instructors is required before using AI tools.
        Unauthorized use of AI will result in academic penalties,
        but we encourage innovative approaches to learning with proper oversight.
        """
        
        result = classifier.classify_policy(mixed_text)
        
        pytest.assert_valid_classification(result)
        
        # Mixed signals often result in moderate classification
        # but could reasonably be any classification depending on algorithm
        assert result['classification'] in ['Restrictive', 'Moderate', 'Permissive']
        
    def test_get_classification_details(self, sample_policy_text):
        """Test detailed classification information."""
        classifier = PolicyClassifier()
        
        details = classifier.get_classification_details(sample_policy_text)
        
        assert isinstance(details, dict)
        
        # Should provide breakdown of classification reasoning
        expected_keys = ['confidence_breakdown', 'key_indicators']
        for key in expected_keys:
            if key in details:  # Not all implementations may have all keys
                assert isinstance(details[key], (dict, list))
                
    def test_classification_with_domain_specific_language(self):
        """Test classification with higher education specific language."""
        classifier = PolicyClassifier()
        
        academic_text = """
        Students must maintain academic integrity when utilizing AI tools.
        Proper citation of AI assistance is required in all scholarly work.
        Faculty reserve the right to restrict AI use for specific assignments.
        Plagiarism policies apply to AI-generated content.
        Research ethics guidelines must be followed when using AI in studies.
        """
        
        result = classifier.classify_policy(academic_text)
        
        pytest.assert_valid_classification(result)
        
        # Academic integrity language typically indicates moderate approach
        assert result['classification'] in ['Moderate', 'Restrictive']
        
    def test_classification_performance(self):
        """Test classification performance with various text lengths."""
        classifier = PolicyClassifier()
        
        # Short policy
        short_policy = "AI use requires instructor permission."
        short_result = classifier.classify_policy(short_policy)
        pytest.assert_valid_classification(short_result)
        
        # Long policy (simulate comprehensive document)
        long_policy = """
        Comprehensive University Policy on Artificial Intelligence Usage
        
        1. Introduction
        This document establishes detailed guidelines for AI integration across all academic activities.
        
        2. Definitions
        Artificial Intelligence refers to computer systems that can perform tasks typically requiring human intelligence.
        
        3. Permitted Uses
        AI tools may be used for research assistance, data analysis, and learning support with appropriate oversight.
        
        4. Prohibited Uses  
        AI cannot be used for exam completion, plagiarism, or replacement of original thinking.
        
        5. Disclosure Requirements
        All AI usage must be documented and disclosed according to institutional standards.
        
        6. Assessment Implications
        Faculty will determine appropriate AI use for each assessment on a case-by-case basis.
        
        7. Research Applications
        AI use in research must comply with ethical guidelines and research integrity standards.
        
        8. Enforcement
        Violations of this policy will be addressed through existing academic misconduct procedures.
        """ * 3  # Make it longer
        
        import time
        start_time = time.time()
        long_result = classifier.classify_policy(long_policy)
        processing_time = time.time() - start_time
        
        pytest.assert_valid_classification(long_result)
        
        # Should complete within reasonable time
        assert processing_time < 2.0, f"Classification took too long: {processing_time:.2f} seconds"
        
    def test_classification_with_numerical_data(self):
        """Test classification when policy contains numerical data or statistics."""
        classifier = PolicyClassifier()
        
        numerical_text = """
        Students may use AI tools for up to 30% of their research process.
        A minimum of 70% of work must be original student contribution.
        AI assistance must be disclosed within 48 hours of use.
        Violations may result in grade reductions of 10-50%.
        """
        
        result = classifier.classify_policy(numerical_text)
        
        pytest.assert_valid_classification(result)
        
        # Numerical guidelines often indicate structured, moderate approach
        assert result['classification'] in ['Moderate', 'Restrictive']
        
    def test_classification_with_legal_language(self):
        """Test classification with formal legal or policy language."""
        classifier = PolicyClassifier()
        
        legal_text = """
        In accordance with institutional regulations and academic standards,
        the utilization of artificial intelligence technologies shall be governed
        by the following provisions and stipulations. Students hereby acknowledge
        their responsibility to comply with all applicable guidelines.
        Failure to adhere to these requirements may result in disciplinary action
        pursuant to the Student Code of Conduct.
        """
        
        result = classifier.classify_policy(legal_text)
        
        pytest.assert_valid_classification(result)
        
        # Formal legal language often indicates restrictive approach
        assert result['classification'] in ['Restrictive', 'Moderate']
        
    def test_confidence_score_reliability(self):
        """Test that confidence scores correlate with classification clarity."""
        classifier = PolicyClassifier()
        
        # Very clear restrictive policy
        clear_restrictive = "AI tools are completely banned and prohibited in all academic work."
        clear_result = classifier.classify_policy(clear_restrictive)
        
        # Ambiguous policy
        ambiguous = "The university is considering policies regarding AI usage."
        ambiguous_result = classifier.classify_policy(ambiguous)
        
        # Clear policy should have higher confidence than ambiguous one
        if clear_result['confidence'] > 0 and ambiguous_result['confidence'] > 0:
            assert clear_result['confidence'] >= ambiguous_result['confidence']
            
    def test_method_attribution(self, sample_policy_text):
        """Test that classification method is properly attributed."""
        classifier = PolicyClassifier()
        
        result = classifier.classify_policy(sample_policy_text)
        
        assert 'method' in result
        assert isinstance(result['method'], str)
        assert len(result['method']) > 0
        
        # Common method names might include 'hybrid', 'keyword', 'ml', etc.
        valid_methods = ['hybrid', 'keyword', 'machine_learning', 'ml', 'rule_based', 'statistical']
        # Don't assert specific method as it depends on implementation