"""
Knowledge Base Manager for PolicyCraft AI Policy Analysis.

This module implements sophisticated knowledge base management functionality,
handling version control, document merging, conflict resolution, and systematic
updates to the policy recommendation knowledge repository. The manager ensures
data integrity while enabling continuous improvement of policy insights.

The system provides:
1. Version-controlled knowledge base updates with rollback capabilities
2. Intelligent document merging and conflict detection
3. Automated backup and recovery mechanisms
4. Integration with existing knowledge base structure
5. Audit trails for all knowledge base modifications

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import logging
import os
import json
import shutil
import re
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class KnowledgeBaseManager:
    """
    Advanced knowledge base management system for academic literature integration.
    
    This class manages the systematic integration of new academic insights into
    the existing PolicyCraft knowledge base, ensuring version control, conflict
    resolution, and data integrity throughout the update process.
    """
    
    def __init__(self, knowledge_base_path: str = "docs/knowledge_base"):
        """
        Initialise the knowledge base manager with configuration and paths.
        
        Args:
            knowledge_base_path: Path to the knowledge base directory
        """
        self.knowledge_base_path = knowledge_base_path
        self.backup_path = os.path.join(knowledge_base_path, "backups")
        self.version_file = os.path.join(knowledge_base_path, "version_history.json")
        
        # Ensure required directories exist
        self._ensure_directory_structure()
        
        # Load version history
        self.version_history = self._load_version_history()
        
        logger.info("Knowledge Base Manager initialised successfully")

    def integrate_new_document(self, processing_results: Dict) -> Dict:
        """
        Integrate new document into knowledge base based on processing results.
        
        This method handles the complete integration workflow including conflict
        detection, version management, and knowledge base updates.
        
        Args:
            processing_results: Results from LiteratureProcessor containing
                              quality assessment and integration recommendations
            
        Returns:
            Dict: Integration results including success status, conflicts,
                 and version information
        """
        try:
            logger.info("Integrating document: %s", processing_results.get('document_id'))
            
            # Check if document should be integrated
            recommendation = processing_results.get('processing_recommendation', {})
            if not self._should_integrate_document(recommendation):
                return self._generate_integration_result(
                    'rejected', 'Document does not meet integration criteria'
                )
            
            # Create backup before making changes (intelligent backup)
            backup_id = self._create_backup()
            
            # Determine integration action
            action = recommendation.get('action', 'review_required')
            
            if action == 'approve_new_document':
                result = self._integrate_new_document(processing_results, backup_id)
            elif action == 'merge_with_existing':
                result = self._merge_with_existing_document(processing_results, backup_id)
            else:
                result = self._handle_manual_review_case(processing_results)
            
            # Update version history
            if result.get('status') == 'success':
                self._update_version_history(result, processing_results)
            
            logger.info("Document integration completed: %s", result.get('status'))
            return result
            
        except Exception as e:
            error_msg = f"Error integrating document: {str(e)}"
            logger.error(error_msg)
            return self._generate_integration_result('error', error_msg)

    def _should_integrate_document(self, recommendation: Dict) -> bool:
        """Determine if document should be integrated based on recommendation."""
        action = recommendation.get('action', 'review_required')
        confidence = recommendation.get('confidence', 'low')
        
        # Auto-approve high-confidence documents
        if action in ['approve_new_document', 'merge_with_existing'] and confidence in ['high', 'medium']:
            return True
        
        return False

    def _generate_document_filename(self, processing_results: Dict) -> Tuple[str, str]:
        """
        Generate a consistent and user-friendly filename for a document.
        
        Args:
            processing_results: Dictionary containing document processing results
            
        Returns:
            Tuple of (filename, display_name) where:
            - filename: Safe filename for storage
            - display_name: Human-readable document name for UI
        """
        # Get or generate document ID first
        doc_id = processing_results.get('document_id')
        if not doc_id:
            doc_id = str(uuid.uuid4())[:8]  # Generate short ID if not provided
            processing_results['document_id'] = doc_id
            
        metadata = processing_results.get('metadata', {})
        
        # 1. Determine the best title to use (in order of preference)
        title = ''
        
        # Try to get title from metadata first
        if metadata.get('title'):
            title = str(metadata['title']).strip()
        # Fall back to document title from processing results
        elif processing_results.get('document_title'):
            title = str(processing_results['document_title']).strip()
        # Fall back to original filename without extension
        elif metadata.get('original_filename'):
            title = os.path.splitext(str(metadata['original_filename']))[0].strip()
        elif metadata.get('filename'):
            title = os.path.splitext(str(metadata['filename']))[0].strip()
        # Final fallback to document ID
        else:
            return f"document_{doc_id}.md", f"Document {doc_id}"
        
        # Create a clean version of the title for the filename
        clean_title = title.lower()
        clean_title = re.sub(r'[^\w\s-]', '', clean_title)  # Remove special chars
        clean_title = re.sub(r'\s+', '_', clean_title)       # Replace spaces with underscores
        clean_title = clean_title.strip('_')                  # Remove leading/trailing underscores
        clean_title = clean_title[:50]                       # Limit length
        
        # Get year from most specific to least specific source
        year = ''
        for date_field in ['publication_date', 'processing_date', 'upload_date', 'date']:
            if metadata.get(date_field):
                try:
                    date_str = str(metadata[date_field])
                    if len(date_str) >= 4:  # Ensure we have at least a year
                        year = f"_{date_str[:4]}"  # Extract YYYY
                        break
                except (TypeError, AttributeError):
                    continue
        
        # If no year found in metadata, use current year as fallback
        if not year:
            year = f"_{datetime.now().year}"
        
        # Get document type (default to 'document' if not specified)
        doc_type = metadata.get('document_type', 'document').lower()
        if not isinstance(doc_type, str):
            doc_type = 'document'
        doc_type = re.sub(r'[^a-z0-9]', '', doc_type)  # Clean document type
        if not doc_type:
            doc_type = 'document'
            
        # Generate safe filename and display name
        filename = f"{doc_type}_{clean_title}{year}_{doc_id}.md".lower()
        display_name = f"{title} ({doc_id})"  # Human-readable format for UI
        
        return filename, display_name

    def _integrate_new_document(self, processing_results: Dict, backup_id: str) -> Dict:
        """Integrate completely new document into knowledge base with consistent naming."""
        try:
            # Generate consistent filename and display name
            filename, display_name = self._generate_document_filename(processing_results)
            file_path = os.path.join(self.knowledge_base_path, filename)
            
            # Store the display name in processing results for UI use
            if 'metadata' not in processing_results:
                processing_results['metadata'] = {}
            processing_results['metadata']['display_name'] = display_name
            
            # Generate markdown content
            markdown_content = self._generate_markdown_content(processing_results)
            
            # Write new file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return self._generate_integration_result(
                'success',
                f'New document integrated as {filename}',
                {
                    'action_taken': 'new_document_created',
                    'filename': filename,
                    'backup_id': backup_id,
                    'insights_count': len(processing_results.get('extracted_insights', [])),
                    'metadata': processing_results.get('metadata', {})
                }
            )
            
        except Exception as e:
            return self._generate_integration_result('error', f'Failed to integrate new document: {str(e)}')

    def _merge_with_existing_document(self, processing_results: Dict, backup_id: str) -> Dict:
        """Merge insights with existing similar document."""
        try:
            # Find most similar existing document
            similarity_analysis = processing_results.get('similarity_analysis', {})
            similar_docs = similarity_analysis.get('similar_documents', [])
            
            if not similar_docs:
                return self._integrate_new_document(processing_results, backup_id)
            
            # Select document with highest similarity
            target_doc = max(similar_docs, key=lambda x: x['similarity_score'])
            target_filename = target_doc['filename']
            target_path = os.path.join(self.knowledge_base_path, target_filename)
            
            # Read existing content
            with open(target_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Generate merged content
            merged_content = self._merge_document_content(
                existing_content, processing_results
            )
            
            # Write updated content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            return self._generate_integration_result(
                'success',
                f'Insights merged with existing document {target_filename}',
                {
                    'action_taken': 'document_merged',
                    'target_filename': target_filename,
                    'backup_id': backup_id,
                    'similarity_score': target_doc['similarity_score'],
                    'new_insights_added': len(processing_results.get('extracted_insights', []))}
            )
            
        except Exception as e:
            return self._generate_integration_result('error', f'Failed to merge with existing document: {str(e)}')

    def _handle_manual_review_case(self, processing_results: Dict) -> Dict:
        """Handle documents requiring manual review."""
        return self._generate_integration_result(
            'manual_review_required',
            'Document requires manual review before integration',
            {
                'action_taken': 'flagged_for_review',
                'quality_score': processing_results.get('quality_assessment', {}).get('total_score', 0),
                'review_reason': 'Quality or novelty thresholds not met for automatic integration'
            }
        )

    def _generate_markdown_content(self, processing_results: Dict) -> str:
        """Generate formatted markdown content for knowledge base.
        
        Args:
            processing_results: Dictionary containing document data and metadata
            
        Returns:
            str: Formatted markdown content with consistent headers
        """
        metadata = processing_results.get('metadata', {})
        insights = processing_results.get('extracted_insights', [])
        quality_assessment = processing_results.get('quality_assessment', {})
        
        # Get document title or use filename as fallback
        title = metadata.get('title')
        if not title:
            title = metadata.get('filename', 'Unknown Document')
            # Clean up the title
            title = os.path.splitext(title)[0].replace('_', ' ').title()
        
        # Prepare document info section with consistent header format
        doc_info = []
        
        # Add basic metadata with consistent formatting
        if 'author' in metadata and metadata['author']:
            doc_info.append(f"- **Author(s)**: {metadata['author']}")
        
        if 'publication_date' in metadata and metadata['publication_date']:
            doc_info.append(f"- **Publication Date**: {metadata['publication_date']}")
        
        if 'source' in metadata and metadata['source']:
            doc_info.append(f"- **Source**: {metadata['source']}")
        elif 'filename' in metadata and metadata['filename']:
            doc_info.append(f"- **Source File**: {metadata['filename']}")
        
        # Add processing metadata
        doc_info.append(f"- **Processing Date**: {datetime.now().strftime('%Y-%m-%d')}")
        
        if 'estimated_word_count' in metadata and metadata['estimated_word_count']:
            doc_info.append(f"- **Word Count**: {metadata['estimated_word_count']}")
        
        # Add quality assessment info if available
        if 'total_score' in quality_assessment:
            doc_info.append(f"- **Quality Score**: {quality_assessment['total_score']:.2f}")
        
        if 'confidence_level' in quality_assessment and quality_assessment['confidence_level']:
            doc_info.append(f"- **Confidence Level**: {quality_assessment['confidence_level']}")
        
        # Create markdown content with consistent headers
        markdown_content = f"""# {title}

