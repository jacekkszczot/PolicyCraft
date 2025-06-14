"""
Database operations for PolicyCraft.
Handles both SQLite (users) and MongoDB (documents/analyses) operations.

Author: Jacek Robert Kszczot
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3

# MongoDB imports
try:
    import pymongo
    from pymongo import MongoClient
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Warning: MongoDB libraries not available. Using JSON file storage as fallback.")

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Unified database operations handling both SQLite and MongoDB.
    SQLite for users, MongoDB for documents and analysis results.
    """
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/", db_name: str = "policycraft"):
        """
        Initialize database connections.
        
        Args:
            mongodb_uri (str): MongoDB connection URI
            db_name (str): MongoDB database name
        """
        self.db_name = db_name
        self.mongo_client = None
        self.mongo_db = None
        
        # Fallback storage (JSON files)
        self.fallback_storage = {
            'documents': [],
            'analyses': [],
            'recommendations': []
        }
        self.fallback_file = 'data/fallback_storage.json'
        
        # Initialize MongoDB if available
        if MONGODB_AVAILABLE:
            self._init_mongodb(mongodb_uri)
        else:
            print("Using fallback JSON storage instead of MongoDB")
            self._load_fallback_storage()
        
        print("DatabaseOperations initialized successfully")

    def _init_mongodb(self, mongodb_uri: str):
        """Initialize MongoDB connection."""
        try:
            self.mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.mongo_client.server_info()
            self.mongo_db = self.mongo_client[self.db_name]
            
            # Create indexes for better performance
            self._create_indexes()
            
            print(f"Connected to MongoDB: {self.db_name}")
            
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Falling back to JSON file storage")
            self.mongo_client = None
            self.mongo_db = None
            self._load_fallback_storage()

    def _create_indexes(self):
        """Create database indexes for better performance."""
        if not self.mongo_db:
            return
            
        try:
            # Documents collection indexes
            self.mongo_db.documents.create_index([("user_id", 1), ("upload_date", -1)])
            self.mongo_db.documents.create_index("filename")
            
            # Analyses collection indexes  
            self.mongo_db.analyses.create_index([("user_id", 1), ("analysis_date", -1)])
            self.mongo_db.analyses.create_index("document_id")
            
            # Recommendations collection indexes
            self.mongo_db.recommendations.create_index([("user_id", 1), ("created_date", -1)])
            
            print("Database indexes created successfully")
            
        except Exception as e:
            print(f"Error creating indexes: {e}")

    def _load_fallback_storage(self):
        """Load data from JSON fallback storage."""
        try:
            import os
            os.makedirs('data', exist_ok=True)
            
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, 'r') as f:
                    self.fallback_storage = json.load(f)
            else:
                self._save_fallback_storage()
                
        except Exception as e:
            print(f"Error loading fallback storage: {e}")

    def _save_fallback_storage(self):
        """Save data to JSON fallback storage."""
        try:
            with open(self.fallback_file, 'w') as f:
                json.dump(self.fallback_storage, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving fallback storage: {e}")

    # Document operations
    def store_document(self, user_id: int, filename: str, file_path: str, 
                      extracted_text: str, metadata: Dict = None) -> str:
        """
        Store document information.
        
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
            'user_id': user_id,
            'filename': filename,
            'file_path': file_path,
            'extracted_text': extracted_text,
            'text_length': len(extracted_text),
            'upload_date': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        if self.mongo_db:
            try:
                result = self.mongo_db.documents.insert_one(document_data)
                document_id = str(result.inserted_id)
                print(f"Document stored in MongoDB: {document_id}")
                return document_id
            except Exception as e:
                print(f"MongoDB storage failed: {e}")
        
        # Fallback storage
        document_data['_id'] = f"doc_{len(self.fallback_storage['documents']) + 1}"
        document_data['upload_date'] = document_data['upload_date'].isoformat()
        self.fallback_storage['documents'].append(document_data)
        self._save_fallback_storage()
        
        print(f"Document stored in fallback: {document_data['_id']}")
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
            'user_id': user_id,
            'document_id': document_id,
            'filename': filename,
            'analysis_date': datetime.utcnow(),
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
        
        if self.mongo_db:
            try:
                result = self.mongo_db.analyses.insert_one(analysis_data)
                analysis_id = str(result.inserted_id)
                print(f"Analysis stored in MongoDB: {analysis_id}")
                return analysis_id
            except Exception as e:
                print(f"MongoDB analysis storage failed: {e}")
        
        # Fallback storage
        analysis_data['_id'] = f"analysis_{len(self.fallback_storage['analyses']) + 1}"
        analysis_data['analysis_date'] = analysis_data['analysis_date'].isoformat()
        self.fallback_storage['analyses'].append(analysis_data)
        self._save_fallback_storage()
        
        print(f"Analysis stored in fallback: {analysis_data['_id']}")
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
        if self.mongo_db:
            try:
                cursor = self.mongo_db.analyses.find(
                    {'user_id': user_id}
                ).sort('analysis_date', -1).limit(limit)
                
                analyses = []
                for doc in cursor:
                    doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                    analyses.append(doc)
                
                print(f"Retrieved {len(analyses)} analyses from MongoDB for user {user_id}")
                return analyses
                
            except Exception as e:
                print(f"MongoDB retrieval failed: {e}")
        
        # Fallback storage
        analyses = [
            analysis for analysis in self.fallback_storage['analyses']
            if analysis['user_id'] == user_id
        ]
        analyses.sort(key=lambda x: x['analysis_date'], reverse=True)
        
        print(f"Retrieved {len(analyses)} analyses from fallback for user {user_id}")
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
        if self.mongo_db:
            try:
                if ObjectId.is_valid(analysis_id):
                    query = {'_id': ObjectId(analysis_id), 'user_id': user_id}
                else:
                    query = {'_id': analysis_id, 'user_id': user_id}
                
                analysis = self.mongo_db.analyses.find_one(query)
                if analysis:
                    analysis['_id'] = str(analysis['_id'])
                    return analysis
                    
            except Exception as e:
                print(f"MongoDB retrieval failed: {e}")
        
        # Fallback storage
        for analysis in self.fallback_storage['analyses']:
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
        if self.mongo_db:
            try:
                # Build query
                match_query = {'user_id': user_id} if user_id else {}
                
                # Aggregation pipeline
                pipeline = [
                    {'$match': match_query},
                    {'$group': {
                        '_id': None,
                        'total_analyses': {'$sum': 1},
                        'avg_themes': {'$avg': {'$size': '$themes'}},
                        'classifications': {'$push': '$classification.classification'},
                        'confidence_scores': {'$push': '$classification.confidence'}
                    }}
                ]
                
                result = list(self.mongo_db.analyses.aggregate(pipeline))
                if result:
                    stats = result[0]
                    
                    # Count classifications
                    classification_counts = {}
                    for cls in stats['classifications']:
                        classification_counts[cls] = classification_counts.get(cls, 0) + 1
                    
                    return {
                        'total_analyses': stats['total_analyses'],
                        'avg_themes_per_analysis': round(stats['avg_themes'], 1),
                        'classification_distribution': classification_counts,
                        'avg_confidence': round(sum(stats['confidence_scores']) / len(stats['confidence_scores']), 1)
                    }
                    
            except Exception as e:
                print(f"MongoDB statistics failed: {e}")
        
        # Fallback statistics
        analyses = self.fallback_storage['analyses']
        if user_id:
            analyses = [a for a in analyses if a['user_id'] == user_id]
        
        if not analyses:
            return {'total_analyses': 0}
        
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
            'user_id': user_id,
            'analysis_id': analysis_id,
            'recommendations': recommendations,
            'created_date': datetime.utcnow(),
            'total_recommendations': len(recommendations)
        }
        
        if self.mongo_db:
            try:
                result = self.mongo_db.recommendations.insert_one(rec_data)
                rec_id = str(result.inserted_id)
                print(f"Recommendations stored in MongoDB: {rec_id}")
                return rec_id
            except Exception as e:
                print(f"MongoDB recommendation storage failed: {e}")
        
        # Fallback storage
        rec_data['_id'] = f"rec_{len(self.fallback_storage['recommendations']) + 1}"
        rec_data['created_date'] = rec_data['created_date'].isoformat()
        self.fallback_storage['recommendations'].append(rec_data)
        self._save_fallback_storage()
        
        print(f"Recommendations stored in fallback: {rec_data['_id']}")
        return rec_data['_id']

    def cleanup_old_data(self, days_old: int = 30):
        """
        Clean up old analysis data to save space.
        
        Args:
            days_old (int): Delete data older than this many days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        if self.mongo_db:
            try:
                # Delete old analyses
                result = self.mongo_db.analyses.delete_many({
                    'analysis_date': {'$lt': cutoff_date}
                })
                print(f"Deleted {result.deleted_count} old analyses from MongoDB")
                
                # Delete old recommendations
                result = self.mongo_db.recommendations.delete_many({
                    'created_date': {'$lt': cutoff_date}
                })
                print(f"Deleted {result.deleted_count} old recommendations from MongoDB")
                
            except Exception as e:
                print(f"MongoDB cleanup failed: {e}")
        
        # Fallback cleanup
        self.fallback_storage['analyses'] = [
            a for a in self.fallback_storage['analyses']
            if datetime.fromisoformat(a['analysis_date']) > cutoff_date
        ]
        self.fallback_storage['recommendations'] = [
            r for r in self.fallback_storage['recommendations']
            if datetime.fromisoformat(r['created_date']) > cutoff_date
        ]
        self._save_fallback_storage()

    def close_connections(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
            print("MongoDB connection closed")


# Test the database operations
if __name__ == "__main__":
    print("Starting database operations test...")
    
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
    
    print("\n=== Database Operations Test ===")
    
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
    
    # Test retrieving specific analysis
    retrieved_analysis = db_ops.get_user_analysis_by_id(test_user_id, analysis_id)
    if retrieved_analysis:
        print(f"Retrieved specific analysis: {retrieved_analysis['filename']}")
    
    print("\n✅ Database operations working correctly!")
    
    # Clean up
    db_ops.close_connections()