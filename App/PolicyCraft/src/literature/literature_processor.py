"""
Literature Processing Engine for PolicyCraft AI Policy Analysis.

This module implements comprehensive processing of academic literature for AI policy
enhancement. The processor handles PDF document extraction, insight generation,
knowledge base comparison, and version management to maintain an up-to-date
repository of policy-relevant academic knowledge.

The processing pipeline includes:
1. Document ingestion and text extraction from multiple formats
2. NLP-based insight extraction using advanced text processing
3. Semantic similarity analysis against existing knowledge base
4. Quality assessment and validation workflows
5. Version-controlled knowledge base updates

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import logging
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

# PDF processing
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. PDF processing disabled.")

# NLP components - module level variables
SPACY_AVAILABLE = False
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("Warning: spaCy not available. Using basic processing.")

EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    print("Warning: sentence-transformers not available. Using basic similarity.")
# Internal imports
from .quality_validator import LiteratureQualityValidator

logger = logging.getLogger(__name__)
from .quality_validator import LiteratureQualityValidator

logger = logging.getLogger(__name__)

class LiteratureProcessor:
    """
    Advanced literature processing system for academic document analysis.
    
    This class orchestrates the complete pipeline for processing academic literature,
    from initial document ingestion through quality assessment to knowledge base
    integration. The processor employs state-of-the-art NLP techniques for insight
    extraction and semantic analysis while maintaining rigorous quality standards.
    """
    
    def __init__(self, knowledge_base_path: str = "docs/knowledge_base"):
        """
        Initialise the literature processor with required NLP models and components.
        
        Args:
            knowledge_base_path: Path to the existing knowledge base directory
        """
        self.knowledge_base_path = knowledge_base_path
        self.quality_validator = LiteratureQualityValidator()
        self.knowledge_base_path = knowledge_base_path
        self.quality_validator = LiteratureQualityValidator()
        
        # Load spaCy model
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except OSError:
                logger.warning("spaCy en_core_web_sm not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
        
        # Load sentence transformer
        self.embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"Sentence transformer failed to load: {e}")
                self.embedder = None
        
        # Processing configuration
        self.similarity_threshold = 0.7
        self.max_insights_per_document = 15
        
        logger.info("Literature Processor initialised successfully")
    
    def extract_text(self, file_path: str) -> str:
        """Public wrapper used in tests to extract text from a file path."""
        return self._extract_text_from_file(file_path)
    
    def analyse_structure(self, text: Optional[str]) -> Dict:
        """Basic structure analysis stub used in tests."""
        if not text:
            return {"paragraphs": 0, "sentences": 0, "status": "empty"}
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        return {"paragraphs": len(paragraphs), "sentences": len(sentences), "status": "ok"}
    def process_document(self, file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Process a single academic document through the complete analysis pipeline.
        
        This method handles the end-to-end processing of academic documents including
        text extraction, insight generation, quality assessment, and knowledge base
        integration recommendations.
        
        Args:
            file_path: Path to the document file (PDF, TXT, or DOCX)
            metadata: Optional metadata dictionary with document information
            
        Returns:
            Dict: Comprehensive processing results including extracted insights,
                 quality assessment, and integration recommendations
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Step 1: Extract text content
            text_content = self._extract_text_from_file(file_path)
            if not text_content:
                return self._generate_error_result("Failed to extract text from document")
            
            # Step 2: Generate document metadata if not provided
            if metadata is None:
                metadata = self._generate_document_metadata(file_path, text_content)
            
            # Step 3: Extract insights using NLP
            extracted_insights = self._extract_insights(text_content)
            
            # Step 4: Assess document quality
            quality_assessment = self.quality_validator.assess_document_quality(
                metadata, text_content, extracted_insights
            )
            
            # Step 5: Compare against existing knowledge base
            similarity_analysis = self._compare_with_knowledge_base(
                text_content, extracted_insights
            )
            
            # Step 6: Generate processing recommendations
            processing_recommendation = self._generate_processing_recommendation(
                quality_assessment, similarity_analysis, extracted_insights
            )
            
            # Compile comprehensive results
            processing_results = {
                'document_id': self._generate_document_id(file_path, text_content),
                'processing_date': datetime.now().isoformat(),
                'file_path': file_path,
                'metadata': metadata,
                'text_content_length': len(text_content),
                'extracted_insights': extracted_insights,
                'quality_assessment': quality_assessment,
                'similarity_analysis': similarity_analysis,
                'processing_recommendation': processing_recommendation,
                'status': 'processed_successfully'
            }
            
            logger.info(f"Document processing completed successfully. Quality: {quality_assessment.get('confidence_level')}")
            return processing_results
            
        except Exception as e:
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg)
            return self._generate_error_result(error_msg)

    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file formats."""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.txt', '.md']:
                return self._extract_from_text(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_extension}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return ""

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF."""
        if not PDF_AVAILABLE:
            logger.error("PDF processing not available. Install PyMuPDF: pip install PyMuPDF")
            return ""
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

    def _extract_from_text(self, text_path: str) -> str:
        """Extract text from plain text files."""
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return ""

    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from document text using NLP."""
        if not self.nlp:
            logger.warning("spaCy not available. Using basic insight extraction.")
            return self._basic_insight_extraction(text)
        
        try:
            doc = self.nlp(text)
            insights = []
            
            # Extract key noun phrases
            for chunk in doc.noun_chunks:
                if (len(chunk.text.split()) > 1 and 
                    len(chunk.text) > 10 and 
                    len(chunk.text) < 100):
                    insights.append(chunk.text.strip())
            
            # Extract sentences containing policy-relevant terms
            policy_terms = [
                'policy', 'governance', 'ethics', 'guidelines', 'framework',
                'artificial intelligence', 'ai', 'machine learning', 'transparency',
                'accountability', 'oversight', 'human agency', 'inclusive'
            ]
            
            for sent in doc.sents:
                if (any(term in sent.text.lower() for term in policy_terms) and
                    len(sent.text) > 20 and len(sent.text) < 200):
                    insights.append(sent.text.strip())
            
            # Remove duplicates and limit results
            unique_insights = list(dict.fromkeys(insights))
            return unique_insights[:self.max_insights_per_document]
            
        except Exception as e:
            logger.error(f"Error in NLP insight extraction: {str(e)}")
            return self._basic_insight_extraction(text)

    def _basic_insight_extraction(self, text: str) -> List[str]:
        """Basic insight extraction when NLP models are not available."""
        insights = []
        sentences = text.split('.')
        
        policy_keywords = [
            'policy', 'governance', 'ethics', 'guidelines', 'artificial intelligence',
            'transparency', 'accountability', 'oversight', 'framework'
        ]
        
        for sentence in sentences:
            if (any(keyword in sentence.lower() for keyword in policy_keywords) and
                len(sentence.strip()) > 20):
                insights.append(sentence.strip())
        
        return insights[:self.max_insights_per_document]

    def _generate_document_metadata(self, file_path: str, content: str) -> Dict:
        """Generate basic metadata for document."""
        return {
            'filename': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'processing_date': datetime.now().isoformat(),
            'content_length': len(content),
            'estimated_word_count': len(content.split()),
            'file_type': os.path.splitext(file_path)[1].lower()
        }

    def _compare_with_knowledge_base(self, content: str, insights: List[str]) -> Dict:
        """Compare document against existing knowledge base for similarity."""
        similarity_results = {
            'similar_documents': [],
            'novelty_score': 1.0,
            'merge_candidates': [],
            'comparison_method': 'basic_text_matching'
        }
        
        if not self.embedder:
            logger.warning("Embeddings not available. Using basic text comparison.")
            return self._basic_similarity_comparison(content, insights)
        
        try:
            # Generate embedding for new content
            content_embedding = self.embedder.encode(content)
            
            # Compare with existing knowledge base files
            if os.path.exists(self.knowledge_base_path):
                for filename in os.listdir(self.knowledge_base_path):
                    if filename.endswith('.md'):
                        file_path = os.path.join(self.knowledge_base_path, filename)
                        existing_content = self._extract_from_text(file_path)
                        
                        if existing_content:
                            existing_embedding = self.embedder.encode(existing_content)
                            
                            # Safe numpy operations
                            if EMBEDDINGS_AVAILABLE:
                                similarity = np.dot(content_embedding, existing_embedding) / (
                                    np.linalg.norm(content_embedding) * np.linalg.norm(existing_embedding)
                                )
                                
                                if similarity > self.similarity_threshold:
                                    similarity_results['similar_documents'].append({
                                        'filename': filename,
                                        'similarity_score': float(similarity)
                                    })
            
            # Calculate novelty score
            if similarity_results['similar_documents']:
                max_similarity = max(doc['similarity_score'] for doc in similarity_results['similar_documents'])
                similarity_results['novelty_score'] = max(0.0, 1.0 - max_similarity)
            
            similarity_results['comparison_method'] = 'semantic_embedding'
            
        except Exception as e:
            logger.error(f"Error in knowledge base comparison: {str(e)}")
            return self._basic_similarity_comparison(content, insights)
        
        return similarity_results

    def _basic_similarity_comparison(self, content: str, insights: List[str]) -> Dict:
        """Basic text-based similarity comparison when embeddings unavailable."""
        similarity_results = {
            'similar_documents': [],
            'novelty_score': 0.8,  # Assume moderate novelty
            'merge_candidates': [],
            'comparison_method': 'basic_text_matching'
        }
        
        # Simple keyword-based comparison
        content_words = set(content.lower().split())
        
        if os.path.exists(self.knowledge_base_path):
            for filename in os.listdir(self.knowledge_base_path):
                if filename.endswith('.md'):
                    file_path = os.path.join(self.knowledge_base_path, filename)
                    existing_content = self._extract_from_text(file_path)
                    
                    if existing_content:
                        existing_words = set(existing_content.lower().split())
                        
                        # Calculate Jaccard similarity
                        intersection = len(content_words.intersection(existing_words))
                        union = len(content_words.union(existing_words))
                        
                        if union > 0:
                            jaccard_similarity = intersection / union
                            
                            if jaccard_similarity > 0.3:  # Lower threshold for basic comparison
                                similarity_results['similar_documents'].append({
                                    'filename': filename,
                                    'similarity_score': jaccard_similarity
                                })
        
        return similarity_results

    def _generate_processing_recommendation(self, quality_assessment: Dict,
                                          similarity_analysis: Dict,
                                          insights: List[str]) -> Dict:
        """Generate recommendation for how to process this document."""
        recommendation = {
            'action': 'review_required',
            'confidence': 'low',
            'reasoning': [],
            'suggested_filename': '',
            'merge_with_existing': False
        }
        
        # Determine action based on quality and novelty
        if (quality_assessment.get('auto_approve', False) and
            similarity_analysis.get('novelty_score', 0) > 0.5):
            recommendation['action'] = 'approve_new_document'
            recommendation['confidence'] = quality_assessment.get('confidence_level', 'medium')
        elif (quality_assessment.get('auto_approve', False) and
              similarity_analysis.get('similar_documents')):
            recommendation['action'] = 'merge_with_existing'
            recommendation['merge_with_existing'] = True
            recommendation['confidence'] = 'medium'
        
        # Generate reasoning
        if quality_assessment.get('total_score', 0) >= 0.8:
            recommendation['reasoning'].append("High quality document with strong academic credentials")
        if similarity_analysis.get('novelty_score', 0) > 0.7:
            recommendation['reasoning'].append("Document contains novel insights not present in knowledge base")
        if len(insights) >= 10:
            recommendation['reasoning'].append("Rich insight extraction suggests valuable content")
        
        return recommendation

    def _generate_document_id(self, file_path: str, content: str) -> str:
        """Generate unique identifier for document."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        filename = os.path.splitext(os.path.basename(file_path))[0]
        return f"{filename}_{content_hash}"

    def _generate_error_result(self, error_message: str) -> Dict:
        """Generate standardised error result."""
        return {
            'status': 'error',
            'error_message': error_message,
            'processing_date': datetime.now().isoformat(),
            'extracted_insights': [],
            'quality_assessment': {
                'total_score': 0.0,
                'confidence_level': 'error',
                'auto_approve': False
            },
            'processing_recommendation': {
                'action': 'manual_review_required',
                'confidence': 'error'
            }
        }