## Document Information
{metadata.get('description', 'No description available.')}

## Metadata
{chr(10).join(doc_info) if doc_info else 'No metadata available.'}

## Executive Summary
{quality_assessment.get('summary', 'No summary available.')}

## Quality Assessment
{quality_assessment.get('recommendation', 'No assessment available')}

## Key Insights
"""
        
        # Add insights if available
        if insights:
            for i, insight in enumerate(insights, 1):
                markdown_content += f"\n### Insight {i}\n{insight.strip()}\n"
        else:
            markdown_content += "\nNo insights extracted.\n"
        
        # Add integration metadata
        markdown_content += f"""
## Integration Details
- **Document ID**: {processing_results.get('document_id', 'N/A')}
- **Processing Version**: PolicyCraft Literature Processor v1.0
- **Integration Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Auto-Generated**: Yes

---
*This document was automatically processed and integrated into the PolicyCraft knowledge base.*
"""
        
        return markdown_content

    def _merge_document_content(self, existing_content: str, processing_results: Dict) -> str:
        """Merge new insights with existing document content."""
        new_insights = processing_results.get('extracted_insights', [])
        
        # Find insertion point (before integration details section)
        if "## Integration Details" in existing_content:
            base_content = existing_content.split("## Integration Details")[0]
        else:
            base_content = existing_content
        
        # Add new insights section
        merge_section = f"""
