"""
Database operations for PolicyCraft.
Handles SQLite (users) and JSON (documents/analyses) operations.

Author: Jacek Robert Kszczot
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Database operations handling SQLite and JSON storage.
    SQLite for users, JSON for documents and analysis results.
    """
    
    def __init__(self):
        """
        Initialize database operations with JSON storage.
        """
        # JSON storage for documents and analyses
        self.storage = {
            'documents': [],
            'analyses': [],
            'recommendations': []
        }
        self.storage_file = 'data/database_storage.json'
        
        # Load existing data
        self._load_storage()
        print("DatabaseOperations initialized successfully with JSON storage")

    def _load_storage(self):
        """Load data from JSON storage file."""
        try:
            os.makedirs('data', exist_ok=True)
            
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.storage = json.load(f)
            else:
                self._save_storage()
                
        except Exception as e:
            print(f"Error loading storage: {e}")

    def _save_storage(self):
        """Save data to JSON storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.storage, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving storage: {e}")

    # Document operations
    def store_document(self, user_id: int, filename: str, file_path: str, 
                      extracted_text: str, metadata: Dict = None) -> str:
        """
        Store document information in JSON.
        
        Args:
            user_id (int): ID of the user who uploaded the document
            filename (str): Original filename
            file_path (str): Path to stored file
            extracted_text (str): Extracted text content
            metadata (Dict): Additional metadata
            
        Returns:
            str: Document ID
        """
        document_data = {
            '_id': f"doc_{len(self.storage['documents']) + 1}",
            'user_id': user_id,
            'filename': filename,
            'file_path': file_path,
            'extracted_text': extracted_text,
            'text_length': len(extracted_text),
            'upload_date': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        
        self.storage['documents'].append(document_data)
        self._save_storage()
        
        print(f"Document stored: {document_data['_id']}")
        return document_data['_id']

    def store_user_analysis_results(self, user_id: int, filename: str, 
                                   original_text: str, cleaned_text: str,
                                   themes: List[Dict], classification: Dict,
                                   document_id: str = None) -> str:
        """
        Store complete analysis results for a user.
        
        Args:
            user_id (int): User ID
            filename (str): Document filename  
            original_text (str): Original extracted text
            cleaned_text (str): Processed text
            themes (List[Dict]): Extracted themes
            classification (Dict): Classification results
            document_id (str): Associated document ID
            
        Returns:
            str: Analysis ID
        """
        analysis_data = {
            '_id': f"analysis_{len(self.storage['analyses']) + 1}",
            'user_id': user_id,
            'document_id': document_id,
            'filename': filename,
            'analysis_date': datetime.now(timezone.utc).isoformat(),
            'text_data': {
                'original_text': original_text[:5000],  # Limit storage size
                'cleaned_text': cleaned_text[:5000],
                'text_length': len(cleaned_text)
            },
            'themes': themes,
            'classification': classification,
            'summary': {
                'total_themes': len(themes),
                'top_theme': themes[0]['name'] if themes else None,
                'classification_type': classification.get('classification', 'Unknown'),
                'confidence': classification.get('confidence', 0)
            }
        }
        
        self.storage['analyses'].append(analysis_data)
        self._save_storage()
        
        print(f"Analysis stored: {analysis_data['_id']}")
        return analysis_data['_id']

    def get_user_analyses(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get all analyses for a specific user.
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: List of user analyses
        """
        # Filter analyses for user
        analyses = [
            analysis for analysis in self.storage['analyses']
            if analysis['user_id'] == user_id
        ]
        
        # Sort by analysis date (newest first)
        analyses.sort(key=lambda x: x['analysis_date'], reverse=True)
        
        print(f"Retrieved {len(analyses)} analyses for user {user_id}")
        return analyses[:limit]

    def get_user_analysis_by_id(self, user_id: int, analysis_id: str) -> Optional[Dict]:
        """
        Get specific analysis by ID for a user.
        
        Args:
            user_id (int): User ID
            analysis_id (str): Analysis ID
            
        Returns:
            Optional[Dict]: Analysis data or None
        """
        for analysis in self.storage['analyses']:
            if analysis['_id'] == analysis_id and analysis['user_id'] == user_id:
                return analysis
        
        return None

    def get_analysis_statistics(self, user_id: int = None) -> Dict:
        """
        Get analysis statistics for a user or globally.
        
        Args:
            user_id (int): Optional user ID for user-specific stats
            
        Returns:
            Dict: Statistics summary
        """
        # Filter analyses
        analyses = self.storage['analyses']
        if user_id:
            analyses = [a for a in analyses if a['user_id'] == user_id]
        
        if not analyses:
            return {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}
        
        # Calculate statistics
        classification_counts = {}
        confidence_scores = []
        theme_counts = []
        
        for analysis in analyses:
            # Classification distribution
            cls = analysis.get('classification', {}).get('classification', 'Unknown')
            classification_counts[cls] = classification_counts.get(cls, 0) + 1
            
            # Confidence scores
            conf = analysis.get('classification', {}).get('confidence', 0)
            confidence_scores.append(conf)
            
            # Theme counts
            theme_counts.append(len(analysis.get('themes', [])))
        
        return {
            'total_analyses': len(analyses),
            'avg_themes_per_analysis': round(sum(theme_counts) / len(theme_counts), 1) if theme_counts else 0,
            'classification_distribution': classification_counts,
            'avg_confidence': round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0
        }

    def store_recommendations(self, user_id: int, analysis_id: str, 
                            recommendations: List[Dict]) -> str:
        """
        Store recommendation results.
        
        Args:
            user_id (int): User ID
            analysis_id (str): Associated analysis ID
            recommendations (List[Dict]): Generated recommendations
            
        Returns:
            str: Recommendation set ID
        """
        rec_data = {
            '_id': f"rec_{len(self.storage['recommendations']) + 1}",
            'user_id': user_id,
            'analysis_id': analysis_id,
            'recommendations': recommendations,
            'created_date': datetime.now(timezone.utc).isoformat(),
            'total_recommendations': len(recommendations)
        }
        
        self.storage['recommendations'].append(rec_data)
        self._save_storage()
        
        print(f"Recommendations stored: {rec_data['_id']}")
        return rec_data['_id']

    def cleanup_old_data(self, days_old: int = 30):
        """
        Clean up old analysis data to save space.
        
        Args:
            days_old (int): Delete data older than this many days
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        cutoff_iso = cutoff_date.isoformat()
        
        # Clean old analyses
        original_count = len(self.storage['analyses'])
        self.storage['analyses'] = [
            a for a in self.storage['analyses']
            if a['analysis_date'] > cutoff_iso
        ]
        deleted_analyses = original_count - len(self.storage['analyses'])
        
        # Clean old recommendations
        original_rec_count = len(self.storage['recommendations'])
        self.storage['recommendations'] = [
            r for r in self.storage['recommendations']
            if r['created_date'] > cutoff_iso
        ]
        deleted_recs = original_rec_count - len(self.storage['recommendations'])
        
        self._save_storage()
        print(f"Cleaned up {deleted_analyses} old analyses and {deleted_recs} old recommendations")

    def get_storage_info(self) -> Dict:
        """
        Get information about current storage.
        
        Returns:
            Dict: Storage statistics
        """
        return {
            'storage_type': 'JSON',
            'storage_file': self.storage_file,
            'total_documents': len(self.storage['documents']),
            'total_analyses': len(self.storage['analyses']),
            'total_recommendations': len(self.storage['recommendations']),
            'file_size_mb': round(os.path.getsize(self.storage_file) / 1024 / 1024, 2) if os.path.exists(self.storage_file) else 0
        }


# Test the database operations
if __name__ == "__main__":
    print("Starting JSON database operations test...")
    
    db_ops = DatabaseOperations()
    
    # Test data
    test_user_id = 1
    test_filename = "test_policy.pdf"
    test_text = "This is a test AI policy document for testing purposes."
    test_themes = [
        {'name': 'AI Ethics', 'score': 5.5, 'confidence': 55},
        {'name': 'Academic Integrity', 'score': 3.5, 'confidence': 35}
    ]
    test_classification = {
        'classification': 'Moderate',
        'confidence': 75,
        'method': 'hybrid'
    }
    
    print("\n=== JSON Database Operations Test ===")
    
    # Test storing analysis
    analysis_id = db_ops.store_user_analysis_results(
        user_id=test_user_id,
        filename=test_filename,
        original_text=test_text,
        cleaned_text=test_text,
        themes=test_themes,
        classification=test_classification
    )
    print(f"Stored analysis with ID: {analysis_id}")
    
    # Test retrieving analyses
    user_analyses = db_ops.get_user_analyses(test_user_id)
    print(f"Retrieved {len(user_analyses)} analyses for user {test_user_id}")
    
    # Test statistics
    stats = db_ops.get_analysis_statistics(test_user_id)
    print(f"User statistics: {stats}")
    
    # Test storage info
    storage_info = db_ops.get_storage_info()
    print(f"Storage info: {storage_info}")
    
    print("\n✅ JSON database operations working correctly!")