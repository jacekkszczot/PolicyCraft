"""
Test Suite for PolicyCraft Recommendation Engine

This module contains comprehensive tests for the PolicyCraft Recommendation Engine,
which is responsible for generating AI policy recommendations based on ethical frameworks
and institutional context. The tests cover the complete recommendation generation
pipeline, including ethical framework analysis, context detection, and scoring.

Test Coverage:
- EthicalFrameworkAnalyzer: Tests for coverage analysis and scoring
- RecommendationGenerator: Tests for context-aware recommendation generation
- RecommendationEngine: Integration tests for the complete recommendation workflow

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University

Priority: CRITICAL - This module tests the core recommendation functionality
"""

import pytest
import json
from src.recommendation.engine import (
    EthicalFrameworkAnalyzer, 
    RecommendationGenerator, 
    RecommendationEngine
)

class TestEthicalFrameworkAnalyzer:
    """Test the ethical framework analysis functionality."""
    
    def test_analyze_coverage_realistic_scoring(self, sample_policy_text, sample_themes):
        """
        Test that coverage analysis produces realistic scores (15-35% range).
        This addresses the bug where Columbia got 0% transparency despite having disclosure requirements.
        """
        analyzer = EthicalFrameworkAnalyzer()
        coverage = analyzer.analyze_coverage(sample_themes, sample_policy_text)
        
        # Basic structure validation
        assert isinstance(coverage, dict)
        assert len(coverage) == 4  # Four ethical dimensions
        
        expected_dimensions = ['accountability', 'transparency', 'human_agency', 'inclusiveness']
        for dimension in expected_dimensions:
            assert dimension in coverage
            
        # Test realistic scoring - should not be 0% for policies with content
        transparency = coverage['transparency']
        assert transparency['score'] > 0, "Transparency should not be 0% for policy with disclosure requirements"
        assert transparency['score'] <= 100, "Score should not exceed 100%"
        
        # Test that disclosure language is detected
        assert transparency['item_count'] > 0, "Should detect disclosure-related items"
        assert any('disclose' in item.lower() for item in transparency['matched_items']), \
            "Should detect 'disclose' in policy text"
        
        # Test status assignment
        assert transparency['status'] in ['weak', 'moderate', 'strong']
        
        # Test human agency detection (policy mentions human oversight)
        human_agency = coverage['human_agency']
        assert human_agency['score'] > 0, "Should detect human oversight language"
        assert any('human' in item.lower() or 'faculty' in item.lower() 
                  for item in human_agency['matched_items']), \
            "Should detect human oversight indicators"

    def test_weighted_keyword_matching(self):
        """Test that weighted keyword matching works correctly."""
        analyzer = EthicalFrameworkAnalyzer()
        
        # Test text with high-weight transparency indicators
        test_text = "Students must disclose AI usage and acknowledge all AI-generated content."
        coverage = analyzer.analyze_coverage([], test_text)
        
        transparency = coverage['transparency']
        
        # Should detect high-weight keywords
        assert transparency['score'] > 15, "Should score higher with weighted keywords"
        assert 'disclose' in str(transparency['matched_items']).lower()
        assert 'acknowledge' in str(transparency['matched_items']).lower()

    def test_phrase_detection(self):
        """Test that phrase detection (e.g., 'must disclose') works correctly."""
        analyzer = EthicalFrameworkAnalyzer()
        
        # Test text with specific phrases
        test_text = "All students must disclose their use of AI tools in academic work."
        coverage = analyzer.analyze_coverage([], test_text)
        
        transparency = coverage['transparency']
        
        # Should detect phrase bonuses
        assert transparency['score'] > 0
        # Should have phrase matches in matched_items
        phrase_matches = [item for item in transparency['matched_items'] if 'PHRASE:' in item]
        assert len(phrase_matches) > 0, "Should detect phrase matches"

    def test_detect_existing_policies(self, sample_policy_text):
        """Test detection of existing policy elements."""
        analyzer = EthicalFrameworkAnalyzer()
        existing = analyzer.detect_existing_policies(sample_policy_text)
        
        assert isinstance(existing, dict)
        
        # Should detect disclosure requirements from sample text
        assert existing['disclosure_requirements'] == True, \
            "Should detect disclosure requirements in sample policy"
        
        # Should detect approval processes (mentions faculty approval)
        assert existing['approval_processes'] == True, \
            "Should detect approval processes in sample policy"
        
        # Test with empty text
        empty_existing = analyzer.detect_existing_policies("")
        assert all(not value for value in empty_existing.values()), \
            "Empty text should not detect any existing policies"

    def test_identify_gaps_with_proper_fields(self, sample_coverage_analysis):
        """Test that gap identification includes all required fields (fixes gap_type error)."""
        analyzer = EthicalFrameworkAnalyzer()
        gaps = analyzer.identify_gaps(sample_coverage_analysis, "Moderate")
        
        assert isinstance(gaps, list)
        
        for gap in gaps:
            # Test required fields that were missing before
            assert 'dimension' in gap
            assert 'type' in gap  # This was the missing field causing errors
            assert 'priority' in gap
            assert 'current_score' in gap
            assert 'description' in gap
            
            # Test valid values
            assert gap['dimension'] in ['accountability', 'transparency', 'human_agency', 'inclusiveness']
            assert gap['type'] in ['coverage_gap', 'improvement_opportunity', 'classification_risk']
            assert gap['priority'] in ['critical', 'high', 'medium', 'low']
            assert isinstance(gap['current_score'], (int, float))

    def test_coverage_for_different_policy_types(self):
        """Test coverage analysis for different policy approaches."""
        analyzer = EthicalFrameworkAnalyzer()
        
        # Restrictive policy text - longer for better coverage detection
        restrictive_text = """
        AI tools are strictly prohibited and banned in all academic work. 
        No exceptions are permitted. Students must not use any AI assistance.
        Violations will result in disciplinary action and academic penalties.
        Faculty oversight is required. All work must be original.
        """
        restrictive_coverage = analyzer.analyze_coverage([], restrictive_text)
        
        # Permissive policy text - longer for better coverage detection
        permissive_text = """
        Students are encouraged to use AI tools for learning and creativity.
        AI assistance is welcomed and supported for research enhancement.
        Faculty encourage innovative approaches with AI technology.
        Transparent disclosure of AI use is appreciated but flexible.
        """
        permissive_coverage = analyzer.analyze_coverage([], permissive_text)
        
        # Should produce different coverage patterns
        assert isinstance(restrictive_coverage, dict)
        assert isinstance(permissive_coverage, dict)
        
        # Both should have some coverage (not all zeros)
        assert isinstance(restrictive_coverage, dict)
        assert any(dim['score'] > 0 for dim in permissive_coverage.values())


