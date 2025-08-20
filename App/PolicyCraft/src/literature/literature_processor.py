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
import re
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
from ..nlp.theme_extractor import ThemeExtractor

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
        
        # Initialize theme extractor for advanced theme analysis
        try:
            self.theme_extractor = ThemeExtractor()
            logger.info("ThemeExtractor initialized successfully")
        except Exception as e:
            logger.warning(f"ThemeExtractor failed to initialize: {e}")
            self.theme_extractor = None
        
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
            
            # Step 2.5: Extract enhanced metadata (authors, abstract, keywords)
            enhanced_metadata = self._extract_enhanced_metadata(text_content, file_path)
            metadata.update(enhanced_metadata)
            
            # Step 3: Extract insights using NLP
            extracted_insights = self._extract_insights(text_content)
            
            # Step 3.5: Extract topics from insights for better categorisation
            document_topics = self._extract_topics_from_insights(extracted_insights)
            
            # Step 3.7: Extract themes using ThemeExtractor
            extracted_themes = self._extract_themes(text_content)
            
            # Step 3.8: Extract content-based recommendations
            content_recommendations = self._extract_content_recommendations(text_content)
            
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
                quality_assessment, similarity_analysis, extracted_insights, metadata
            )
            
            # Compile comprehensive results
            processing_results = {
                'document_id': self._generate_document_id(file_path, text_content),
                'processing_date': datetime.now().isoformat(),
                'file_path': file_path,
                'metadata': metadata,
                'text_content_length': len(text_content),
                'extracted_insights': extracted_insights,
                'document_topics': document_topics,
                'extracted_themes': extracted_themes,
                'content_recommendations': content_recommendations,
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
        """Extract key insights from document text using advanced NLP and semantic analysis."""
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
                'accountability', 'oversight', 'human agency', 'inclusive',
                'bias', 'fairness', 'responsible', 'trustworthy', 'explainable'
            ]
            
            # Enhanced semantic extraction for policy sentences
            policy_sentences = []
            for sent in doc.sents:
                if (any(term in sent.text.lower() for term in policy_terms) and
                    len(sent.text) > 20 and len(sent.text) < 300):
                    policy_sentences.append(sent.text.strip())
            
            # Apply semantic filtering if embeddings available
            if self.embedder and policy_sentences:
                policy_sentences = self._filter_insights_by_relevance(policy_sentences)
            
            insights.extend(policy_sentences)
            
            # Remove duplicates and limit results
            unique_insights = list(dict.fromkeys(insights))
            
            # Apply semantic clustering to get diverse insights
            if self.embedder and len(unique_insights) > self.max_insights_per_document:
                unique_insights = self._cluster_insights_semantically(unique_insights)
            
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

    def _filter_insights_by_relevance(self, sentences: List[str]) -> List[str]:
        """Filter insights using semantic similarity to AI policy concepts."""
        if not self.embedder:
            return sentences
        
        try:
            # Define AI policy reference concepts for semantic filtering
            policy_concepts = [
                "AI governance frameworks for educational institutions",
                "Ethical guidelines for artificial intelligence in universities", 
                "Transparency and accountability in AI policy implementation",
                "Human oversight and agency in automated decision making",
                "Inclusive and fair AI systems in higher education",
                "Risk management and bias mitigation in AI applications"
            ]
            
            # Encode concepts and sentences
            concept_embeddings = self.embedder.encode(policy_concepts)
            sentence_embeddings = self.embedder.encode(sentences)
            
            # Calculate similarity scores
            filtered_sentences = []
            for i, sentence in enumerate(sentences):
                # Get max similarity to any policy concept
                similarities = []
                for concept_emb in concept_embeddings:
                    similarity = np.dot(sentence_embeddings[i], concept_emb) / (
                        np.linalg.norm(sentence_embeddings[i]) * np.linalg.norm(concept_emb)
                    )
                    similarities.append(similarity)
                
                max_similarity = max(similarities)
                
                # Keep sentences with high semantic relevance
                if max_similarity > 0.3:  # Threshold for policy relevance
                    filtered_sentences.append(sentence)
            
            logger.info(f"Semantic filtering: {len(sentences)} → {len(filtered_sentences)} sentences")
            return filtered_sentences
            
        except Exception as e:
            logger.warning(f"Semantic filtering failed: {e}")
            return sentences

    def _cluster_insights_semantically(self, insights: List[str]) -> List[str]:
        """Apply semantic clustering to select diverse, representative insights."""
        if not self.embedder or len(insights) <= self.max_insights_per_document:
            return insights
        
        try:
            # Encode all insights
            embeddings = self.embedder.encode(insights)
            
            # Simple diversity sampling using cosine distance
            selected_insights = [insights[0]]  # Start with first insight
            selected_embeddings = [embeddings[0]]
            
            for i in range(1, len(insights)):
                current_embedding = embeddings[i]
                
                # Calculate minimum distance to already selected insights
                min_distance = float('inf')
                for selected_emb in selected_embeddings:
                    # Cosine distance = 1 - cosine similarity
                    similarity = np.dot(current_embedding, selected_emb) / (
                        np.linalg.norm(current_embedding) * np.linalg.norm(selected_emb)
                    )
                    distance = 1 - similarity
                    min_distance = min(min_distance, distance)
                
                # If sufficiently different from existing insights, add it
                if min_distance > 0.2:  # Diversity threshold
                    selected_insights.append(insights[i])
                    selected_embeddings.append(current_embedding)
                    
                    if len(selected_insights) >= self.max_insights_per_document:
                        break
            
            logger.info(f"Semantic clustering: {len(insights)} → {len(selected_insights)} diverse insights")
            return selected_insights
            
        except Exception as e:
            logger.warning(f"Semantic clustering failed: {e}")
            return insights[:self.max_insights_per_document]

    def _extract_topics_from_insights(self, insights: List[str]) -> List[str]:
        """Extract topic clusters from insights using semantic grouping."""
        if not insights or len(insights) < 3:
            return []
            
        try:
            # Define AI policy topic keywords for clustering
            topic_categories = {
                'governance': ['governance', 'oversight', 'management', 'administration', 'control', 'regulation'],
                'ethics': ['ethics', 'ethical', 'moral', 'values', 'principles', 'responsibility'],
                'transparency': ['transparency', 'explainable', 'interpretable', 'clear', 'open', 'disclosure'],
                'accountability': ['accountability', 'liable', 'responsible', 'answerable', 'compliance'],
                'fairness': ['fairness', 'bias', 'discrimination', 'equity', 'inclusive', 'equal'],
                'privacy': ['privacy', 'data protection', 'confidential', 'personal data', 'gdpr'],
                'safety': ['safety', 'security', 'risk', 'harm', 'protection', 'mitigation'],
                'human_agency': ['human', 'human oversight', 'human control', 'agency', 'autonomy', 'intervention']
            }
            
            # Categorise insights by topic
            topic_insights = {topic: [] for topic in topic_categories.keys()}
            
            for insight in insights:
                insight_lower = insight.lower()
                best_topic = None
                max_matches = 0
                
                for topic, keywords in topic_categories.items():
                    matches = sum(1 for keyword in keywords if keyword in insight_lower)
                    if matches > max_matches:
                        max_matches = matches
                        best_topic = topic
                
                if best_topic and max_matches > 0:
                    topic_insights[best_topic].append(insight)
            
            # Return topics that have at least 2 insights
            discovered_topics = []
            for topic, topic_insights_list in topic_insights.items():
                if len(topic_insights_list) >= 2:
                    discovered_topics.append(f"{topic}_policies")
            
            return discovered_topics[:5]  # Limit to top 5 topics
            
        except Exception as e:
            logger.warning(f"Topic extraction failed: {e}")
            return []

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

    def _basic_similarity_comparison(self, content: str, _insights: List[str]) -> Dict:
        """Basic text-based similarity comparison when embeddings unavailable.
        _insights is accepted for signature compatibility but not used here.
        """
        similarity_results = {
            'similar_documents': [],
            'novelty_score': 1.0,  # Start with maximum novelty
            'merge_candidates': [],
            'comparison_method': 'basic_text_matching'
        }
        
        # Simple keyword-based comparison
        content_words = set(content.lower().split())
        max_similarity = 0.0
        
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
                            max_similarity = max(max_similarity, jaccard_similarity)
                            
                            if jaccard_similarity > 0.3:  # Lower threshold for basic comparison
                                similarity_results['similar_documents'].append({
                                    'filename': filename,
                                    'similarity_score': jaccard_similarity
                                })
        
        # Update novelty score based on maximum similarity found
        similarity_results['novelty_score'] = max(0.0, 1.0 - max_similarity)
        
        return similarity_results

    def _generate_processing_recommendation(self, quality_assessment: Dict,
                                          similarity_analysis: Dict,
                                          insights: List[str],
                                          metadata: Dict) -> Dict:
        """Generate recommendation for how to process this document."""
        # Determine core action/confidence in a separate helper
        action, confidence, merge_with_existing = self._decide_action(quality_assessment, similarity_analysis, metadata)

        # Build reasoning list via helper for clarity and testability
        reasoning = self._build_reasoning(quality_assessment, similarity_analysis, insights)

        recommendation = {
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,
            'suggested_filename': '',
            'merge_with_existing': merge_with_existing
        }

        return recommendation

    def _decide_action(self, quality_assessment: Dict, similarity_analysis: Dict, metadata: Dict) -> Tuple[str, str, bool]:
        """Decide processing action, confidence and merge flag based on inputs.

        Preserves original thresholds and outcomes.
        """
        action = 'review_required'
        confidence = 'low'
        merge_with_existing = False

        # Configurable thresholds (ENV overrideable)
        try:
            import os
            NEW_QUALITY = float(os.getenv('AUTO_NEW_QUALITY', '0.60'))
            NEW_NOVELTY = float(os.getenv('AUTO_NEW_NOVELTY', '0.60'))
            MERGE_SIM_EMB = float(os.getenv('AUTO_MERGE_SIM', '0.75'))
            MERGE_SIM_BASIC = float(os.getenv('AUTO_BASIC_JACCARD', '0.30'))
        except Exception:
            NEW_QUALITY, NEW_NOVELTY = 0.60, 0.60
            MERGE_SIM_EMB, MERGE_SIM_BASIC = 0.75, 0.30

        qa = quality_assessment or {}
        sim = similarity_analysis or {}
        novelty = float(sim.get('novelty_score', 0) or 0)
        comparison_method = sim.get('comparison_method', 'basic_text_matching')
        similar_docs = sim.get('similar_documents') or []
        max_sim = max((d.get('similarity_score') or 0) for d in similar_docs) if similar_docs else 0.0
        merge_threshold = MERGE_SIM_EMB if comparison_method == 'semantic_embedding' else MERGE_SIM_BASIC

        qa_total = float(qa.get('total_score', 0) or 0)
        qa_auto = bool(qa.get('auto_approve', False))

        # Auto-approve NEW when high quality and novel enough
        if (qa_auto or qa_total >= NEW_QUALITY) and novelty >= NEW_NOVELTY:
            action = 'approve_new_document'
            confidence = qa.get('confidence_level', 'medium')
            return action, confidence, merge_with_existing

        # Auto-MERGE when sufficiently similar to an existing document
        # BUT only if authors are the same (different authors should never be merged)
        if similar_docs and max_sim >= merge_threshold and (qa_auto or qa_total >= 0.80):
            # Check if authors are EXACTLY the same before allowing merge
            current_author = metadata.get('author', '').strip()
            if current_author and self._can_merge_with_identical_authors(current_author, similar_docs):
                action = 'merge_with_existing'
                merge_with_existing = True
                confidence = 'medium'
                return action, confidence, merge_with_existing
            # If authors are different, treat as new document instead of merge

        # Fallback: manual review
        return action, confidence, merge_with_existing

    def _build_reasoning(self, quality_assessment: Dict, similarity_analysis: Dict, insights: List[str]) -> List[str]:
        """Construct reasoning list for recommendation without changing semantics."""
        reasoning: List[str] = []

        if quality_assessment.get('total_score', 0) >= 0.8:
            reasoning.append("High quality document with strong academic credentials")
        if similarity_analysis.get('novelty_score', 0) > 0.7:
            reasoning.append("Document contains novel insights not present in knowledge base")
        if len(insights) >= 10:
            reasoning.append("Rich insight extraction suggests valuable content")

        return reasoning

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

    def _extract_enhanced_metadata(self, text: str, file_path: str = None) -> Dict:
        """Extract enhanced metadata including authors, abstract, keywords, etc."""
        metadata = {}
        
        # Set current filename for fallback author extraction
        self._current_filename = os.path.basename(file_path) if file_path else None
        
        # Extract authors using pattern matching
        authors = self._extract_authors(text)
        if authors:
            metadata['author'] = authors
            metadata['author_count'] = len(authors.split(',')) if isinstance(authors, str) else len(authors)
        
        # Extract abstract
        abstract = self._extract_abstract(text)
        if abstract:
            metadata['abstract'] = abstract
            metadata['abstract_length'] = len(abstract)
        
        # Extract keywords
        keywords = self._extract_keywords(text)
        if keywords:
            metadata['keywords'] = keywords
            metadata['keyword_count'] = len(keywords)
        
        # Extract publication year
        pub_year = self._extract_publication_year(text)
        if pub_year:
            metadata['publication_year'] = pub_year
            metadata['publication_date'] = f"{pub_year}-01-01"  # Default to beginning of year
        
        # Extract journal/conference name
        journal = self._extract_journal_name(text)
        if journal:
            metadata['journal'] = journal
        
        # Extract DOI if present
        doi = self._extract_doi(text)
        if doi:
            metadata['doi'] = doi
        
        return metadata
    
    def _extract_authors(self, text: str) -> Optional[str]:
        """Extract author names from document text."""
        # Common patterns for author extraction
        patterns = [
            r'(?:Authors?:?\s*)([A-Z][a-z]+(?:\s+[A-Z]\.\s*)?[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z]\.\s*)?[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+,\s*[A-Z]\.\s*(?:,\s*[A-Z][a-z]+,\s*[A-Z]\.)*)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z]\.\s*)?[A-Z][a-z]+(?:\s*,\s*&?\s*[A-Z][a-z]+(?:\s+[A-Z]\.\s*)?[A-Z][a-z]+)*)'
        ]
        
        # Try each pattern on the first few pages
        first_page = text[:2000]  # First ~2000 characters
        
        for pattern in patterns:
            match = re.search(pattern, first_page, re.MULTILINE)
            if match:
                authors = match.group(1).strip()
                # Clean up the authors string
                authors = re.sub(r'\s+', ' ', authors)  # Normalize whitespace
                
                # Filter out invalid author values
                invalid_authors = ['Open Access', 'open access', 'OPEN ACCESS', 'Available online', 'Creative Commons']
                if authors not in invalid_authors and not any(invalid in authors for invalid in invalid_authors):
                    return authors
        
        # If no authors found in text, try to extract from filename as fallback
        return self._extract_authors_from_filename()
    
    def _extract_authors_from_filename(self) -> Optional[str]:
        """Extract authors from filename as fallback method."""
        if not hasattr(self, '_current_filename') or not self._current_filename:
            return None
            
        filename = self._current_filename.lower()
        
        # Common filename patterns with authors
        patterns = [
            r'(\w+)(?:_|\s+)[a-z]\.(?:_|\s+)(?:et\.?\s*al\.?|etal)',  # Smith_M_et_al 
            r'(\w+)(?:_|\s+)(?:et\.?\s*al\.?|etal)',  # Smith_et_al or Smith et al
            r'(\w+)(?:_|\s+)[a-z]\.(?:_|\s+)(\w+)(?:_|\s+)[a-z]\.',   # Smith_M_Jones_K
            r'(\w+)(?:_|\s+)(\w+)(?:_|\s+)(\d{4})',   # Smith_Jones_2024
            r'(\w+)(?:_|\s+)(\w+)(?:_|\s+)(\w+)',     # Smith_Jones_Brown
            r'(\w+)(?:_|\s+)(\w+)',                    # Smith_Jones
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if 'et' in pattern:
                    # Handle et al format
                    return f"{match.group(1).title()} et al."
                elif len(match.groups()) >= 2:
                    # Handle multiple authors - filter out years and invalid names
                    authors = []
                    for group in match.groups():
                        if group and not group.isdigit() and len(group) > 1:
                            # Skip common non-author words
                            if group.lower() not in ['comprehensive', 'ethical', 'policy', 'ai', 'intelligence', 'education']:
                                authors.append(group.title())
                    if authors:
                        if len(authors) > 2:
                            return f"{', '.join(authors[:2])} et al."
                        else:
                            return ', '.join(authors)
                else:
                    return match.group(1).title()
        
        return None
    
    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from document text."""
        patterns = [
            r'Abstract:?\s*\n(.*?)(?:\n\s*\n|\nKeywords?:|\nIntroduction|\n1\.)',
            r'ABSTRACT\s*\n(.*?)(?:\n\s*\n|\nKeywords?:|\nIntroduction|\n1\.)',
            r'Summary:?\s*\n(.*?)(?:\n\s*\n|\nKeywords?:|\nIntroduction|\n1\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:3000], re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace
                if len(abstract) > 50:  # Minimum meaningful abstract length
                    return abstract
        
        return None
    
    def _extract_keywords(self, text: str) -> Optional[List[str]]:
        """Extract keywords from document text."""
        patterns = [
            r'Keywords?:?\s*(.*?)(?:\n\s*\n|\nIntroduction|\n1\.|\nABSTRACT)',
            r'Key\s+words?:?\s*(.*?)(?:\n\s*\n|\nIntroduction|\n1\.)',
            r'Index\s+terms?:?\s*(.*?)(?:\n\s*\n|\nIntroduction|\n1\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:3000], re.DOTALL | re.IGNORECASE)
            if match:
                keywords_text = match.group(1).strip()
                # Split by common separators
                keywords = re.split(r'[,;]\s*', keywords_text)
                # Clean up keywords
                keywords = [kw.strip().lower() for kw in keywords if kw.strip()]
                keywords = [kw for kw in keywords if len(kw) > 2]  # Filter short terms
                if keywords:
                    return keywords
        
        return None
    
    def _extract_publication_year(self, text: str) -> Optional[int]:
        """Extract publication year from document text."""
        # Look for 4-digit years in typical ranges
        years = re.findall(r'\b(19[7-9]\d|20[0-4]\d)\b', text[:2000])
        if years:
            # Return the most recent reasonable year
            years = [int(year) for year in years]
            recent_years = [year for year in years if year >= 1990]  # Focus on recent publications
            if recent_years:
                return max(recent_years)
        
        return None
    
    def _extract_journal_name(self, text: str) -> Optional[str]:
        """Extract journal or conference name."""
        patterns = [
            r'Published in:?\s*(.*?)(?:\n|,|\.|$)',
            r'Journal:?\s*(.*?)(?:\n|,|\.|$)',
            r'Conference:?\s*(.*?)(?:\n|,|\.|$)',
            r'Proceedings of:?\s*(.*?)(?:\n|,|\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                journal = match.group(1).strip()
                if len(journal) > 5:  # Minimum meaningful journal name
                    return journal
        
        return None
    
    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from document text."""
        doi_pattern = r'(?:doi:?\s*|DOI:?\s*)(10\.\d+/[^\s,\]]+)'
        match = re.search(doi_pattern, text[:3000], re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_themes(self, text: str) -> List[Dict]:
        """Extract themes using ThemeExtractor."""
        if not self.theme_extractor:
            logger.warning("ThemeExtractor not available. Skipping theme extraction.")
            return []
        
        try:
            themes = self.theme_extractor.extract_themes(text, max_themes=10)
            logger.info(f"Extracted {len(themes)} themes from document")
            return themes
        except Exception as e:
            logger.error(f"Theme extraction failed: {e}")
            return []
    
    def _extract_content_recommendations(self, text: str) -> List[str]:
        """Extract content-based recommendations from the literature."""
        recommendations = []
        
        # Patterns for finding recommendations in academic text
        recommendation_patterns = [
            r'(?:recommend[s]?|suggest[s]?|propose[s]?|advise[s]?)\s+(?:that\s+)?([^.!?]+[.!?])',
            r'(?:should|must|ought to|need to)\s+([^.!?]+[.!?])',
            r'(?:it is (?:essential|important|crucial|necessary))\s+(?:that\s+)?([^.!?]+[.!?])',
            r'(?:future research|further studies|next steps)\s+(?:should\s+)?([^.!?]+[.!?])',
            r'(?:implications?|conclusions?):?\s*([^.!?]+[.!?])'
        ]
        
        # Search for recommendations in the text
        for pattern in recommendation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                recommendation = match.group(1).strip()
                # Clean up the recommendation
                recommendation = re.sub(r'\s+', ' ', recommendation)
                if len(recommendation) > 20:  # Minimum meaningful recommendation
                    recommendations.append(recommendation)
        
        # Remove duplicates and limit to top recommendations
        recommendations = list(dict.fromkeys(recommendations))  # Remove duplicates
        recommendations = recommendations[:10]  # Limit to 10 recommendations
        
        logger.info(f"Extracted {len(recommendations)} content recommendations")
        return recommendations

    def _can_merge_with_identical_authors(self, current_author: str, similar_docs: List[Dict]) -> bool:
        """Check if current document can be merged with similar documents based on EXACT author match.
        
        Only allows merge if authors are IDENTICAL - no similar names allowed.
        
        Args:
            current_author: Author(s) of current document (original case)
            similar_docs: List of similar documents with metadata
            
        Returns:
            bool: True only if authors are exactly identical, False otherwise
        """
        if not current_author or not similar_docs:
            return False
            
        # Normalize current author for comparison (remove extra spaces, standardize format)
        current_normalized = self._normalize_author_string(current_author)
        
        # For each similar document, we need to get the actual author from knowledge base
        # This requires reading the actual document metadata, not just filename
        for doc in similar_docs:
            doc_filename = doc.get('filename', '')
            if not doc_filename:
                continue
                
            # Try to extract author from the knowledge base document
            try:
                kb_author = self._extract_author_from_kb_document(doc_filename)
                if kb_author:
                    kb_normalized = self._normalize_author_string(kb_author)
                    
                    # Only allow merge if authors are EXACTLY the same
                    if current_normalized == kb_normalized:
                        return True
            except Exception:
                # If we can't determine the author, don't allow merge
                continue
                
        # If no exact author matches found, don't allow merge
        return False
    
    def _normalize_author_string(self, author: str) -> str:
        """Normalize author string for exact comparison."""
        if not author:
            return ""
        
        # Remove extra whitespace, convert to lowercase for comparison
        normalized = ' '.join(author.strip().split()).lower()
        
        # Remove common separators and normalize format
        normalized = normalized.replace(' & ', ', ').replace(' and ', ', ')
        
        # Sort authors alphabetically for consistent comparison
        authors_list = [a.strip() for a in normalized.split(',') if a.strip()]
        authors_list.sort()
        
        return ', '.join(authors_list)
    
    def _extract_author_from_kb_document(self, kb_filename: str) -> str:
        """Extract author from knowledge base document file.
        
        This is a simplified implementation - in practice you'd want to 
        read the actual document metadata from the KB file.
        """
        # For now, return empty string to effectively disable merge
        # This ensures no merge happens until we have proper author extraction
        # from existing KB documents
        return ""