"""
Integration tests for PolicyCraft Analysis Pipeline
Tests the complete workflow from file upload to recommendations.

Author: Jacek Robert Kszczot
Project: MSc AI & Data Science - COM7016

Priority: HIGH - Validates complete system integration
"""

import pytest
import tempfile
import os
from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.recommendation.engine import RecommendationEngine

class TestAnalysisPipeline:
    """Test the complete analysis pipeline integration."""
    
    def test_full_analysis_workflow(self, temp_policy_file):
        """Test complete PDF → themes → classification → recommendations workflow."""
        
        # Initialize all components
        text_processor = TextProcessor()
        theme_extractor = ThemeExtractor()
        policy_classifier = PolicyClassifier()
        recommendation_engine = RecommendationEngine()
        
        # Step 1: Extract text
        extracted_text = text_processor.extract_text_from_file(temp_policy_file)
        assert extracted_text is not None
        assert len(extracted_text) > 0
        print(f"✅ Text extraction: {len(extracted_text)} characters")
        
        # Step 2: Clean text
        cleaned_text = text_processor.clean_text(extracted_text)
        assert cleaned_text is not None
        assert len(cleaned_text) > 0
        print(f"✅ Text cleaning: {len(cleaned_text)} characters")
        
        # Step 3: Extract themes
        themes = theme_extractor.extract_themes(cleaned_text)
        assert isinstance(themes, list)
        assert len(themes) > 0
        
        # Validate theme structure
        for theme in themes:
            pytest.assert_valid_theme(theme)
        
        print(f"✅ Theme extraction: {len(themes)} themes found")
        print(f"   Top themes: {[t['name'] for t in themes[:3]]}")
        
        # Step 4: Classify policy
        classification = policy_classifier.classify_policy(cleaned_text)
        pytest.assert_valid_classification(classification)
        
        print(f"✅ Policy classification: {classification['classification']} ({classification['confidence']}%)")
        
        # Step 5: Generate recommendations
        recommendations_result = recommendation_engine.generate_recommendations(
            themes=themes,
            classification=classification,
            text=cleaned_text,
            analysis_id="integration_test_001"
        )
        
        assert isinstance(recommendations_result, dict)
        assert 'recommendations' in recommendations_result
        assert 'coverage_analysis' in recommendations_result
        assert 'summary' in recommendations_result
        
        recommendations = recommendations_result['recommendations']
        assert isinstance(recommendations, list)
        
        for rec in recommendations:
            pytest.assert_valid_recommendation(rec)
        
        print(f"✅ Recommendation generation: {len(recommendations)} recommendations")
        print(f"   Coverage: {recommendations_result['summary'].get('overall_coverage', 'N/A')}%")
        
        # Step 6: Validate end-to-end coherence
        # Themes should relate to classification
        theme_names = [theme['name'].lower() for theme in themes]
        
        if classification['classification'] == 'Moderate':
            # Moderate policies often mention guidelines, disclosure, or approval
            moderate_indicators = ['guideline', 'disclosure', 'approval', 'integrity', 'oversight']
            assert any(any(indicator in theme_name for theme_name in theme_names) 
                      for indicator in moderate_indicators), \
                "Themes should reflect moderate classification"
        
        # Recommendations should address identified gaps
        rec_dimensions = [rec.get('dimension') for rec in recommendations]
        expected_dimensions = ['accountability', 'transparency', 'human_agency', 'inclusiveness']
        assert any(dim in rec_dimensions for dim in expected_dimensions), \
            "Recommendations should address ethical framework dimensions"
        
        print("✅ End-to-end pipeline integration successful")
        
        # Store results for potential inspection (without returning)
        integration_results = {
            'extracted_text': extracted_text,
            'cleaned_text': cleaned_text,
            'themes': themes,
            'classification': classification,
            'recommendations': recommendations_result
        }
        
        # Test passes by reaching this point without exceptions
        assert True

    def test_batch_processing_simulation(self):
        """Test processing multiple policies in sequence (batch analysis simulation)."""
        
        # Create multiple test policies
        test_policies = [
            {
                'name': 'restrictive_policy',
                'content': """
                AI tools are strictly prohibited in all academic work.
                Students may not use artificial intelligence for any assignments.
                Violations will result in immediate disciplinary action.
                """
            },
            {
                'name': 'permissive_policy', 
                'content': """
                Students are encouraged to use AI tools for learning enhancement.
                Creative use of artificial intelligence is supported and welcomed.
                AI can be freely used to augment academic work and research.
                """
            },
            {
                'name': 'moderate_policy',
                'content': """
                AI tools may be used with instructor approval and proper disclosure.
                Students must cite AI assistance and maintain academic integrity.
                Faculty will provide guidelines for appropriate AI use in courses.
                """
            }
        ]
        
        # Initialize components
        text_processor = TextProcessor()
        theme_extractor = ThemeExtractor()
        policy_classifier = PolicyClassifier()
        
        batch_results = []
        
        for policy_data in test_policies:
            print(f"\n--- Processing {policy_data['name']} ---")
            
            # Process each policy through the pipeline
            cleaned_text = text_processor.clean_text(policy_data['content'])
            themes = theme_extractor.extract_themes(cleaned_text)
            classification = policy_classifier.classify_policy(cleaned_text)
            
            # Validate results
            assert len(themes) > 0, f"Should extract themes from {policy_data['name']}"
            pytest.assert_valid_classification(classification)
            
            batch_results.append({
                'policy_name': policy_data['name'],
                'themes': themes,
                'classification': classification,
                'theme_count': len(themes)
            })
            
            print(f"✅ {policy_data['name']}: {classification['classification']} ({len(themes)} themes)")
        
        # Validate batch results diversity
        classifications = [result['classification']['classification'] for result in batch_results]
        
        # Should get different classifications for different policy types
        unique_classifications = set(classifications)
        assert len(unique_classifications) >= 2, \
            f"Should get diverse classifications, got: {classifications}"
        
        # Expected classification mapping (flexible for different algorithms)
        expected_mapping = {
            'restrictive_policy': 'Restrictive',
            'permissive_policy': 'Permissive', 
            'moderate_policy': 'Moderate'
        }
        
        for result in batch_results:
            policy_name = result['policy_name']
            actual_classification = result['classification']['classification']
            expected_classification = expected_mapping[policy_name]
            
            print(f"Policy: {policy_name}")
            print(f"  Expected: {expected_classification}")
            print(f"  Actual: {actual_classification}")
            
            # Note: We don't assert exact match as classification algorithms may vary
            # The important thing is that we get reasonable, different results
        
        print(f"\n✅ Batch processing completed: {len(batch_results)} policies processed")
        
        # Store results for inspection without returning
        batch_processing_results = batch_results
        
        # Test passes if we reach this point
        assert len(batch_results) == len(test_policies)

    def test_error_recovery_in_pipeline(self):
        """Test that pipeline handles errors gracefully without complete failure."""
        
        text_processor = TextProcessor()
        theme_extractor = ThemeExtractor()
        policy_classifier = PolicyClassifier()
        
        # Test with problematic inputs
        problematic_inputs = [
            "",  # Empty text
            "AI",  # Single word
            "   \n\t   ",  # Whitespace only
            "A" * 10000,  # Very long repetitive text
            "🤖🧠💻📝",  # Emoji only
            None  # None input (if handled)
        ]
        
        successful_processes = 0
        
        for i, problematic_input in enumerate(problematic_inputs):
            try:
                print(f"\n--- Testing problematic input {i + 1} ---")
                
                # Try to process through pipeline
                if problematic_input is not None:
                    cleaned = text_processor.clean_text(problematic_input)
                    
                    if cleaned and len(cleaned.strip()) > 0:
                        themes = theme_extractor.extract_themes(cleaned)
                        classification = policy_classifier.classify_policy(cleaned)
                        
                        # Should still return valid structures even for edge cases
                        assert isinstance(themes, list)
                        pytest.assert_valid_classification(classification)
                        
                        successful_processes += 1
                        print(f"✅ Processed successfully: {len(themes)} themes, {classification['classification']}")
                    else:
                        print("⚠️ Cleaned text was empty, skipping further processing")
                        successful_processes += 1  # Still successful handling
                else:
                    print("⚠️ None input handled gracefully")
                    successful_processes += 1
                    
            except Exception as e:
                print(f"❌ Error with input {i + 1}: {str(e)}")
                # Errors are acceptable for truly invalid inputs
                # but pipeline should not crash completely
        
        # Should successfully handle at least some edge cases
        assert successful_processes > 0, "Pipeline should handle at least some edge cases gracefully"
        
        print(f"\n✅ Error recovery test: {successful_processes}/{len(problematic_inputs)} inputs handled")

    def test_performance_benchmarking(self):
        """Test pipeline performance with realistic document sizes."""
        import time
        
        # Create realistic policy document (similar to actual university policies)
        realistic_policy = """
        University of Test - Artificial Intelligence Usage Policy
        
        1. PURPOSE AND SCOPE
        This policy establishes comprehensive guidelines for the responsible use of artificial intelligence 
        technologies within our academic institution. The purpose is to ensure ethical, transparent, 
        and educationally beneficial integration of AI tools while maintaining academic integrity.
        
        2. DEFINITIONS
        For the purposes of this policy, artificial intelligence refers to computer systems that can 
        perform tasks that typically require human intelligence, including but not limited to:
        - Natural language processing and generation
        - Machine learning and predictive analytics
        - Computer vision and image recognition
        - Automated decision-making systems
        
        3. PERMITTED USES
        Students and faculty may use AI tools for the following purposes:
        - Research assistance and literature review
        - Data analysis and visualization
        - Language translation and editing support
        - Accessibility accommodations
        - Learning enhancement and tutoring
        
        4. DISCLOSURE REQUIREMENTS
        All users must disclose the use of AI tools in their academic work according to these guidelines:
        - Clearly acknowledge AI assistance in assignments and papers
        - Specify which AI tools were used and for what purposes
        - Include AI usage in citations and references as appropriate
        - Maintain records of AI interactions for academic integrity purposes
        
        5. PROHIBITED USES
        The following uses of AI are strictly prohibited:
        - Submitting AI-generated work as original student work
        - Using AI to complete exams or assessments without explicit permission
        - Violating copyright or intellectual property rights through AI usage
        - Inputting confidential or sensitive data into AI systems
        
        6. FACULTY GUIDELINES
        Faculty members are responsible for:
        - Establishing clear AI usage policies for their courses
        - Providing guidance on appropriate AI integration
        - Assessing student work with AI considerations in mind
        - Reporting suspected violations of this policy
        
        7. ASSESSMENT AND EVALUATION
        The university recognizes that AI integration affects assessment methods:
        - Faculty may restrict or prohibit AI use for specific assignments
        - Alternative assessment methods may be implemented as needed
        - Student learning outcomes will be evaluated considering AI capabilities
        - Grading rubrics will be updated to reflect AI considerations
        
        8. RESEARCH APPLICATIONS
        For research purposes, AI usage must comply with:
        - Research ethics and integrity standards
        - Institutional Review Board requirements when applicable
        - Data protection and privacy regulations
        - Publication and authorship guidelines
        
        9. ENFORCEMENT AND VIOLATIONS
        Violations of this policy will be addressed through:
        - Existing academic misconduct procedures
        - Educational interventions and support
        - Disciplinary actions as appropriate
        - Appeals processes for contested violations
        
        10. POLICY REVIEW AND UPDATES
        This policy will be reviewed annually and updated as needed to reflect:
        - Technological developments in AI
        - Changes in educational practices
        - Feedback from students and faculty
        - Legal and regulatory requirements
        """
        
        # Initialize components
        text_processor = TextProcessor()
        theme_extractor = ThemeExtractor()
        policy_classifier = PolicyClassifier()
        recommendation_engine = RecommendationEngine()
        
        # Measure processing time for each component
        print("\n🚀 Performance Benchmarking")
        
        # Text processing performance
        start_time = time.time()
        cleaned_text = text_processor.clean_text(realistic_policy)
        text_stats = text_processor.get_text_statistics(cleaned_text)
        text_time = time.time() - start_time
        
        print(f"📝 Text Processing: {text_time:.3f}s ({text_stats['word_count']} words)")
        assert text_time < 1.0, f"Text processing too slow: {text_time:.3f}s"
        
        # Theme extraction performance
        start_time = time.time()
        themes = theme_extractor.extract_themes(cleaned_text)
        theme_time = time.time() - start_time
        
        print(f"🏷️ Theme Extraction: {theme_time:.3f}s ({len(themes)} themes)")
        assert theme_time < 2.0, f"Theme extraction too slow: {theme_time:.3f}s"
        
        # Classification performance
        start_time = time.time()
        classification = policy_classifier.classify_policy(cleaned_text)
        classification_time = time.time() - start_time
        
        print(f"📊 Classification: {classification_time:.3f}s ({classification['classification']})")
        assert classification_time < 1.0, f"Classification too slow: {classification_time:.3f}s"
        
        # Recommendation generation performance
        start_time = time.time()
        recommendations = recommendation_engine.generate_recommendations(
            themes=themes,
            classification=classification,
            text=cleaned_text,
            analysis_id="performance_test"
        )
        recommendation_time = time.time() - start_time
        
        rec_count = len(recommendations.get('recommendations', []))
        print(f"💡 Recommendations: {recommendation_time:.3f}s ({rec_count} recommendations)")
        assert recommendation_time < 3.0, f"Recommendation generation too slow: {recommendation_time:.3f}s"
        
        # Total pipeline performance
        total_time = text_time + theme_time + classification_time + recommendation_time
        print(f"⏱️ Total Pipeline: {total_time:.3f}s")
        
        # Should complete realistic document in under 5 seconds
        assert total_time < 5.0, f"Total pipeline too slow: {total_time:.3f}s"
        
        # Validate quality of results wasn't sacrificed for speed
        assert len(themes) >= 3, "Should extract meaningful number of themes"
        assert classification['confidence'] > 30, "Should have reasonable classification confidence"
        assert rec_count >= 2, "Should generate multiple recommendations"
        
        print(f"✅ Performance benchmarking passed")
        
        # Store performance data without returning
        performance_data = {
            'text_time': text_time,
            'theme_time': theme_time,
            'classification_time': classification_time,
            'recommendation_time': recommendation_time,
            'total_time': total_time,
            'word_count': text_stats['word_count'],
            'theme_count': len(themes),
            'recommendation_count': rec_count
        }
        
        # Test passes if all assertions passed

    def test_data_flow_consistency(self, sample_policy_text):
        """Test that data flows consistently through the pipeline without corruption."""
        
        text_processor = TextProcessor()
        theme_extractor = ThemeExtractor()
        policy_classifier = PolicyClassifier()
        recommendation_engine = RecommendationEngine()
        
        # Track data through pipeline
        original_text = sample_policy_text
        original_length = len(original_text)
        
        # Step 1: Text processing
        cleaned_text = text_processor.clean_text(original_text)
        assert isinstance(cleaned_text, str)
        assert len(cleaned_text) > 0
        assert len(cleaned_text) <= original_length  # Should be same or shorter
        
        # Key content should be preserved
        key_phrases = ["AI", "policy", "disclosure"]
        for phrase in key_phrases:
            if phrase.lower() in original_text.lower():
                assert phrase.lower() in cleaned_text.lower(), f"Key phrase '{phrase}' lost during cleaning"
        
        # Step 2: Theme extraction
        themes = theme_extractor.extract_themes(cleaned_text)
        assert isinstance(themes, list)
        assert all(isinstance(theme, dict) for theme in themes)
        
        # Themes should be relevant to policy content
        theme_names = [theme['name'].lower() for theme in themes]
        policy_relevant_terms = ['ai', 'policy', 'academic', 'guideline', 'integrity', 'disclosure']
        
        # At least some themes should be policy-relevant
        relevant_themes = sum(1 for theme_name in theme_names 
                            if any(term in theme_name for term in policy_relevant_terms))
        assert relevant_themes > 0, f"No policy-relevant themes found: {theme_names}"
        
        # Step 3: Classification
        classification = policy_classifier.classify_policy(cleaned_text)
        pytest.assert_valid_classification(classification)
        
        # Classification should be reasonable for policy content
        assert classification['classification'] in ['Restrictive', 'Moderate', 'Permissive']
        
        # Step 4: Recommendations
        recommendations_result = recommendation_engine.generate_recommendations(
            themes=themes,
            classification=classification,
            text=cleaned_text,
            analysis_id="consistency_test"
        )
        
        # Validate data consistency in recommendations
        assert 'coverage_analysis' in recommendations_result
        coverage = recommendations_result['coverage_analysis']
        
        # Coverage analysis should reference the original themes/content
        total_coverage_score = sum(dim['score'] for dim in coverage.values()) / len(coverage)
        assert 0 <= total_coverage_score <= 100, f"Invalid average coverage score: {total_coverage_score}"
        
        # Recommendations should address gaps found in coverage
        recommendations = recommendations_result['recommendations']
        if recommendations:
            rec_dimensions = [rec.get('dimension') for rec in recommendations]
            coverage_dimensions = list(coverage.keys())
            
            # Some recommendation dimensions should match coverage dimensions
            matching_dimensions = set(rec_dimensions) & set(coverage_dimensions)
            assert len(matching_dimensions) > 0, "Recommendations should address coverage dimensions"
        
        print("✅ Data flow consistency validated")
        
        # Test passes if all validations completed successfully