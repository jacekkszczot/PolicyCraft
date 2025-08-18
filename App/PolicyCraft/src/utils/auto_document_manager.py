"""
Automatic Document Management System for PolicyCraft

This module automatically manages new regulatory documents added to the knowledge base:
- Scans for new documents in knowledge_base/
- Automatically adds them to academic_references.md
- Generates citation mappings for validation
- Ensures seamless integration of new regulatory sources

Author: PolicyCraft System
Date: 2025-08-13
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoDocumentManager:
    """
    Automatically manages new regulatory documents in the knowledge base.
    
    Features:
    - Scans knowledge_base/ for new documents
    - Auto-adds to academic_references.md
    - Generates citation mappings
    - Maintains validation consistency
    """
    
    def __init__(self, knowledge_base_path: str, academic_refs_path: str, validation_path: str):
        """
        Initialise the AutoDocumentManager.
        
        Args:
            knowledge_base_path: Path to docs/knowledge_base/
            academic_refs_path: Path to academic_references.md
            validation_path: Path to validation.py
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.academic_refs_path = Path(academic_refs_path)
        self.validation_path = Path(validation_path)
        
        # Regulatory document patterns
        self.regulatory_patterns = [
            r'.*act.*\d{4}.*',
            r'.*regulation.*\d{4}.*',
            r'.*directive.*\d{4}.*',
            r'.*law.*\d{4}.*',
            r'.*policy.*\d{4}.*',
            r'.*framework.*\d{4}.*',
            r'.*guidelines.*\d{4}.*'
        ]
        
        logger.info("AutoDocumentManager initialized")
    
    def scan_for_new_documents(self) -> List[Dict]:
        """
        Scan knowledge_base/ for new regulatory documents.
        
        Returns:
            List of new document metadata dictionaries
        """
        logger.info(f"Scanning {self.knowledge_base_path} for new documents...")
        
        # Get existing documents from academic_references.md
        existing_docs = self._get_existing_references()
        
        # Scan knowledge base directory
        new_documents = []
        
        if not self.knowledge_base_path.exists():
            logger.warning(f"Knowledge base path does not exist: {self.knowledge_base_path}")
            return new_documents
        
        for file_path in self.knowledge_base_path.glob("*.md"):
            # Skip backup directories
            if "backup" in str(file_path).lower():
                continue
                
            # Extract metadata from file
            metadata = self._extract_document_metadata(file_path)
            
            if metadata and self._is_regulatory_document(metadata):
                # Check if already exists in academic_references.md
                if not self._document_exists_in_references(metadata, existing_docs):
                    new_documents.append(metadata)
                    logger.info(f"Found new regulatory document: {metadata['title']}")
        
        logger.info(f"Found {len(new_documents)} new regulatory documents")
        return new_documents
    
    def _extract_document_metadata(self, file_path: Path) -> Optional[Dict]:
        """
        Extract metadata from a markdown document.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dictionary with document metadata or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first line (# Title format)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else file_path.stem
            
            # Extract year from title or filename
            year_match = re.search(r'\b(20\d{2})\b', title)
            year = year_match.group(1) if year_match else "2024"
            
            # Determine document type and organization
            doc_type, organization = self._classify_document(title, content)
            
            # Generate citation format
            citation = self._generate_citation(title, organization, year, file_path)
            
            return {
                'file_path': str(file_path),
                'filename': file_path.name,
                'title': title,
                'year': year,
                'organization': organization,
                'doc_type': doc_type,
                'citation': citation,
                'short_citation': self._generate_short_citation(title, year)
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _classify_document(self, title: str, content: str) -> Tuple[str, str]:
        """
        Classify document type and determine issuing organization.
        
        Args:
            title: Document title
            content: Document content
            
        Returns:
            Tuple of (document_type, organization)
        """
        title_lower = title.lower()
        
        # Determine organization
        if any(term in title_lower for term in ['eu', 'european union', 'european']):
            organization = "European Union"
        elif any(term in title_lower for term in ['uk', 'british', 'britain']):
            organization = "United Kingdom"
        elif any(term in title_lower for term in ['us', 'usa', 'united states']):
            organization = "United States"
        elif any(term in title_lower for term in ['unesco', 'un ']):
            organization = "UNESCO"
        elif any(term in title_lower for term in ['jisc']):
            organization = "Jisc"
        else:
            organization = "Regulatory Authority"
        
        # Determine document type
        if any(term in title_lower for term in ['act', 'law']):
            doc_type = "Legal Act"
        elif any(term in title_lower for term in ['regulation']):
            doc_type = "Regulation"
        elif any(term in title_lower for term in ['directive']):
            doc_type = "Directive"
        elif any(term in title_lower for term in ['guideline', 'guide']):
            doc_type = "Guidelines"
        elif any(term in title_lower for term in ['framework']):
            doc_type = "Framework"
        elif any(term in title_lower for term in ['policy']):
            doc_type = "Policy Document"
        else:
            doc_type = "Regulatory Document"
        
        return doc_type, organization
    
    def _generate_citation(self, title: str, organization: str, year: str, file_path: Path) -> str:
        """
        Generate APA-style citation for the document.
        
        Args:
            title: Document title
            organization: Issuing organization
            year: Publication year
            file_path: Path to the document file
            
        Returns:
            APA-style citation string
        """
        # Clean title for citation
        clean_title = title.replace(' - ', ': ').replace('(', '').replace(')', '')
        
        # Generate official link (placeholder)
        link = f"[Official Document](https://example.org/{file_path.stem})"
        
        citation = f"{organization}. ({year}). *{clean_title}*. | {link}"
        
        return citation
    
    def _generate_short_citation(self, title: str, year: str) -> str:
        """
        Generate short citation format for validation mapping.
        
        Args:
            title: Document title
            year: Publication year
            
        Returns:
            Short citation format
        """
        # Extract key terms for short citation
        if 'ai act' in title.lower():
            return f"EU AI Act ({year})"
        elif 'gdpr' in title.lower():
            return f"GDPR ({year})"
        elif 'data protection' in title.lower():
            return f"Data Protection Act ({year})"
        elif 'privacy' in title.lower():
            return f"Privacy Regulation ({year})"
        else:
            # Generic format: First significant word + year
            words = title.split()
            significant_words = [w for w in words if len(w) > 3 and w.lower() not in ['the', 'and', 'for', 'with']]
            if significant_words:
                return f"{significant_words[0]} ({year})"
            else:
                return f"Regulatory Document ({year})"
    
    def _is_regulatory_document(self, metadata: Dict) -> bool:
        """
        Determine if document is a regulatory document.
        
        Args:
            metadata: Document metadata dictionary
            
        Returns:
            True if document appears to be regulatory
        """
        title_lower = metadata['title'].lower()
        
        # Check against regulatory patterns
        for pattern in self.regulatory_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True
        
        # Check for regulatory keywords
        regulatory_keywords = [
            'regulation', 'act', 'law', 'directive', 'policy',
            'framework', 'guidelines', 'compliance', 'legal',
            'statutory', 'official', 'government', 'authority'
        ]
        
        return any(keyword in title_lower for keyword in regulatory_keywords)
    
    def _get_existing_references(self) -> List[str]:
        """
        Get list of existing references from academic_references.md.
        
        Returns:
            List of existing reference titles/citations
        """
        existing_refs = []
        
        try:
            with open(self.academic_refs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract citations from table rows
            table_rows = re.findall(r'\|\s*\d+\s*\|\s*(.+?)\s*\|', content)
            existing_refs.extend(table_rows)
            
        except Exception as e:
            logger.error(f"Error reading academic references: {e}")
        
        return existing_refs
    
    def _document_exists_in_references(self, metadata: Dict, existing_refs: List[str]) -> bool:
        """
        Check if document already exists in academic references.
        
        Args:
            metadata: Document metadata
            existing_refs: List of existing references
            
        Returns:
            True if document already exists
        """
        title_lower = metadata['title'].lower()
        
        for ref in existing_refs:
            if any(term in ref.lower() for term in title_lower.split()[:3]):
                return True
        
        return False
    
    def add_to_academic_references(self, new_documents: List[Dict]) -> bool:
        """
        Add new documents to academic_references.md.
        
        Args:
            new_documents: List of new document metadata
            
        Returns:
            True if successfully added
        """
        if not new_documents:
            logger.info("No new documents to add to academic references")
            return True
        
        try:
            # Read current content
            with open(self.academic_refs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the last table row number
            last_number = self._get_last_reference_number(content)
            
            # Generate new entries
            new_entries = []
            for i, doc in enumerate(new_documents):
                number = last_number + i + 1
                significance = self._generate_significance_text(doc)
                
                entry = f"| {number} | {doc['citation']} | {significance} |"
                new_entries.append(entry)
            
            # Insert before "# Short citation formats" section
            insert_point = content.find("# Short citation formats")
            if insert_point == -1:
                # If section not found, append at end
                insert_point = len(content)
                content += "\n"
            
            # Insert new entries
            new_content = (
                content[:insert_point] +
                "\n".join(new_entries) + "\n\n" +
                content[insert_point:]
            )
            
            # Write back to file
            with open(self.academic_refs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"Added {len(new_documents)} new documents to academic references")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to academic references: {e}")
            return False
    
    def _get_last_reference_number(self, content: str) -> int:
        """
        Get the last reference number from academic_references.md.
        
        Args:
            content: File content
            
        Returns:
            Last reference number
        """
        numbers = re.findall(r'\|\s*(\d+)\s*\|', content)
        return max([int(n) for n in numbers]) if numbers else 0
    
    def _generate_significance_text(self, metadata: Dict) -> str:
        """
        Generate significance text for the document.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Significance description
        """
        doc_type = metadata['doc_type']
        organization = metadata['organization']
        
        significance_templates = {
            "Legal Act": f"Legal framework from {organization} providing regulatory foundation for AI governance and institutional compliance.",
            "Regulation": f"Regulatory requirements from {organization} establishing compliance standards for AI implementation.",
            "Directive": f"Policy directive from {organization} guiding institutional AI adoption and governance practices.",
            "Guidelines": f"Official guidance from {organization} supporting evidence-based AI policy development.",
            "Framework": f"Regulatory framework from {organization} informing institutional AI strategy and risk management.",
            "Policy Document": f"Policy documentation from {organization} providing regulatory context for AI governance."
        }
        
        return significance_templates.get(doc_type, f"Regulatory documentation from {organization} supporting AI policy analysis and recommendations.")
    
    def add_validation_mappings(self, new_documents: List[Dict]) -> bool:
        """
        Add citation mappings to validation.py for new documents.
        
        Args:
            new_documents: List of new document metadata
            
        Returns:
            True if successfully added
        """
        if not new_documents:
            logger.info("No new documents to add validation mappings for")
            return True
        
        try:
            # Read current validation.py content
            with open(self.validation_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate new mapping code
            new_mappings = []
            for doc in new_documents:
                mapping = self._generate_validation_mapping(doc)
                if mapping:
                    new_mappings.append(mapping)
            
            if not new_mappings:
                return True
            
            # Find insertion point (after existing special handling)
            insert_pattern = r'(# Special handling for "European Union\. \(2024\)" format.*?refs\[short_citation\] = metadata)'
            match = re.search(insert_pattern, content, re.DOTALL)
            
            if match:
                insert_point = match.end()
                # Insert new mappings
                new_content = (
                    content[:insert_point] +
                    "\n" + "\n".join(new_mappings) +
                    content[insert_point:]
                )
                
                # Write back to file
                with open(self.validation_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"Added {len(new_mappings)} new validation mappings")
                return True
            else:
                logger.warning("Could not find insertion point for validation mappings")
                return False
                
        except Exception as e:
            logger.error(f"Error adding validation mappings: {e}")
            return False
    
    def _generate_validation_mapping(self, metadata: Dict) -> Optional[str]:
        """
        Generate validation mapping code for a document.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Python code string for validation mapping
        """
        organization = metadata['organization']
        year = metadata['year']
        short_citation = metadata['short_citation']
        
        # Generate condition based on organization and title patterns
        if organization == "European Union":
            condition = f'citation_text.startswith("European Union. ({year})")'
        elif organization == "United Kingdom":
            condition = f'citation_text.startswith("United Kingdom. ({year})")'
        elif organization == "United States":
            condition = f'citation_text.startswith("United States. ({year})")'
        else:
            # Generic pattern
            condition = f'citation_text.startswith("{organization}. ({year})")'
        
        mapping_code = f'''                            # Special handling for "{organization}. ({year})" format
                            elif {condition}:
                                # Create exact format used by recommendation system
                                short_citation = f"{short_citation}"
                                refs[short_citation] = metadata'''
        
        return mapping_code
    
    def process_new_documents(self) -> Dict[str, int]:
        """
        Complete process: scan, add to references, add mappings.
        
        Returns:
            Dictionary with processing results
        """
        logger.info("Starting automatic document processing...")
        
        # Scan for new documents
        new_documents = self.scan_for_new_documents()
        
        results = {
            'scanned': len(new_documents),
            'added_to_references': 0,
            'added_mappings': 0,
            'errors': 0
        }
        
        if not new_documents:
            logger.info("No new regulatory documents found")
            return results
        
        # Add to academic references
        if self.add_to_academic_references(new_documents):
            results['added_to_references'] = len(new_documents)
        else:
            results['errors'] += 1
        
        # Add validation mappings
        if self.add_validation_mappings(new_documents):
            results['added_mappings'] = len(new_documents)
        else:
            results['errors'] += 1
        
        logger.info(f"Document processing complete: {results}")
        return results


def run_auto_document_scan():
    """
    Convenience function to run automatic document scanning.
    
    Returns:
        Processing results dictionary
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    knowledge_base_path = base_path / "docs" / "knowledge_base"
    academic_refs_path = base_path / "docs" / "academic_references.md"
    validation_path = base_path / "src" / "utils" / "validation.py"
    
    # Create manager and process
    manager = AutoDocumentManager(
        str(knowledge_base_path),
        str(academic_refs_path),
        str(validation_path)
    )
    
    return manager.process_new_documents()


if __name__ == "__main__":
    # Run standalone
    results = run_auto_document_scan()
    print(f"Auto Document Processing Results: {results}")
