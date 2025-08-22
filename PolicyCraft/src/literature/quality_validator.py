"""
Literature Quality Validator for PolicyCraft AI Policy Analysis.

This module implements a sophisticated quality assessment framework for academic
literature used in AI policy recommendations. The validator evaluates documents
across multiple dimensions including source credibility, methodological rigour,
and content relevance to ensure only high-quality insights inform policy
recommendations.

The framework employs a three-tier assessment system:
1. Source Credibility Assessment: Evaluates publisher reputation and institutional affiliation
2. Content Quality Analysis: Assesses methodological transparency and empirical foundation
3. Relevance Scoring: Determines alignment with AI policy domains and current practice

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LiteratureQualityValidator:
    """
    Advanced quality assessment system for academic literature in AI policy contexts.
    
    This class provides comprehensive evaluation of academic documents to ensure
    only high-quality, methodologically sound research informs policy recommendations.
    The validator considers multiple factors including source reputation, research
    methodology, sample sizes, and alignment with established academic standards.
    """
    
    def __init__(self):
        """
        Initialise the quality validator with assessment criteria and thresholds.
        
        Sets up the multi-dimensional assessment framework including source credibility
        indicators, content quality metrics, and confidence thresholds for automated
        vs manual review decisions.
        """
        
        # Quality assessment thresholds - simplified: ≥60% auto-approve, <60% manual review
        self.quality_thresholds = {
            'auto_approve_threshold': 0.6,
            'auto_approve': True,
            'manual_review': False
        }
        
        # Source credibility indicators with associated weights
        self.source_indicators = {
            'high_credibility': {
                'keywords': ['unesco', 'jisc', 'oxford', 'cambridge', 'mit', 'stanford', 'harvard'],
                'domains': ['.edu', '.ac.uk', '.org'],
                'score': 1.0
            },
            'medium_credibility': {
                'keywords': ['university', 'institute', 'research', 'academic'],
                'indicators': ['peer.reviewed', 'journal', 'conference'],
                'score': 0.7
            },
            'basic_credibility': {
                'keywords': ['policy', 'report', 'guidelines'],
                'score': 0.4
            }
        }
        
        logger.info("Literature Quality Validator initialised successfully")

    def assess_document_quality(self, document_metadata: Dict, content: str, 
                              extracted_insights: List[str]) -> Dict:
        """
        Perform comprehensive quality assessment of academic document.
        
        This method evaluates a document across multiple quality dimensions to determine
        its suitability for inclusion in the policy recommendation knowledge base.
        
        Args:
            document_metadata: Dictionary containing document metadata including
                             title, author, publication year, source URL, etc.
            content: Full text content of the document for analysis
            extracted_insights: List of key insights extracted from the document
            
        Returns:
            Dict: Comprehensive quality assessment including scores, confidence level,
                 and approval recommendation
        """
        try:
            # Assess different quality dimensions
            source_score = self._assess_source_credibility(document_metadata)
            content_score = self._assess_content_quality(content, extracted_insights)
            methodology_score = self._assess_methodology_quality(content)
            relevance_score = self._assess_policy_relevance(content, extracted_insights)
            
            # Calculate weighted total score
            total_score = (
                source_score * 0.3 +
                content_score * 0.25 +
                methodology_score * 0.25 +
                relevance_score * 0.2
            )
            
            # Determine confidence level and approval status (simplified: only total_score matters)
            confidence_level, auto_approve = self._determine_confidence_level(
                total_score, source_score, content_score
            )
            
            assessment_result = {
                'total_score': round(total_score, 3),
                'dimension_scores': {
                    'source_credibility': round(source_score, 3),
                    'content_quality': round(content_score, 3),
                    'methodology_quality': round(methodology_score, 3),
                    'policy_relevance': round(relevance_score, 3)
                },
                'confidence_level': confidence_level,
                'auto_approve': auto_approve,
                'assessment_date': datetime.now().isoformat(),
                'recommendation': self._generate_quality_recommendation(
                    total_score, confidence_level, auto_approve
                )
            }
            
            logger.info(f"Document quality assessment completed: {confidence_level} confidence, score: {total_score:.3f}")
            return assessment_result
            
        except Exception as e:
            logger.error(f"Error in document quality assessment: {str(e)}")
            return self._generate_fallback_assessment(str(e))

    def _assess_source_credibility(self, metadata: Dict) -> float:
        """Assess credibility of document source based on institutional affiliation."""
        credibility_score = 0.0
        
        # Extract relevant text for analysis
        source_text = ' '.join([
            metadata.get('title', '').lower(),
            metadata.get('author', '').lower(),
            metadata.get('source_url', '').lower(),
            metadata.get('publisher', '').lower()
        ])
        
        # Check against credibility indicators
        for level, indicators in self.source_indicators.items():
            if any(keyword in source_text for keyword in indicators.get('keywords', [])):
                credibility_score = max(credibility_score, indicators['score'])
            
            if 'domains' in indicators:
                if any(domain in source_text for domain in indicators['domains']):
                    credibility_score = max(credibility_score, indicators['score'])
        
        return min(1.0, credibility_score)

    def _assess_content_quality(self, content: str, insights: List[str]) -> float:
        """Assess quality of document content and extracted insights."""
        content_lower = content.lower()
        quality_score = 0.0
        
        # Check for methodological indicators
        methodology_indicators = [
            'methodology', 'method', 'approach', 'framework', 'analysis',
            'data', 'sample', 'results', 'findings', 'conclusion'
        ]
        method_score = sum(1 for indicator in methodology_indicators if indicator in content_lower)
        quality_score += min(0.4, method_score / len(methodology_indicators))
        
        # Assess insight quality
        if insights and len(insights) > 0:
            insight_quality = min(0.3, len(insights) / 10)  # Up to 0.3 for good insight extraction
            quality_score += insight_quality
        
        # Check for academic language and structure
        academic_indicators = [
            'research', 'study', 'investigation', 'empirical', 'theoretical',
            'literature review', 'systematic', 'meta-analysis'
        ]
        academic_score = sum(1 for indicator in academic_indicators if indicator in content_lower)
        quality_score += min(0.3, academic_score / len(academic_indicators))
        
        return min(1.0, quality_score)

    def _assess_methodology_quality(self, content: str) -> float:
        """Assess methodological rigour of the research."""
        methodology_score = 0.0
        content_lower = content.lower()
        
        # Check for clear methodology description
        methodology_terms = [
            'methodology', 'methods', 'approach', 'procedure', 'protocol',
            'systematic', 'empirical', 'quantitative', 'qualitative'
        ]
        if any(term in content_lower for term in methodology_terms):
            methodology_score += 0.4
        
        # Check for data and evidence
        evidence_terms = [
            'data', 'evidence', 'findings', 'results', 'analysis',
            'statistics', 'survey', 'interview', 'observation'
        ]
        evidence_count = sum(1 for term in evidence_terms if term in content_lower)
        methodology_score += min(0.3, evidence_count / len(evidence_terms))
        
        # Check for validation and reliability
        validation_terms = ['validation', 'reliability', 'validity', 'verification', 'peer review']
        if any(term in content_lower for term in validation_terms):
            methodology_score += 0.3
        
        return min(1.0, methodology_score)

    def _assess_policy_relevance(self, content: str, insights: List[str]) -> float:
        """Assess relevance to AI policy domains."""
        relevance_score = 0.0
        content_lower = content.lower()
        
        # AI and technology terms
        ai_terms = [
            'artificial intelligence', 'ai', 'machine learning', 'generative ai',
            'chatgpt', 'llm', 'natural language processing', 'automation'
        ]
        ai_relevance = sum(1 for term in ai_terms if term in content_lower)
        relevance_score += min(0.4, ai_relevance / 5)  # Cap at 0.4
        
        # Education and policy terms
        education_terms = [
            'education', 'teaching', 'learning', 'university', 'academic',
            'policy', 'governance', 'ethics', 'guidelines', 'framework'
        ]
        education_relevance = sum(1 for term in education_terms if term in content_lower)
        relevance_score += min(0.4, education_relevance / 5)  # Cap at 0.4
        
        # Check insights for policy relevance
        if insights:
            policy_relevant_insights = 0
            for insight in insights:
                if any(term in insight.lower() for term in ['policy', 'governance', 'ethics', 'guidelines']):
                    policy_relevant_insights += 1
            relevance_score += min(0.2, policy_relevant_insights / len(insights))
        
        return min(1.0, relevance_score)

    def _determine_confidence_level(self, total_score: float, source_score: float, 
                                  content_score: float) -> Tuple[str, bool]:
        """Determine confidence level and approval status based on scores."""
        
        # Simplified logic: ≥60% auto-approve, <60% manual review
        if total_score >= self.quality_thresholds['auto_approve_threshold']:
            return 'high', self.quality_thresholds['auto_approve']
        else:
            return 'low', self.quality_thresholds['manual_review']

    def _generate_quality_recommendation(self, score: float, confidence: str, 
                                       auto_approve: bool) -> str:
        """Generate human-readable quality recommendation."""
        if auto_approve:
            return f"Quality document (score: {score:.1%}). Approved for automatic inclusion in knowledge base."
        else:
            return f"Lower quality document (score: {score:.1%}). Requires manual review before inclusion."

    def _generate_fallback_assessment(self, error_message: str) -> Dict:
        """Generate fallback assessment when main process fails."""
        return {
            'total_score': 0.0,
            'dimension_scores': {
                'source_credibility': 0.0,
                'content_quality': 0.0,
                'methodology_quality': 0.0,
                'policy_relevance': 0.0
            },
            'confidence_level': 'error',
            'auto_approve': False,
            'assessment_date': datetime.now().isoformat(),
            'recommendation': f"Assessment failed due to error: {error_message}. Manual review required.",
            'error': error_message
        }