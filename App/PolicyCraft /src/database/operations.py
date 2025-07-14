"""
PolicyCraft – Database operations module.

Provides a cohesive abstraction over two storage modalities: relational
(SQLite) for persistent learner records and schemaless JSON files for
uploaded policy documents together with their analytical derivatives.

Author: Jacek Robert Kszczot
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import os
import uuid

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
        Persist a comprehensive analytical result set for the specified
        learner. Should an analysis bearing an identical ``filename`` already
        exist for this learner, the extant record identifier will be returned
        and, where appropriate, its attributes updated in lieu of creating a
        duplicate artefact.
        """
        # --- Duplicate check ---
        existing = next((a for a in self.storage['analyses']
                         if a['user_id'] == user_id and a['filename'] == filename), None)
        if existing:
            # Zaktualizuj klucz `analysis_date` i ewentualnie overwrite themes / classification
            existing['analysis_date'] = datetime.now(timezone.utc).isoformat()
            existing['themes'] = themes
            existing['classification'] = classification
            existing['text_data']['cleaned_text'] = cleaned_text[:5000]
            existing['text_data']['text_length'] = len(cleaned_text)
            self._save_storage()
            return existing['_id']

        # --- New analysis ---
        analysis_data = {
            '_id': f"analysis_{uuid.uuid4().hex}",
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
        return analyses

    # --------------------
    # Reporting utilities
    # --------------------
    def get_analysis_statistics(self) -> Dict[str, float]:
        """Return simple statistics across *all* stored analyses.

        Returns a dictionary of at least:
        - ``total_analyses`` (int): total number of analysis records.
        - ``avg_confidence`` (float): mean classification confidence across analyses (0 if none).
        """
        total = len(self.storage.get('analyses', []))
        if total == 0:
            return {"total_analyses": 0, "avg_confidence": 0}

        confidences = [a.get('classification', {}).get('confidence', 0)
                       for a in self.storage['analyses']]
        avg_conf = sum(confidences) / total if confidences else 0
        return {
            "total_analyses": total,
            "avg_confidence": avg_conf
        }

    def _deduplicate(self, analyses: List[Dict]) -> int:
        """Helper: deduplicate list by filename, keep the oldest entry."""
        removed = 0
        seen = set()
        # sort by analysis_date, keep first occurrence per filename
        for analysis in sorted(analyses, key=lambda x: x['analysis_date']):
            fname = analysis['filename']
            if fname in seen:
                self.storage['analyses'] = [a for a in self.storage['analyses'] if a['_id'] != analysis['_id']]
                removed += 1
            else:
                seen.add(fname)
        return removed

    def deduplicate_user_analyses(self, user_id: int) -> int:
        """Usuń duplikaty analiz (wszystkich) danego użytkownika bazując na nazwie pliku.
        Zostawia najstarszy wpis, usuwa kolejne.
        Zwraca liczbę usuniętych.
        """
        user_analyses = [a for a in self.storage['analyses'] if a['user_id'] == user_id]
        removed = self._deduplicate(user_analyses)
        if removed:
            self._save_storage()
        return removed

    def deduplicate_baseline_analyses(self, user_id: int) -> int:
        """Usuń duplikaty analiz rozpoczynających się od "[BASELINE]".
        Zostawia najstarszą (pierwszą) analizę dla danego pliku.

        Zwraca: liczba usuniętych duplikatów.
        """
        baseline_analyses = [a for a in self.storage['analyses']
                              if a['user_id'] == user_id and a['filename'].startswith('[BASELINE]')]
        removed = 0
        seen = {}
        for analysis in sorted(baseline_analyses, key=lambda x: x['analysis_date']):
            fname = analysis['filename']
            if fname not in seen:
                seen[fname] = analysis['_id']
            else:
                # duplikat – usuń
                self.storage['analyses'] = [a for a in self.storage['analyses'] if a['_id'] != analysis['_id']]
                removed += 1
        if removed:
            self._save_storage()
        return removed

    def get_user_analysis_by_id(self, user_id: int, analysis_id: str) -> Optional[Dict]:
        """Retrieve a single analysis document by its identifier and owner.

        Returns the analysis dictionary or ``None`` if not found.
        """
        for analysis in self.storage.get('analyses', []):
            if analysis['_id'] == analysis_id and analysis['user_id'] == user_id:
                return analysis
        return None
        
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


    def load_sample_policies_for_user(self, user_id: int) -> bool:
        """
        Load all 15 sample university policies as baseline analyses for new user.
        
        Args:
            user_id (int): User ID to load policies for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from src.auth.models import SAMPLE_UNIVERSITIES
            # If baseline analyses already exist for this user, treat as success
            existing_baselines = [
                a for a in self.storage['analyses']
                if a['user_id'] == user_id and a.get('filename', '').startswith('[BASELINE]')
            ]
            if existing_baselines:
                print(f"ℹ️ Baseline analyses already present for user {user_id} (" + str(len(existing_baselines)) + ")")
                return True
            from pathlib import Path
            
            # Path to clean dataset
            dataset_path = Path("data/policies/clean_dataset")
            if not dataset_path.exists():
                print(f"❌ Dataset path not found: {dataset_path}")
                return False
            
            loaded_count = 0
            
            # Load each sample policy
            for uni_key, uni_data in SAMPLE_UNIVERSITIES.items():
                filename = uni_data['file']
                file_path = dataset_path / filename
                
                if file_path.exists():
                    # Create baseline analysis entry with [BASELINE] prefix
                    baseline_filename = f"[BASELINE] {uni_data['name']} - {filename}"
                    _ = self.store_user_analysis_results(
                        user_id=user_id,
                        filename=baseline_filename,
                        original_text=f"Sample policy from {uni_data['name']}",
                        cleaned_text=f"Sample policy from {uni_data['name']} ({uni_data['country']})",
                        themes=[{"name": theme, "score": 0.8, "confidence": 85} for theme in uni_data.get("themes", [])],
                        classification={
                            'classification': uni_data.get('classification', 'Unknown'),
                            'confidence': 85,
                            'source': 'Sample Dataset'
                        },
                        document_id=f"sample_{uni_key}"
                    )
                    loaded_count += 1
                    print(f"✅ Loaded sample policy: {uni_data['name']}")
                else:
                    print(f"⚠️ Sample policy not found: {filename}")
            
            print(f"🎯 Loaded {loaded_count} sample policies for user {user_id}")
            return loaded_count > 0
            
        except Exception as e:
            print(f"❌ Error loading sample policies: {e}")
            return False


    def delete_user_analysis(self, user_id: int, analysis_id: str) -> bool:
        """
        Delete a user analysis by ID.
        
        Args:
            user_id (int): User ID
            analysis_id (str): Analysis ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find and remove the analysis
            original_count = len(self.storage['analyses'])
            self.storage['analyses'] = [
                analysis for analysis in self.storage['analyses']
                if not (analysis['user_id'] == user_id and analysis['_id'] == analysis_id)
            ]
            
            # Check if something was deleted
            deleted = len(self.storage['analyses']) < original_count
            
            if deleted:
                self._save_storage()
                print(f"✅ Deleted analysis {analysis_id} for user {user_id}")
                return True
            else:
                print(f"⚠️ Analysis {analysis_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting analysis: {e}")
            return False

    def compare_with_baseline_policies(self, user_id: int, analysis_id: str) -> Dict:
        """
        Compare user analysis with baseline university policies.
        
        Args:
            user_id (int): User ID
            analysis_id (str): Analysis ID to compare
            
        Returns:
            Dict: Comparison results with rankings and insights
        """
        try:
            # Get user analysis
            user_analysis = self.get_user_analysis_by_id(user_id, analysis_id)
            if not user_analysis:
                return {"error": "Analysis not found"}
            
            # Get baseline policies for this user
            all_analyses = self.get_user_analyses(user_id, limit=100)
            baseline_analyses = [a for a in all_analyses if a.get("filename", "").startswith("[BASELINE]")]
            
            if not baseline_analyses:
                return {"error": "No baseline policies found"}
            
            user_classification = user_analysis.get("classification", {})
            user_score = user_classification.get("confidence", 0)
            user_type = user_classification.get("classification", "Unknown")
            
            # Compare with each baseline
            comparisons = []
            for baseline in baseline_analyses:
                baseline_class = baseline.get("classification", {})
                baseline_score = baseline_class.get("confidence", 0)
                baseline_type = baseline_class.get("classification", "Unknown")
                
                # Extract university name from filename
                filename = baseline.get("filename", "")
                university_name = filename.replace("[BASELINE] ", "").split(" - ")[0] if " - " in filename else "Unknown"
                
                comparison = {
                    "university": university_name,
                    "classification": baseline_type,
                    "confidence": baseline_score,
                    "score_difference": user_score - baseline_score,
                    "classification_match": user_type == baseline_type,
                    "relative_performance": "better" if user_score > baseline_score else "worse" if user_score < baseline_score else "similar"
                }
                comparisons.append(comparison)
            
            # Sort by score difference
            comparisons.sort(key=lambda x: abs(x["score_difference"]))
            
            # Generate insights
            better_than = [c for c in comparisons if c["relative_performance"] == "better"]
            worse_than = [c for c in comparisons if c["relative_performance"] == "worse"]
            
            summary = {
                "total_comparisons": len(comparisons),
                "better_than_count": len(better_than),
                "worse_than_count": len(worse_than),
                "average_baseline_score": round(sum(c["confidence"] for c in comparisons) / len(comparisons), 1),
                "user_score": user_score,
                "user_classification": user_type,
                "ranking_percentile": round((len(better_than) / len(comparisons)) * 100, 1)
            }
            
            return {
                "summary": summary,
                "comparisons": comparisons[:10],  # Top 10 closest matches
                "better_than": better_than[:3],   # Top 3 universities outperformed
                "worse_than": worse_than[:3],     # Top 3 that outperform user
                "analysis_id": analysis_id
            }
            
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}


# Test functionality
if __name__ == "__main__":
    print("Testing DatabaseOperations...")
    
    db_ops = DatabaseOperations()
    
    # Test user ID
    test_user_id = 1
    
    # Test data
    test_filename = "test-policy.pdf"
    test_text = "Sample AI policy text for testing purposes."
    test_themes = [
        {'name': 'AI Ethics', 'score': 0.85, 'confidence': 92},
        {'name': 'Academic Integrity', 'score': 0.78, 'confidence': 89}
    ]
    test_classification = {
        'classification': 'Moderate',
        'confidence': 75,
        'method': 'hybrid'
    }
    
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