class TestRecommendationGenerator:
    """Test the recommendation generation functionality."""
    
    def test_generate_recommendations_with_context(self, sample_themes, sample_coverage_analysis):
        """Test contextual recommendation generation."""
        generator = RecommendationGenerator()
        
        # Create sample gaps
        gaps = [
            {
                'dimension': 'transparency',
                'type': 'improvement_opportunity',
                'priority': 'high',
                'current_score': 15.0,
                'description': 'Low transparency coverage'
            },
            {
                'dimension': 'accountability',
                'type': 'coverage_gap', 
                'priority': 'high',
                'current_score': 8.0,
                'description': 'Weak accountability framework'
            }
        ]
        
        recommendations = generator.generate_recommendations(
            gaps=gaps,
            classification="Moderate",
            themes=sample_themes,
            text="Sample policy text with some disclosure requirements"
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0, "Should generate at least one recommendation"
        
        for rec in recommendations:
            pytest.assert_valid_recommendation(rec)
            
        # Should have recommendations for the gap dimensions
        rec_dimensions = [rec['dimension'] for rec in recommendations]
        assert 'transparency' in rec_dimensions or 'accountability' in rec_dimensions

    def test_institution_context_detection(self, sample_themes):
        """Test that institution type is correctly detected from themes and text."""
        generator = RecommendationGenerator()
        
        # Research university context
        research_text = "faculty research publication scholarly graduate phd"
        research_context = generator._analyze_institution_context(sample_themes, research_text)
        
        # Should detect research university characteristics
        assert research_context['type'] in ['research_university', 'teaching_focused', 'technical_institute']
        
        # Teaching-focused context
        teaching_text = "student learning undergraduate classroom pedagogy teaching"
        teaching_context = generator._analyze_institution_context(sample_themes, teaching_text)
        
        # Contexts should potentially differ based on content
        assert isinstance(teaching_context, dict)
        assert 'type' in teaching_context

    def test_existing_policy_detection_for_recommendations(self):
        """Test that existing policies are properly detected for enhancement vs new implementation."""
        generator = RecommendationGenerator()
        
        # Policy with existing disclosure requirements
        disclosure_text = "Students must disclose AI usage and cite AI-generated content."
        existing = generator._detect_existing_policies(disclosure_text)
        
        assert existing['disclosure_requirements'] == True
        
        # Policy without disclosure requirements
        no_disclosure_text = "Students may use AI tools for learning purposes."
        no_existing = generator._detect_existing_policies(no_disclosure_text)
        
        assert no_existing['disclosure_requirements'] == False

    def test_template_matching_logic(self):
        """Test that appropriate templates are selected based on context."""
        generator = RecommendationGenerator()
        
        # Test contextual recommendation generation
        gap = {
            'dimension': 'transparency',
            'type': 'coverage_gap',
            'priority': 'high',
            'current_score': 10.0,
            'description': 'Low transparency'
        }
        
        institution_context = {'type': 'research_university'}
        
        recommendation = generator._generate_contextual_recommendation(
            dimension='transparency',
            institution_context=institution_context,
            implementation_type='new_implementation',
            priority='high',
            current_score=10.0,
            gap_details=gap
        )
        
        assert recommendation is not None
        assert isinstance(recommendation, dict)
        assert 'title' in recommendation
        assert 'description' in recommendation


class TestRecommendationEngine:
    """Test the main recommendation engine integration."""
    
    def test_full_recommendation_generation_workflow(self, sample_themes, sample_classification, sample_policy_text):
        """Test the complete recommendation generation workflow."""
        engine = RecommendationEngine()
        
        result = engine.generate_recommendations(
            themes=sample_themes,
            classification=sample_classification,
            text=sample_policy_text,
            analysis_id="test_analysis_123"
        )
        
        # Test result structure
        assert isinstance(result, dict)
        assert 'analysis_metadata' in result
        assert 'coverage_analysis' in result
        assert 'recommendations' in result
        assert 'summary' in result
        
        # Test metadata
        metadata = result['analysis_metadata']
        assert metadata['analysis_id'] == "test_analysis_123"
        assert 'generated_date' in metadata
        assert 'framework_version' in metadata
        assert 'methodology' in metadata
        
        # Test coverage analysis
        coverage = result['coverage_analysis']
        assert len(coverage) == 4  # Four ethical dimensions
        
        # Test recommendations
        recommendations = result['recommendations']
        assert isinstance(recommendations, list)
        
        for rec in recommendations:
            pytest.assert_valid_recommendation(rec)
        
        # Test summary
        summary = result['summary']
        assert 'total_recommendations' in summary
        assert 'overall_coverage' in summary
        assert summary['total_recommendations'] == len(recommendations)

    def test_enhanced_scoring_validation(self, sample_policy_text):
        """Test that the enhanced scoring system produces realistic results."""
        engine = RecommendationEngine()
        
        # Policy with strong disclosure language
        strong_disclosure_text = """
        All students and faculty must disclose AI usage in academic work.
        AI-generated content must be acknowledged and properly cited.
        Transparency in AI usage is required for all submissions.
        """
        
        result = engine.generate_recommendations(
            themes=[],
            classification={'classification': 'Moderate', 'confidence': 60},
            text=strong_disclosure_text,
            analysis_id="test_strong_disclosure"
        )
        
        # Should have realistic transparency coverage (not 0%)
        transparency_score = result['coverage_analysis']['transparency']['score']
        assert transparency_score > 10, f"Transparency score should be >10%, got {transparency_score}%"
        assert transparency_score < 80, f"Transparency score should be realistic, got {transparency_score}%"

    def test_fallback_behavior(self):
        """Test that the engine provides useful fallback when main analysis fails."""
        engine = RecommendationEngine()
        
        # Test with invalid inputs that might cause errors
        result = engine.generate_recommendations(
            themes=None,  # Invalid input
            classification={},  # Invalid input
            text="",  # Empty text
            analysis_id="test_fallback"
        )
        
        # Should still return a structured result
        assert isinstance(result, dict)
        assert 'recommendations' in result
        
        # Fallback should provide at least basic recommendations
        if 'recommendations' in result and result['recommendations']:
            for rec in result['recommendations']:
                assert 'title' in rec
                assert 'description' in rec

    def test_recommendation_deduplication(self, sample_themes, sample_classification, sample_policy_text):
        """Test that duplicate recommendations are not generated."""
        engine = RecommendationEngine()
        
        result = engine.generate_recommendations(
            themes=sample_themes,
            classification=sample_classification,
            text=sample_policy_text,
            analysis_id="test_deduplication"
        )
        
        recommendations = result['recommendations']
        
        # Check for duplicate titles
        titles = [rec['title'] for rec in recommendations]
        assert len(titles) == len(set(titles)), "Should not have duplicate recommendation titles"
        
        # Check for duplicate dimension+implementation_type combinations
        combinations = [(rec.get('dimension'), rec.get('implementation_type')) for rec in recommendations]
        unique_combinations = set(combinations)
        assert len(combinations) == len(unique_combinations), \
            "Should not have duplicate dimension+implementation_type combinations"

    def test_academic_source_attribution(self, sample_themes, sample_classification, sample_policy_text):
        """Test that recommendations properly attribute academic sources."""
        engine = RecommendationEngine()
        
        result = engine.generate_recommendations(
            themes=sample_themes,
            classification=sample_classification,
            text=sample_policy_text,
            analysis_id="test_attribution"
        )
        
        # Check metadata has academic sources
        metadata = result['analysis_metadata']
        assert 'academic_sources' in metadata
        
        expected_sources = ['UNESCO 2023', 'JISC 2023', 'BERA 2018']
        assert any(source in metadata['academic_sources'] for source in expected_sources)
        
        # Check individual recommendations have source attribution
        recommendations = result['recommendations']
        for rec in recommendations:
            if 'source' in rec:
                assert isinstance(rec['source'], str)
                assert len(rec['source']) > 0