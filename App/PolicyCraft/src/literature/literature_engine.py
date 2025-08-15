"""
Literature Engine for PolicyCraft AI Policy Analysis.

This module serves as the main orchestrator for the literature processing system,
coordinating document processing, quality assessment, and knowledge base integration.
The engine provides a unified interface for admin users to upload and process
academic literature while maintaining system integrity and quality standards.

The engine implements:
1. Complete document processing pipeline from upload to integration
2. Quality assurance workflows with automatic and manual review paths
3. Integration with existing PolicyCraft recommendation system
4. Admin interface integration for seamless user experience
5. Comprehensive logging and error handling

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from werkzeug.utils import secure_filename

# Internal imports
from .literature_processor import LiteratureProcessor
from .quality_validator import LiteratureQualityValidator
from .knowledge_manager import KnowledgeBaseManager
from src.analysis_engine.literature.repository import LiteratureRepository

logger = logging.getLogger(__name__)

class LiteratureEngine:
    """
    Main orchestrator for academic literature processing and integration.
    
    This class provides the primary interface for processing academic documents
    and integrating insights into the PolicyCraft knowledge base. It coordinates
    all aspects of the literature update pipeline while ensuring quality and
    maintaining system integrity.
    """
    
    def __init__(self, upload_path: str = "data/literature", 
                 knowledge_base_path: str = "docs/knowledge_base"):
        """
        Initialise the literature engine with required components and configuration.
        
        Args:
            upload_path: Directory for temporarily storing uploaded files
            knowledge_base_path: Path to the knowledge base directory
        """
        self.upload_path = upload_path
        self.knowledge_base_path = knowledge_base_path
        
        # Ensure upload directory exists
        os.makedirs(upload_path, exist_ok=True)
        
        # Initialise core components
        self.processor = LiteratureProcessor(knowledge_base_path)
        self.quality_validator = LiteratureQualityValidator()
        self.knowledge_manager = KnowledgeBaseManager(knowledge_base_path)
        
        # Activity log stored alongside knowledge base for simplicity
        try:
            kb_path = getattr(self.knowledge_manager, 'knowledge_base_path', 'docs/knowledge_base')
        except Exception:
            kb_path = 'docs/knowledge_base'
        self.activity_log_file = os.path.join(kb_path, 'activity_log.json')
        
        # Supported file types
        self.supported_extensions = {'.pdf', '.txt', '.md'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        logger.info("Literature Engine initialised successfully")
        
    def process_literature(self, file, metadata: Optional[Dict] = None) -> Dict[str, any]:
        """
        Process an uploaded file through the complete literature pipeline.
        
        This method handles the end-to-end processing of uploaded academic documents,
        from initial validation through quality assessment to knowledge base integration.
        
        Args:
            file: Uploaded file object (from Flask request.files)
            metadata: Optional metadata dictionary with document information
        
        Returns:
            Dict: Comprehensive processing results including status, quality assessment,
                 and integration recommendations
        """
        try:
            logger.info(f"Processing uploaded file: {file.filename}")
            
            # Step 1: Validate uploaded file
            validation_result = self._validate_uploaded_file(file)
            if not validation_result['valid']:
                return self._generate_processing_result(
                    'validation_failed', validation_result['message']
                )
            
            # Step 2: Save file securely
            file_path = self._save_uploaded_file(file)
            if not file_path:
                return self._generate_processing_result(
                    'save_failed', 'Failed to save uploaded file'
                )
            
            # Step 3: Process document through pipeline
            processing_results = self.processor.process_document(file_path, metadata)
            
            if processing_results.get('status') == 'error':
                return self._generate_processing_result(
                    'processing_failed', 
                    processing_results.get('error_message', 'Processing failed')
                )
            
            # Step 4: Attempt integration if quality is sufficient
            integration_results = self.knowledge_manager.integrate_new_document(processing_results)
            # Incrementally update literature repository index (no-op on failure)
            try:
                LiteratureRepository.get().on_document_integrated(processing_results)
            except Exception:
                pass
            
            # Step 5: Save analysis data before cleanup
            analysis_data = self._save_analysis_data(processing_results, file.filename)
            
            # Step 6: Clean up temporary file
            self._cleanup_temporary_file(file_path)
            
            # Step 7: Compile comprehensive results
            final_results = self._compile_final_results(
                processing_results, integration_results, file.filename, analysis_data
            )
            
            logger.info(f"File processing completed: {final_results.get('status')}")
            return final_results
            
        except Exception as e:
            error_msg = f"Error processing uploaded file: {str(e)}"
            logger.error(error_msg)
            return self._generate_processing_result('error', error_msg)

    def analyse_themes(self, text: Optional[str]) -> Dict:
        """Minimal theme analysis wrapper used by tests."""
        if not text:
            return {"themes": [], "status": "empty"}
        # Reuse processor insight extraction as a proxy for themes
        insights = self.processor._basic_insight_extraction(text) if hasattr(self.processor, '_basic_insight_extraction') else []
        # Map insights to simple theme-like dicts
        themes = [{"name": i[:50], "score": 0.5, "confidence": 50} for i in insights[:5]]
        return {"themes": themes, "status": "ok"}

    def get_processing_status(self) -> Dict:
        """Get current status of literature processing system."""
        try:
            kb_status = self.knowledge_manager.get_knowledge_base_status()
            # Flatten structure: KnowledgeBaseManager returns {'knowledge_base': {...}}
            # For templates expecting system_status.knowledge_base.total_documents, expose the inner dict directly.
            kb_stats = kb_status.get('knowledge_base', kb_status)
            
            return {
                'system_status': 'operational',
                'knowledge_base': kb_stats,
                'supported_formats': list(self.supported_extensions),
                'max_file_size_mb': self.max_file_size // (1024 * 1024),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {str(e)}")
            return {
                'system_status': 'error',
                'error_message': str(e),
                'last_check': datetime.now().isoformat()
            }

    # ------------------------------------------------------------------
    # Activity logging API
    # ------------------------------------------------------------------
    def _read_activity_log(self) -> List[Dict]:
        try:
            if os.path.exists(self.activity_log_file):
                with open(self.activity_log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
        except Exception as e:
            logger.warning(f"Failed to read activity log: {e}")
        return []

    def _write_activity_log(self, entries: List[Dict]) -> None:
        try:
            os.makedirs(os.path.dirname(self.activity_log_file), exist_ok=True)
            with open(self.activity_log_file, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write activity log: {e}")

    def log_activity(self, status: str, filename: str = None, document_id: str = None,
                     quality: Optional[float] = None, insights_count: Optional[int] = None) -> None:
        """Append an activity entry.

        Args:
            status: 'processing' | 'completed' | 'failed'
            filename: Optional filename shown in UI
            document_id: Optional document ID if known
            quality: Optional quality score (0-100)
            insights_count: Optional number of insights
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'filename': filename,
            'document_id': document_id,
            'quality': quality,
            'insights_count': insights_count,
        }
        entries = self._read_activity_log()
        entries.append(entry)
        # Keep log bounded (latest 200)
        entries = entries[-200:]
        self._write_activity_log(entries)

    def get_recent_processing_activity(self, limit: int = 6) -> List[Dict]:
        """Return recent processing activity entries for the admin dashboard.

        Entries referencing documents that no longer exist in the KB are shown
        with status 'deleted' so the UI can present them distinctly.
        """
        entries = self._read_activity_log()

        # Build set of current KB stems (without extension)
        kb_stems: set = set()
        try:
            if os.path.isdir(self.knowledge_manager.knowledge_base_path):
                for fn in os.listdir(self.knowledge_manager.knowledge_base_path):
                    if fn.endswith('.md'):
                        kb_stems.add(os.path.splitext(fn)[0])
        except Exception:
            pass

        def is_in_kb(entry: Dict) -> bool:
            filename = str(entry.get('filename') or '')
            stem = os.path.splitext(os.path.basename(filename))[0] if filename else ''
            doc_id = str(entry.get('document_id') or '')
            if not kb_stems:
                return True
            return (stem in kb_stems) or (doc_id in kb_stems) or any(doc_id and doc_id in s for s in kb_stems)

        # Map missing docs to deleted status
        normalized: List[Dict] = []
        for e in entries:
            e2 = dict(e)
            if not is_in_kb(e2):
                e2['status'] = 'deleted'
            normalized.append(e2)

        try:
            normalized.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception:
            pass
        return normalized[:limit]

    def get_recent_processing_history(self, limit: int = 10) -> List[Dict]:
        """Get recent processing history for admin interface with document metadata."""
        try:
            kb_status = self.knowledge_manager.get_knowledge_base_status()
            recent_updates = kb_status.get('knowledge_base', {}).get('recent_updates', [])
            
            # Get all documents from knowledge base to fetch metadata
            all_documents = self.knowledge_manager.get_all_documents()
            # Only include documents that have a 'document_id' key to prevent KeyError
            documents_by_id = {doc['document_id']: doc for doc in all_documents if 'document_id' in doc}
            
            # Format for admin interface
            formatted_history = []
            for update in recent_updates[-limit:]:
                document_id = update.get('document_id')
                document_metadata = documents_by_id.get(document_id, {}).get('metadata', {}) if document_id else {}
                
                # Get filename from update or document metadata
                filename = update.get('filename') or documents_by_id.get(document_id, {}).get('filename', '')
                
                # Convert old quality scores to new format (0-100) and fix edge cases
                raw_quality_score = update.get('quality_score')
                if raw_quality_score is not None:
                    if raw_quality_score <= 2.0:
                        # Old format detected (0.0-2.0), convert to 0-100
                        converted_quality_score = round(raw_quality_score * 100, 1)
                        # Cap at 100% maximum
                        converted_quality_score = min(100.0, converted_quality_score)
                        logger.debug(f"Converting quality score for {document_id}: {raw_quality_score} -> {converted_quality_score}")
                    elif raw_quality_score > 100:
                        # Already converted but exceeds 100%, cap it
                        converted_quality_score = 100.0
                        logger.debug(f"Capping quality score for {document_id}: {raw_quality_score} -> {converted_quality_score}")
                    else:
                        # Already in 0-100 format
                        converted_quality_score = raw_quality_score
                else:
                    converted_quality_score = raw_quality_score
                
                formatted_update = {
                    'timestamp': update.get('timestamp'),
                    'document_id': document_id,
                    'action': update.get('action'),
                    'filename': filename,
                    'quality_score': converted_quality_score,
                    'insights_count': update.get('insights_count'),
                    'metadata': document_metadata  # Include full metadata
                }
                
                # Also include top-level fields for backward compatibility
                if document_metadata:
                    formatted_update.update({
                        'author': document_metadata.get('author'),
                        'university': document_metadata.get('university') or 
                                    document_metadata.get('institution') or 
                                    document_metadata.get('affiliation'),
                        'publication_year': document_metadata.get('publication_year') or 
                                         (document_metadata.get('publication_date')[:4] 
                                          if document_metadata.get('publication_date') else None)
                    })
        
                # If we have a filename but no title in metadata, use the filename as title
                if filename and not document_metadata.get('title'):
                    # Clean up the filename to make it more readable
                    clean_name = os.path.splitext(filename)[0]  # Remove extension
                    clean_name = clean_name.split('_', 1)[-1]  # Remove document ID if present
                    clean_name = clean_name.replace('_', ' ').replace('-', ' ').title()  # Clean up
                    document_metadata['title'] = clean_name
                    formatted_update['metadata'] = document_metadata
                    
                    if 'title' not in formatted_update:
                        formatted_update['title'] = clean_name
                
                formatted_history.append(formatted_update)
            
            return formatted_history
            
        except Exception as e:
            logger.error(f"Error getting processing history: {str(e)}")
            return []

    def get_unified_document_data(self, include_version_history: bool = True) -> List[Dict]:
        """
        Get unified document data with consistent quality scores for all admin interfaces.
        This is the single source of truth for document data across all admin pages.
        
        Args:
            include_version_history: Whether to include version history entries
            
        Returns:
            List[Dict]: Unified document data with consistent quality scores (0-100 scale)
        """
        try:
            logger.info(f"Getting unified document data, include_version_history={include_version_history}")
            unified_documents = []
            processed_ids = set()
            
            # 1. Get version history entries (if requested)
            if include_version_history:
                kb_status = self.knowledge_manager.get_knowledge_base_status()
                recent_updates = kb_status.get('knowledge_base', {}).get('recent_updates', [])
                
                for update in recent_updates:
                    document_id = update.get('document_id')
                    if document_id and document_id not in processed_ids:
                        # Convert and normalize quality score
                        quality_score = self._normalize_quality_score(update.get('quality_score'))
                        
                        unified_documents.append({
                            'timestamp': update.get('timestamp'),
                            'document_id': document_id,
                            'action': update.get('action'),
                            'filename': update.get('filename'),
                            'quality_score': quality_score,
                            'insights_count': update.get('insights_count'),
                            'metadata': update.get('metadata', {}),
                            'source': 'version_history'
                        })
                        processed_ids.add(document_id)
            
            # 2. Get all knowledge base documents
            all_documents = self.knowledge_manager.get_all_documents()
            logger.info(f"Found {len(all_documents)} documents in knowledge base")
            
            for doc in all_documents:
                doc_id = doc.get('document_id') or doc.get('filename', '').replace('.md', '')
                filename = doc.get('filename')
                raw_quality_score = doc.get('quality_score')
                
                # Skip if already included from version history
                if doc_id not in processed_ids and filename not in processed_ids:
                    # Use calculated quality score (already in 0-100 format)
                    quality_score = self._normalize_quality_score(raw_quality_score)
                    logger.info(f"Document {filename}: raw_score={raw_quality_score} -> normalized={quality_score}")
                    
                    # Get timestamp from various sources
                    metadata = doc.get('metadata', {})
                    timestamp = (metadata.get('upload_date') or 
                               metadata.get('processing_date') or 
                               metadata.get('publication_date') or
                               'Unknown')
                    
                    # If timestamp is just a year, convert to proper date format
                    if timestamp != 'Unknown' and len(str(timestamp)) == 4:
                        timestamp = f"{timestamp}-01-01"
                    
                    unified_documents.append({
                        'timestamp': timestamp,
                        'document_id': doc_id,
                        'action': 'existing_document',
                        'filename': filename,
                        'quality_score': quality_score,
                        'insights_count': doc.get('insights_count'),
                        'metadata': metadata,
                        'title': metadata.get('title') or filename.replace('.md', '').replace('_', ' ').title(),
                        'author': metadata.get('author', 'Unknown'),
                        'publication_date': metadata.get('publication_date', 'Unknown'),
                        'source': 'knowledge_base'
                    })
                    processed_ids.add(doc_id)
                    if filename:
                        processed_ids.add(filename)
            
            return unified_documents
            
        except Exception as e:
            logger.error(f"Error getting unified document data: {str(e)}")
            return []
    
    def _normalize_quality_score(self, raw_score) -> float:
        """
        Normalize quality score to 0-100 scale, handling all legacy formats.
        This is the single source of truth for quality score conversion.
        
        Args:
            raw_score: Raw quality score in any format
            
        Returns:
            float: Normalized quality score in 0-100 scale
        """
        if raw_score is None:
            return 0.0
            
        try:
            score = float(raw_score)
            
            if score <= 2.0:
                # Old format (0.0-2.0) - convert to 0-100
                normalized = round(score * 100, 1)
                # Cap at 100% maximum
                normalized = min(100.0, normalized)
                logger.debug(f"Converting old quality score: {score} -> {normalized}")
                return normalized
            elif score > 100:
                # Already converted but exceeds 100% - cap it
                logger.debug(f"Capping quality score: {score} -> 100.0")
                return 100.0
            else:
                # Already in 0-100 format
                return round(score, 1)
                
        except (ValueError, TypeError):
            logger.warning(f"Invalid quality score format: {raw_score}, using 0.0")
            return 0.0

    def _validate_uploaded_file(self, file) -> Dict:
        """Validate uploaded file meets requirements."""
        if not file or not file.filename:
            return {'valid': False, 'message': 'No file provided'}
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in self.supported_extensions:
            return {
                'valid': False, 
                'message': f'Unsupported file type. Supported: {", ".join(self.supported_extensions)}'
            }
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            return {
                'valid': False,
                'message': f'File too large. Maximum size: {self.max_file_size // (1024*1024)}MB'
            }
        
        if file_size == 0:
            return {'valid': False, 'message': 'File is empty'}
        
        return {'valid': True, 'message': 'File validation passed'}

    def _save_uploaded_file(self, file) -> Optional[str]:
        """Save uploaded file to temporary location."""
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(self.upload_path, unique_filename)
            
            file.save(file_path)
            logger.info(f"File saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return None

    def _save_analysis_data(self, processing_results: Dict, original_filename: str) -> Dict:
        """
        Save analysis data from document processing.
        
        Args:
            processing_results: Dictionary containing processing results
            original_filename: Name of the original uploaded file
                
        Returns:
            Dict containing saved analysis data
        """
        try:
            # Create analysis directory if it doesn't exist
            analysis_dir = os.path.join('data', 'analysis')
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Generate a unique ID for this analysis
            document_id = processing_results.get('document_id')
            if not document_id:
                document_id = f"doc_{int(time.time())}"
                
            # Prepare analysis data to save
            analysis_data = {
                'document_id': document_id,
                'original_filename': original_filename,
                'processing_date': datetime.now().isoformat(),
                'analysis_summary': {
                    'word_count': processing_results.get('word_count', 0),
                    'character_count': processing_results.get('character_count', 0),
                    'quality_score': processing_results.get('quality_assessment', {}).get('total_score', 0),
                    'insights_count': len(processing_results.get('extracted_insights', [])),
                    'key_themes': processing_results.get('key_themes', []),
                    'recommendations': processing_results.get('recommendations', [])
                },
                'full_analysis': processing_results
            }
            
            # Save to JSON file
            analysis_file = os.path.join(analysis_dir, f"{document_id}.json")
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error saving analysis data: {str(e)}")
            # Return minimal analysis data with error information
            return {
                'document_id': document_id if 'document_id' in locals() else 'unknown',
                'original_filename': original_filename,
                'processing_date': datetime.now().isoformat(),
                'error': f"Failed to save analysis data: {str(e)}"
            }

    def _compile_final_results(self, processing_results: Dict, 
                             integration_results: Dict, original_filename: str,
                             analysis_data: Dict = None) -> Dict:
        """
        Compile comprehensive results for admin interface.
        
        Args:
            processing_results: Results from document processing
            integration_results: Results from knowledge base integration
            original_filename: Name of the original uploaded file
            analysis_data: Optional pre-saved analysis data
            
        Returns:
            Dict containing compiled results for the admin interface
        """
        quality_assessment = processing_results.get('quality_assessment', {})
        
        # Determine overall status
        if integration_results.get('status') == 'success':
            overall_status = 'integrated_successfully'
        elif integration_results.get('status') == 'manual_review_required':
            overall_status = 'requires_review'
        else:
            overall_status = 'integration_failed'
        
        # Prepare base results
        results = {
            'status': overall_status,
            'original_filename': original_filename,
            'document_id': processing_results.get('document_id'),
            'processing_date': datetime.now().isoformat(),
            
            # Quality metrics
            'quality_score': quality_assessment.get('total_score', 0),
            'confidence_level': quality_assessment.get('confidence_level'),
            'auto_approved': quality_assessment.get('auto_approve', False),
            
            # Content metrics
            'insights_extracted': len(processing_results.get('extracted_insights', [])),
            'content_length': processing_results.get('text_content_length', 0),
            'word_count': processing_results.get('word_count', 0),
            'character_count': processing_results.get('character_count', 0),
            
            # Integration results
            'integration_action': integration_results.get('details', {}).get('action_taken'),
            'integration_message': integration_results.get('message'),
            
            # Analysis data if available
            'analysis_data': analysis_data or {},
            
            # Detailed results for admin review
            'detailed_results': {
                'processing': processing_results,
                'integration': integration_results
            },
            
            # Admin interface elements
            'admin_summary': self._generate_admin_summary(
                processing_results, integration_results
            ),
            'next_steps': self._generate_next_steps(integration_results)
        }
        
        # Add any additional analysis data
        if analysis_data and 'analysis_summary' in analysis_data:
            results.update({
                'key_themes': analysis_data['analysis_summary'].get('key_themes', []),
                'recommendations': analysis_data['analysis_summary'].get('recommendations', [])
            })
        
        return results

    def _generate_admin_summary(self, processing_results: Dict, integration_results: Dict) -> str:
        """Generate human-readable summary for admin interface."""
        quality_score = processing_results.get('quality_assessment', {}).get('total_score', 0)
        insights_count = len(processing_results.get('extracted_insights', []))
        integration_status = integration_results.get('status')
        
        if integration_status == 'success':
            action = integration_results.get('details', {}).get('action_taken', 'processed')
            return (f"Document successfully processed with quality score {quality_score:.1%}. "
                   f"Extracted {insights_count} insights and {action.replace('_', ' ')}.")
        
        elif integration_status == 'manual_review_required':
            return (f"Document processed with quality score {quality_score:.1%} but requires "
                   f"manual review. {insights_count} insights extracted and ready for review.")
        
        else:
            return (f"Document processing completed but integration failed. "
                   f"Quality score: {quality_score:.1%}, Insights: {insights_count}")

    def _generate_next_steps(self, integration_results: Dict) -> List[str]:
        """Generate recommended next steps for admin."""
        status = integration_results.get('status')
        
        if status == 'success':
            return [
                "Document successfully integrated into knowledge base",
                "Review integrated insights in knowledge base",
                "Consider updating policy recommendations if needed"
            ]
        
        elif status == 'manual_review_required':
            return [
                "Review extracted insights for quality and relevance",
                "Decide whether to include document in knowledge base",
                "Consider merging with existing documents if appropriate"
            ]
        
        else:
            return [
                "Review processing errors and document quality",
                "Consider reprocessing with corrected metadata",
                "Contact system administrator if issues persist"
            ]

    def _generate_processing_result(self, status: str, message: str) -> Dict:
        """Generate standardised processing result."""
        return {
            'status': status,
            'message': message,
            'processing_date': datetime.now().isoformat(),
            'quality_score': 0.0,
            'insights_extracted': 0,
            'admin_summary': message,
            'next_steps': ['Review error message and retry processing'],
            'detailed_results': {
                'processing': {
                    'quality_assessment': {
                        'dimension_scores': {},
                        'overall_score': 0.0,
                        'total_score': 0.0,
                        'recommendation': 'Review document quality'
                    }
                },
                'file_info': {
                    'original_filename': '',
                    'file_size': 0,
                    'file_type': ''
                },
                'metadata': {}
            },
            'original_filename': 'Unknown',
            'confidence_level': 'low',
            'content_length': 0
        }

    def batch_process_directory(self, directory_path: str) -> List[Dict]:
        """Process multiple files from a directory (for admin batch operations)."""
        results = []
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return results
        
        # Get all supported files
        files_to_process = []
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        
        for filename in os.listdir(directory_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_extensions:
                files_to_process.append(os.path.join(directory_path, filename))
        
        logger.info(f"Found {len(files_to_process)} files to process in batch")
        
        # Process each file
        for file_path in files_to_process:
            try:
                processing_results = self.processor.process_document(file_path)
                integration_results = self.knowledge_manager.integrate_new_document(processing_results)
                
                final_result = self._compile_final_results(
                    processing_results, integration_results, os.path.basename(file_path)
                )
                results.append(final_result)
                logger.info(f"Successfully processed {file_path}")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results.append({
                    'status': 'error',
                    'file': file_path,
                    'error': str(e)
                })
                results.append(self._generate_processing_result(
                    'error', f'Failed to process {os.path.basename(file_path)}: {str(e)}'
                ))
        
        return results

    def process_uploaded_file(self, file, metadata: Dict) -> Dict:
        """
        Main method to process uploaded file with metadata.
        
        Orchestrates the complete workflow: validation, saving, processing, integration.
        """
        try:
            logger.info(f"Processing uploaded file: {file.filename}")
            
            # Step 1: Validate uploaded file
            validation_result = self._validate_uploaded_file(file)
            if not validation_result.get('valid'):
                return self._generate_processing_result(
                    'validation_failed', validation_result.get('message')
                )
            
            # Step 2: Save uploaded file temporarily
            file_path = self._save_uploaded_file(file)
            if not file_path:
                return self._generate_processing_result(
                    'save_failed', 'Failed to save uploaded file'
                )
            
            # Step 3: Process document through pipeline
            processing_results = self.processor.process_document(file_path, metadata)
            
            if processing_results.get('status') == 'error':
                return self._generate_processing_result(
                    'processing_failed', 
                    processing_results.get('error_message', 'Processing failed')
                )
            
            # Step 4: Attempt integration if quality is sufficient
            integration_results = self.knowledge_manager.integrate_new_document(processing_results)
            
            # Step 5: Save analysis data before cleanup
            analysis_data = self._save_analysis_data(processing_results, file.filename)
            
            # Step 6: Clean up temporary file
            self._cleanup_temporary_file(file_path)
            
            # Step 7: Compile comprehensive results
            final_results = self._compile_final_results(
                processing_results, integration_results, file.filename, analysis_data
            )
            
            logger.info(f"File processing completed: {final_results.get('status')}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            return self._generate_processing_result('error', str(e))
    
    def _cleanup_temporary_file(self, file_path: str):
        """Clean up temporary uploaded file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary file {file_path}: {str(e)}")