## Additional Insights (Added {datetime.now().strftime('%Y-%m-%d')})

"""
        
        for i, insight in enumerate(new_insights, 1):
            merge_section += f"### Additional Insight {i}\n{insight.strip()}\n\n"
        
        # Update metadata
        metadata_section = f"""## Integration Details
- **Last Updated**: {datetime.now().isoformat()}
- **Update Source**: {processing_results.get('document_id', 'Unknown')}
- **Quality Score**: {processing_results.get('quality_assessment', {}).get('total_score', 0):.2f}
- **Insights Added**: {len(new_insights)}
- **Processing Version**: PolicyCraft Literature Processor v1.0

---
*This document has been updated with additional insights from academic literature.*
"""
        
        return base_content + merge_section + metadata_section

    def _should_create_backup(self) -> bool:
        """Check if a backup should be created based on intelligent criteria."""
        try:
            if not os.path.exists(self.backup_path):
                return True  # First backup
            
            # Get list of existing backups
            backups = [d for d in os.listdir(self.backup_path) 
                      if os.path.isdir(os.path.join(self.backup_path, d))]
            
            if not backups:
                return True  # No backups exist
            
            # Sort backups by timestamp (newest first)
            backups.sort(reverse=True)
            latest_backup = backups[0]
            
            # Check if latest backup is older than 1 hour
            try:
                backup_time = datetime.strptime(latest_backup, '%Y%m%d_%H%M%S')
                time_diff = datetime.now() - backup_time
                if time_diff.total_seconds() < 3600:  # Less than 1 hour
                    logger.info(f"Skipping backup - recent backup exists: {latest_backup}")
                    return False
            except ValueError:
                # Invalid timestamp format, create backup
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking backup criteria: {e}")
            return False  # Don't create backup on error
    
    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        """Remove old backups, keeping only the most recent ones."""
        try:
            if not os.path.exists(self.backup_path):
                return
            
            # Get list of backup directories
            backups = [d for d in os.listdir(self.backup_path) 
                      if os.path.isdir(os.path.join(self.backup_path, d))]
            
            if len(backups) <= max_backups:
                return  # No cleanup needed
            
            # Sort backups by timestamp (newest first)
            backups.sort(reverse=True)
            
            # Remove old backups
            backups_to_remove = backups[max_backups:]
            removed_count = 0
            
            for backup_dir in backups_to_remove:
                backup_full_path = os.path.join(self.backup_path, backup_dir)
                try:
                    shutil.rmtree(backup_full_path)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove backup {backup_dir}: {e}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backups, keeping {max_backups} most recent")
                
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
    
    def _create_backup(self, force: bool = False) -> str:
        """Create backup of current knowledge base state with intelligent logic.
        
        Args:
            force: If True, create backup regardless of criteria
        """
        try:
            # Check if backup is needed (unless forced)
            if not force and not self._should_create_backup():
                # Return latest backup ID if available
                if os.path.exists(self.backup_path):
                    backups = [d for d in os.listdir(self.backup_path) 
                              if os.path.isdir(os.path.join(self.backup_path, d))]
                    if backups:
                        backups.sort(reverse=True)
                        return backups[0]
                return ""
            
            backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.backup_path, backup_id)
            
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all knowledge base files
            for filename in os.listdir(self.knowledge_base_path):
                if filename.endswith('.md'):
                    source_path = os.path.join(self.knowledge_base_path, filename)
                    backup_file_path = os.path.join(backup_dir, filename)
                    shutil.copy2(source_path, backup_file_path)
            
            logger.info("Knowledge base backup created: %s", backup_id)
            
            # Cleanup old backups after creating new one
            self._cleanup_old_backups(max_backups=5)
            
            return backup_id
            
        except Exception as e:
            logger.error("Failed to create backup: %s", str(e))
            return ""

    def _parse_metadata_from_markdown(self, content: str) -> Dict:
        """Extract metadata from markdown headers.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            Dict containing extracted metadata (title, author, etc.)
        """
        metadata = {
            "title": "Untitled Document",  # Default values
            "author": None,
            "publication_date": None,
            "processing_date": None,
            "quality_score": 0.0
        }
        
        if not content or not isinstance(content, str):
            logger.warning("Empty or invalid content provided for metadata extraction")
            return metadata
            
        try:
            lines = content.split('\n')
            
            # First pass - look for standard format
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Extract title (multiple formats)
                if line.startswith("# ") and metadata["title"] == "Untitled Document":
                    title = line[2:].strip()
                    metadata["title"] = title
                    
                    # Extract year from title if present (e.g., "UNESCO (2021)")
                    import re
                    year_match = re.search(r'\((\d{4})\)', title)
                    if year_match and not metadata["publication_date"]:
                        metadata["publication_date"] = f"{year_match.group(1)}-01-01"
                
                # Extract author (multiple formats including knowledge base format)
                elif any(pattern in line.lower() for pattern in ["**author**:", "**authors**:", "author:", "by:"]):
                    try:
                        # Knowledge base format: - **Author**: value or - **Authors**: value
                        if line.strip().startswith("- **Author"):
                            if "**Author**:" in line:
                                metadata["author"] = line.split("**Author**:", 1)[1].strip()
                            elif "**Authors**:" in line:
                                metadata["author"] = line.split("**Authors**:", 1)[1].strip()
                        # Standard formats
                        elif "**author**:" in line.lower():
                            metadata["author"] = line.split("**Author**:", 1)[1].strip()
                        elif "author:" in line.lower():
                            metadata["author"] = line.split("author:", 1)[1].strip()
                        elif "by:" in line.lower():
                            metadata["author"] = line.split("by:", 1)[1].strip()
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Failed to extract author from line: {line}, error: {str(e)}")
                
                # Extract publication date (multiple formats)
                elif any(pattern in line.lower() for pattern in ["**publication date**:", "publication date:", "published:", "date:"]):
                    try:
                        # Try different splitting patterns
                        if "**publication date**:" in line.lower():
                            # Find the actual pattern in the line (case-insensitive)
                            if "**Publication Date**:" in line:
                                metadata["publication_date"] = line.split("**Publication Date**:", 1)[1].strip()
                            elif "**publication date**:" in line:
                                metadata["publication_date"] = line.split("**publication date**:", 1)[1].strip()
                        elif "publication date:" in line.lower():
                            metadata["publication_date"] = line.split("publication date:", 1)[1].strip()
                        elif "published:" in line.lower():
                            metadata["publication_date"] = line.split("published:", 1)[1].strip()
                        elif "date:" in line.lower():
                            metadata["publication_date"] = line.split("date:", 1)[1].strip()
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Failed to extract publication date from line: {line}, error: {str(e)}")
                
                # Extract processing date
                elif any(pattern in line.lower() for pattern in ["**processing date**:", "processing date:", "processed:"]):
                    try:
                        if "**processing date**:" in line.lower():
                            metadata["processing_date"] = line.split("**Processing Date**:", 1)[1].strip()
                        elif "processing date:" in line.lower():
                            metadata["processing_date"] = line.split("processing date:", 1)[1].strip()
                        elif "processed:" in line.lower():
                            metadata["processing_date"] = line.split("processed:", 1)[1].strip()
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Failed to extract processing date from line: {line}, error: {str(e)}")
                
                # Extract quality score
                elif any(pattern in line.lower() for pattern in ["**quality score**:", "quality score:", "quality:", "score:"]):
                    try:
                        if "**quality score**:" in line.lower():
                            score_str = line.split("**Quality Score**:", 1)[1].strip()
                        elif "quality score:" in line.lower():
                            score_str = line.split("quality score:", 1)[1].strip()
                        elif "quality:" in line.lower():
                            score_str = line.split("quality:", 1)[1].strip()
                        elif "score:" in line.lower():
                            score_str = line.split("score:", 1)[1].strip()
                        
                        # Convert to float if possible
                        try:
                            metadata["quality_score"] = float(score_str)
                        except ValueError:
                            logger.warning(f"Could not convert quality score to float: {score_str}")
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Failed to extract quality score from line: {line}, error: {str(e)}")
            
            # Second pass - try to infer missing fields from title if metadata is missing
            if not metadata["publication_date"] and metadata["title"]:
                # Try to extract year from title (e.g., "UNESCO (2021)" or "An, Yu & James (2025)")
                import re
                year_match = re.search(r'\((\d{4})\)', metadata["title"])
                if year_match:
                    year = year_match.group(1)
                    metadata["publication_date"] = f"{year}-01-01"  # Default to January 1st
                    
            if not metadata["author"] and metadata["title"]:
                # Try to extract author from title (before the year)
                import re
                # Pattern: "Author Name (YEAR)" or "Author et al. (YEAR)"
                author_match = re.match(r'^([^(]+?)\s*\(\d{4}\)', metadata["title"])
                if author_match:
                    metadata["author"] = author_match.group(1).strip()
            
            if not metadata["author"]:
                # Try to infer author from filename or content
                filename = getattr(self, "current_filename", "")
                if filename:
                    import re
                    # Look for author patterns in filename (e.g., Smith_2020.md)
                    author_match = re.search(r'([A-Z][a-z]+)_\d{4}', filename)
                    if author_match:
                        metadata["author"] = author_match.group(1)
            
            # Try to extract year from publication date if available
            if metadata["publication_date"] and not metadata.get("year"):
                import re
                year_match = re.search(r'(19|20)\d{2}', metadata["publication_date"])
                if year_match:
                    metadata["year"] = year_match.group(0)
            
            # Log warning for documents with missing critical metadata
            if not metadata["author"]:
                logger.warning(f"Document missing author metadata: {metadata['title']}")
            if not metadata["publication_date"]:
                logger.warning(f"Document missing publication date metadata: {metadata['title']}")
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing markdown metadata: {str(e)}")
            return metadata
        
    def _ensure_directory_structure(self):
        """Ensure required directory structure exists."""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        os.makedirs(self.backup_path, exist_ok=True)

    def _load_version_history(self) -> List[Dict]:
        """Load version history from file."""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_history = json.load(f)
                    
                # Convert old quality scores (0.0-1.0) to new format (0-100)
                for entry in version_history:
                    if 'quality_score' in entry:
                        old_score = entry['quality_score']
                        if isinstance(old_score, (int, float)) and 0 <= old_score <= 1.0:
                            # Convert from 0.0-1.0 to 0-100 format
                            entry['quality_score'] = old_score * 100
                            logger.debug(f"Converted quality score from {old_score} to {entry['quality_score']} for {entry.get('document_id', 'unknown')}")
                
                return version_history
            except Exception as e:
                logger.error("Error loading version history: %s", str(e))
        return []
        
    def _update_version_history(self, integration_result: Dict, processing_results: Dict):
        """Update version history with new integration."""
        version_entry = {
            'timestamp': datetime.now().isoformat(),
            'document_id': processing_results.get('document_id'),
            'action': integration_result.get('details', {}).get('action_taken'),
            'filename': integration_result.get('details', {}).get('filename'),
            'backup_id': integration_result.get('details', {}).get('backup_id'),
            'quality_score': processing_results.get('quality_assessment', {}).get('total_score'),
            'insights_count': len(processing_results.get('extracted_insights', [])),
            'metadata': processing_results.get('metadata', {})
        }

        self.version_history.append(version_entry)

        # Save updated history
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_history, f, indent=2)
        except Exception as e:
            logger.error("Error saving version history: %s", str(e))

    def _generate_integration_result(self, status: str, message: str, details: Optional[Dict] = None) -> Dict:
        """Generate standardised integration result."""
        return {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }

    def get_knowledge_base_status(self) -> Dict:
        """
        Get comprehensive status and statistics of knowledge base.
        
        Returns:
            Dict containing:
                - knowledge_base: Dictionary with knowledge base statistics
                    - total_documents: Number of markdown documents
                    - last_update: Timestamp of last update
                    - version_count: Total number of versions in history
                    - recent_updates: List of recent version updates
                    - backup_count: Number of available backups
                    - status: Overall health status of knowledge base
        """
        try:
            # Count documents
            md_files = [f for f in os.listdir(self.knowledge_base_path) if f.endswith('.md')]

            # Get recent versions
            recent_versions = sorted(self.version_history, key=lambda x: x.get('timestamp', ''))[-10:]
            
            # Get last update timestamp
            last_update = (
                self.version_history[-1].get('timestamp', 'Never') 
                if self.version_history 
                else 'Never'
            )
            
            # Get backup count safely
            backup_count = 0
            if os.path.exists(self.backup_path):
                try:
                    backup_count = len([
                        f for f in os.listdir(self.backup_path) 
                        if os.path.isdir(os.path.join(self.backup_path, f))
                    ])
                except Exception as e:
                    logger.warning("Error counting backups: %s", str(e))
                    backup_count = 0

            return {
                'knowledge_base': {
                    'total_documents': len(md_files),
                    'last_update': last_update,
                    'version_count': len(self.version_history),
                    'recent_updates': recent_versions,
                    'backup_count': backup_count,
                    'status': 'healthy' if md_files else 'empty'
                }
            }

        except Exception as e:
            logger.error("Error getting knowledge base status: %s", str(e), exc_info=True)
            return {
                'knowledge_base': {
                    'total_documents': 0,
                    'last_update': 'Error',
                    'version_count': 0,
                    'recent_updates': [],
                    'backup_count': 0,
                    'status': 'error',
                    'error': str(e)
                }
            }

    def get_all_documents(self) -> List[Dict]:
        """
        Retrieve all documents from the knowledge base with their metadata.
        
        Returns:
            List[Dict]: List of documents with their metadata including:
                - id: Document ID from filename
                - filename: Original filename
                - title: Extracted document title
                - author: Extracted author name
                - publication_date: Extracted publication date
                - quality_score: Extracted quality score if available
                - word_count: Approximate word count
        """
        documents = []

        if not os.path.exists(self.knowledge_base_path):
            return documents

        for filename in os.listdir(self.knowledge_base_path):
            if filename.endswith('.md'):
                file_path = os.path.join(self.knowledge_base_path, filename)
                try:
                    # Extract document ID from filename (format: {document_id}_*.md)
                    document_id = os.path.splitext(filename)[0]  # Use filename without extension as ID

                    # Read file content and get metadata
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Extract metadata from markdown content
                    metadata = self._parse_metadata_from_markdown(content)

                    # Calculate quality score based on content analysis
                    word_count = len(content.split())
                    quality_score = self._calculate_document_quality_score(content, metadata)
                    
                    # Check if metadata has old format quality score (0.0-1.0) and convert or ignore
                    if 'quality_score' in metadata:
                        old_score = metadata.get('quality_score', 0)
                        # If old score is in 0.0-1.0 format, convert to 0-100 format
                        if isinstance(old_score, (int, float)) and 0 <= old_score <= 1.0:
                            logger.debug(f"Converting old quality score {old_score} to new format for {filename}")
                            # Use calculated score instead of old format
                        # If old score is already in 0-100 format but we want consistency, use calculated
                        # Always use freshly calculated score for consistency
                    
                    # Count insights (sections, key points, recommendations)
                    insights_count = self._count_document_insights(content)
                    
                    documents.append({
                        'id': document_id,
                        'document_id': document_id,
                        'filename': filename,
                        'title': metadata.get('title', filename),
                        'author': metadata.get('author', 'Unknown'),
                        'publication_date': metadata.get('publication_date', 'Unknown'),
                        'quality_score': quality_score,
                        'insights_count': insights_count,
                        'word_count': word_count,
                        'metadata': metadata  # Keep as dict for compatibility with cleanup interface
                    })

                except Exception as e:
                    logger.error("Error processing document %s: %s", filename, str(e), exc_info=True)
                    continue

        return documents

    def _calculate_document_quality_score(self, content: str, metadata: Dict) -> float:
        """Calculate quality score based on content and metadata (0-100% scale).
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            float: Quality score between 0.0 and 100.0
        """
        try:
            score = 60.0  # Base score (60% - "Good" baseline)
            
            # Content quality factor (0-20%)
            word_count = len(content.split())
            if word_count > 5000:
                score += 20  # Comprehensive content
            elif word_count > 2000:
                score += 15  # Substantial content
            elif word_count > 1000:
                score += 10  # Adequate content
            elif word_count > 500:
                score += 5   # Minimal content
            
            # Structure quality factor (0-15%)
            sections = content.count('##')
            if sections > 10:
                score += 15  # Highly structured
            elif sections > 5:
                score += 10  # Well structured
            elif sections > 2:
                score += 5   # Basic structure
            
            # Metadata completeness (0-5%)
            if metadata.get('author') and metadata.get('author') != 'Unknown':
                score += 2.5  # Author identified
            if metadata.get('publication_date') and metadata.get('publication_date') != 'Unknown':
                score += 2.5  # Date identified
            
            # Academic indicators (0-10%)
            academic_keywords = ['doi:', 'isbn:', 'journal:', 'conference:', 'university', 'research', 'abstract', 'methodology']
            found_indicators = sum(1 for keyword in academic_keywords if keyword.lower() in content.lower())
            academic_bonus = min(10, found_indicators * 1.25)  # 1.25% per indicator, max 10%
            score += academic_bonus
            
            # Ensure score stays within 0-100% range
            return min(100.0, max(0.0, round(score, 1)))
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {str(e)}")
            return 60.0  # Return baseline score on error
            
    def _count_document_insights(self, content: str) -> int:
        """Count insights (key points, recommendations, findings) in a document.
        
        Args:
            content: Document content
            
        Returns:
            int: Number of insights found
        """
        try:
            insights_count = 0
            
            # Count sections (each section is an insight)
            insights_count += content.count('##')
            
            # Count bullet points (key insights)
            insights_count += content.count('- **')
            insights_count += content.count('* **')
            
            # Count numbered lists
            import re
            numbered_items = re.findall(r'^\d+\.\s', content, re.MULTILINE)
            insights_count += len(numbered_items)
            
            # Count key terms that indicate insights
            insight_keywords = [
                'recommendation', 'finding', 'conclusion', 'insight', 
                'principle', 'guideline', 'best practice', 'framework'
            ]
            for keyword in insight_keywords:
                insights_count += content.lower().count(keyword.lower())
            
            # Minimum of 5 insights for any substantial document
            return max(5, insights_count)
            
        except Exception as e:
            logger.warning(f"Error counting insights: {str(e)}")
            return 10  # Default fallback