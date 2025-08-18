"""
MongoDB-backed data operations for PolicyCraft.

This module provides the same public API (method names and signatures)
as the former JSON-based `DatabaseOperations` so that the rest of the
application can switch storage by changing the import only.

For simplicity we implement only the methods actually referenced by the
Flask app. Additional helpers can be added later.

MongoDB collections:
    analyses          – user analyses and baseline documents
    recommendations   – recommendations generated for an analysis

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University

The module expects a running MongoDB instance (>=4.0) and the `pymongo`
package. Install locally via:
    pip install pymongo

Environment variables (or kwargs) may override default connection URI
and database name.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

# MongoDB query constants
MATCH_QUERY = "$match"
SORT_QUERY = "$sort"
GROUP_QUERY = "$group"
SET_OPERATOR = "$set"
PUSH_OPERATOR = "$push"
SUM_OPERATOR = "$sum"
AVG_OPERATOR = "$avg"
SIZE_OPERATOR = "$size"
NOT_OPERATOR = "$not"

# Field name constants
USER_ID_FIELD = "user_id"
ANALYSIS_ID_FIELD = "analysis_id"
FILENAME_FIELD = "filename"
THEMES_FIELD = "themes"
CLASSIFICATION_FIELD = "classification"
RECOMMENDATIONS_FIELD = "recommendations"
CREATED_AT_FIELD = "created_at"
REGEX_OPERATOR = "$regex"
OPTIONS_OPERATOR = "$options"
IN_OPERATOR = "$in"
GT_OPERATOR = "$gt"

# Additional field name constants (non-duplicates)
ID_FIELD = "_id"
ANALYSIS_DATE_FIELD = "analysis_date"
COUNT_FIELD = "count"
TOTAL_FIELD = "total"
DOCS_FIELD = "docs"
IDS_FIELD = "ids"
CONFIDENCE_FIELD = "confidence"
AVG_CONFIDENCE_FIELD = "avg_confidence"
AVG_THEMES_FIELD = "avg_themes_per_analysis"

# Regular expressions
# Matches filenames starting with "[BASELINE]"
BASELINE_REGEX = r"^\[BASELINE\]"

# Helper types for better code readability
Analysis = Dict
Recommendation = Dict


class MongoOperations:
    """
    MongoDB-backed persistence layer for PolicyCraft application.
    
    Provides data access methods for storing and retrieving policy analyses,
    recommendations, and user data with MongoDB as the backend storage.
    """

    def __init__(self, uri: str | None = None, db_name: str | None = None):
        """
        Initialise MongoDB connection and set up collections.
        
        Args:
            uri: MongoDB connection URI (defaults to localhost)
            db_name: Database name (defaults to 'policycraft')
        """
        uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = db_name or os.getenv("MONGO_DB", "policycraft")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

        self.analyses: Collection = self.db["analyses"]
        self.recommendations: Collection = self.db["recommendations"]

        # Ensure indexes for performance optimisation
        # Non-unique index to accelerate lookup; duplicates handled at application level
        try:
            self.analyses.create_index([("user_id", ASCENDING), ("filename", ASCENDING)])
        except Exception as e:
            logger.warning("[MongoOperations] Index creation warning: %s", e)

        self.recommendations.create_index([("analysis_id", ASCENDING), ("user_id", ASCENDING)])

    # Analysis CRUD operations

    def store_user_analysis_results(
        self,
        user_id: int,
        filename: str,
        original_text: str,
        cleaned_text: str,
        themes: List[Dict],
        classification: Dict,
        document_id: str | None = None,
        username: str | None = None,
    ) -> str:
        """
        Insert or update a user's analysis result in the database.

        Ensures uniqueness on (user_id, filename). Duplicate baseline
        entries therefore do not collide with user uploads because their
        user_id differs (baseline is typically user_id=-1 or similar).
        
        Args:
            user_id: User identifier
            filename: Name of the analysed file
            original_text: Raw extracted text from document
            cleaned_text: Processed text after cleaning
            themes: List of extracted themes
            classification: Policy classification results
            document_id: Optional document identifier
            username: Optional username for tracking
            
        Returns:
            str: MongoDB document ID of the stored analysis
        """
        # Check if this user already analysed this file to avoid duplicates
        existing = self.analyses.find_one({"user_id": user_id, "filename": filename})
        if existing:
            # Update existing document with latest results and refresh date
            self.analyses.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "analysis_date": datetime.now(timezone.utc),
                    "themes": themes,
                    "classification": classification,
                    "text_data.cleaned_text": cleaned_text[:5000],
                    "text_data.text_length": len(cleaned_text),
                    "username": username or existing.get("username"),
                }}
            )
            return str(existing["_id"])

        # Build analysis document for new entry
        analysis_doc: Analysis = {
            "user_id": user_id,
            "document_id": document_id,
            "filename": filename,
            "analysis_date": datetime.now(timezone.utc),
            "username": username,
            "text_data": {
                "original_text": original_text[:5000],
                "cleaned_text": cleaned_text[:5000],
                "text_length": len(cleaned_text),
            },
            "themes": themes,
            "classification": classification,
            "summary": {
                "total_themes": len(themes),
                "top_theme": themes[0]["name"] if themes else None,
                "classification_type": classification.get("classification", "Unknown"),
                "confidence": classification.get("confidence", 0),
            },
        }

        result = self.analyses.insert_one(analysis_doc)
        return str(result.inserted_id)

    def get_analysis_by_filename(self, user_id: int, filename: str) -> Optional[Analysis]:
        """
        Return single analysis for user and filename or None if not found.
        
        Args:
            user_id: User identifier
            filename: Name of the file to search for
            
        Returns:
            Analysis document or None if not found
        """
        return self.analyses.find_one({"user_id": user_id, "filename": filename})

    def get_user_analyses(self, user_id: int) -> List[Analysis]:
        """
        Get all analyses for a specific user ordered by analysis date (newest first).
        
        Args:
            user_id: User identifier
            
        Returns:
            List of analysis documents
        """
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"[DEBUG] MongoOperations: Fetching analyses for user_id: {user_id}")
            logger.info(f"[DEBUG] MongoOperations: Collection name: {self.analyses.name}")
            logger.info(f"[DEBUG] MongoOperations: Database name: {self.db.name}")
            
            # Log connection status
            logger.info(f"[DEBUG] MongoOperations: Connection status: {self.client is not None}")
            
            # List all collections in the database
            try:
                collections = self.db.list_collection_names()
                logger.info(f"[DEBUG] MongoOperations: Available collections: {collections}")
            except Exception as e:
                logger.error(f"[DEBUG] MongoOperations: Error listing collections: {str(e)}")
            
            # Get count of analyses for this user
            count = self.analyses.count_documents({"user_id": user_id})
            logger.info(f"[DEBUG] MongoOperations: Found {count} analyses for user {user_id}")
            
            # Get the analyses
            cursor = self.analyses.find({"user_id": user_id}).sort("analysis_date", DESCENDING)
            analyses = list(cursor)
            
            logger.info(f"[DEBUG] MongoOperations: Retrieved {len(analyses)} analyses")
            if analyses:
                logger.info(f"[DEBUG] MongoOperations: First analysis ID: {analyses[0].get('_id')}")
                logger.info(f"[DEBUG] MongoOperations: First analysis filename: {analyses[0].get('filename')}")
            
            return analyses
            
        except Exception as e:
            logger.error(f"[DEBUG] MongoOperations: Error in get_user_analyses: {str(e)}")
            logger.error(f"[DEBUG] MongoOperations: Error type: {type(e).__name__}", exc_info=True)
            raise

    def remove_duplicate_analyses(self, user_id: int) -> int:
        """
        Delete duplicate analyses for a user keeping the most recent per filename.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of documents removed
        """
        pipeline = [
            {MATCH_QUERY: {USER_ID_FIELD: user_id}},
            {SORT_QUERY: {ANALYSIS_DATE_FIELD: DESCENDING}},  # newest first
            {GROUP_QUERY: {
                ID_FIELD: f"${FILENAME_FIELD}",
                DOCS_FIELD: {PUSH_OPERATOR: f"${ID_FIELD}"},
                COUNT_FIELD: {SUM_OPERATOR: 1}
            }},
            {MATCH_QUERY: {COUNT_FIELD: {GT_OPERATOR: 1}}}
        ]
        
        duplicates = list(self.analyses.aggregate(pipeline))
        
        # For each duplicate, keep the first (newest) and delete the rest
        deleted_count = 0
        for dup in duplicates:
            # Skip the first document (keep it) and delete the rest
            to_delete = dup[DOCS_FIELD][1:]
            if to_delete:
                result = self.analyses.delete_many({ID_FIELD: {IN_OPERATOR: to_delete}})
                deleted_count += result.deleted_count
                
        return deleted_count
            
    def _to_object_id(self, id_str: str):
        """
        Helper function to convert 24-character hex string to ObjectId.
        
        Args:
            id_str: String representation of MongoDB ObjectId
            
        Returns:
            ObjectId or original string if conversion fails
        """
        try:
            from bson import ObjectId  # lazy import
            return ObjectId(id_str) if len(id_str) == 24 else id_str
        except Exception:
            return id_str

    def get_user_analysis_by_id(self, user_id: int, analysis_id: str) -> Optional[Analysis]:
        """
        Get specific analysis by ID for a user.
        
        Args:
            user_id: User identifier
            analysis_id: Analysis document ID
            
        Returns:
            Analysis document or None if not found
        """
        oid = self._to_object_id(analysis_id)
        return self.analyses.find_one({"_id": oid, "user_id": user_id})

    def delete_user_analysis(self, user_id: int, analysis_id: str) -> bool:
        """
        Delete a user's analysis with protection for baseline policies.
        
        Args:
            user_id: User identifier
            analysis_id: Analysis document ID to delete
            
        Returns:
            bool: True if deletion was successful
        """
        oid = self._to_object_id(analysis_id)
        result = self.analyses.delete_one({
            "_id": oid,
            "user_id": user_id,
            "filename": {"$not": {"$regex": BASELINE_REGEX}}
        })
        return result.deleted_count == 1

    def get_analysis_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        Generic fetch without user filter (used by API endpoints).
        
        Args:
            analysis_id: Analysis document ID
            
        Returns:
            Analysis document or None if not found
        """
        oid = self._to_object_id(analysis_id)
        return self.analyses.find_one({"_id": oid})

    # Statistics and aggregation methods

    def get_analysis_statistics(self, user_id: int | None = None) -> Dict:
        """
        Get statistical summary of analyses for user or globally.
        
        Args:
            user_id: User identifier (None for global statistics)
            
        Returns:
            Dict containing analysis statistics
        """
        match = {"user_id": user_id} if user_id is not None else {}
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "avg_confidence": {"$avg": "$classification.confidence"},
                "avg_themes_per_analysis": {"$avg": {"$size": "$themes"}},
            }},
        ]
        agg = list(self.analyses.aggregate(pipeline))
        if not agg:
            return {"total": 0, "avg_confidence": 0, "avg_themes_per_analysis": 0}
        doc = agg[0]
        return {
            "total": doc["total"],
            "avg_confidence": round(doc.get("avg_confidence", 0), 1),
            "avg_themes_per_analysis": round(doc.get("avg_themes_per_analysis", 0), 1),
        }

    # Recommendations management

    def get_recommendations_by_analysis(self, user_id: int, analysis_id: str):
        """
        Return stored recommendations list for an analysis or None.
        
        Args:
            user_id: User identifier
            analysis_id: Analysis document ID
            
        Returns:
            List of recommendations or None if not found
        """
        doc = self.recommendations.find_one({"user_id": user_id, "analysis_id": analysis_id})
        if doc:
            return doc.get("recommendations", [])
        return None

    def store_recommendations(self, user_id: int, analysis_id: str, recs: List[Recommendation]) -> str:
        """
        Store recommendations for an analysis in the database.
        
        Args:
            user_id: User identifier
            analysis_id: Analysis document ID
            recs: List of recommendation objects
            
        Returns:
            str: MongoDB document ID of stored recommendations
        """
        payload = {
            USER_ID_FIELD: user_id,
            ANALYSIS_ID_FIELD: analysis_id,
            "recommendations": recs,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.recommendations.insert_one(payload)
        return str(result.inserted_id)

    # User data cleanup helpers

    def clear_all_recommendations(self) -> int:
        """
        Remove all recommendations from the database.
        
        Returns:
            int: Number of recommendations deleted
        """
        result = self.recommendations.delete_many({})
        return result.deleted_count

    def purge_user_data(self, user_id: int):
        """
        Delete all analyses, recommendations, and associated files for a user.
        
        CRITICAL SECURITY FIX: Now also deletes physical files from disk
        to ensure complete data removal and GDPR compliance.
        
        Args:
            user_id: User identifier whose data should be purged
        """
        import os
        from flask import current_app
        
        # First, get all analyses to find associated files
        user_analyses = list(self.analyses.find({"user_id": user_id}))
        deleted_files = []
        
        # Delete physical files from disk
        for analysis in user_analyses:
            filename = analysis.get('filename', '')
            if filename and not filename.startswith('[baseline]'):  # Don't delete baseline files
                # Try multiple possible upload directories
                possible_paths = [
                    os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename),
                    os.path.join('uploads', filename),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads', filename)
                ]
                
                for file_path in possible_paths:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files.append(filename)
                            print(f"Deleted file: {file_path}")
                            break  # File found and deleted, no need to check other paths
                        except Exception as e:
                            print(f"Warning: Could not delete file {file_path}: {e}")
        
        # Delete from MongoDB
        res1 = self.analyses.delete_many({"user_id": user_id})
        res2 = self.recommendations.delete_many({"user_id": user_id})
        
        print(f"SECURITY FIX: Purged {res1.deleted_count} analyses, {res2.deleted_count} recommendations, and {len(deleted_files)} files for user {user_id}")
        if deleted_files:
            print(f"Deleted files: {', '.join(deleted_files)}")
        
        return {
            'analyses_deleted': res1.deleted_count,
            'recommendations_deleted': res2.deleted_count,
            'files_deleted': len(deleted_files),
            'deleted_files': deleted_files
        }

    # Baseline policy management helpers

    def deduplicate_baseline_analyses(self, user_id: int):
        """
        Remove duplicate baseline analyses for a given user, keeping the newest document.

        Duplicate means same user_id and filename. Keep the most recent (analysis_date max).
        
        Args:
            user_id: User identifier to deduplicate baseline analyses for
        """
        pipeline = [
            {"$match": {"user_id": user_id, "filename": {"$regex": BASELINE_REGEX, "$options": "i"}}},
            {"$sort": {"analysis_date": -1}},
            {"$group": {
                "_id": "$filename",
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = list(self.analyses.aggregate(pipeline))
        removed = 0
        for doc in duplicates:
            ids_to_remove = doc["ids"][1:]  # keep newest (first)
            result = self.analyses.delete_many({"_id": {"$in": ids_to_remove}})
            removed += result.deleted_count
        if removed:
            print(f"Removed {removed} duplicate baseline analyses for user {user_id}.")
        else:
            print("No duplicate baseline analyses found.")

    def remove_duplicate_baselines_global(self):
        """
        Remove duplicate baseline documents irrespective of user_id.
        
        Keeps newest document per filename across all users.
        """
        pipeline = [
            {"$match": {"filename": {"$regex": BASELINE_REGEX, "$options": "i"}}},
            {"$sort": {"analysis_date": -1}},
            {"$group": {"_id": "$filename", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = list(self.analyses.aggregate(pipeline))
        removed = 0
        for doc in duplicates:
            ids_to_remove = doc["ids"][1:]
            res = self.analyses.delete_many({"_id": {"$in": ids_to_remove}})
            removed += res.deleted_count
        if removed:
            print(f"Globally removed {removed} duplicate baseline documents.")
        else:
            print("No global duplicate baseline documents found.")

    def load_sample_policies_for_user(self, user_id: int) -> bool:
        """
        Load or ensure baseline analyses for a particular user.

        Behaviour:
        1. If the user already possesses analyses whose filename starts with
           "[BASELINE]", nothing is done and the method returns True.
        2. Otherwise, it looks for the global baseline set (user_id == -1)
           and duplicates those documents for the specified user.
        3. When no global baseline is found, the method creates baselines from
           the clean_dataset files directly.
           
        Args:
            user_id: User identifier to load sample policies for
            
        Returns:
            bool: True if baseline policies are available, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        # 1) If user already has any baselines, do nothing
        user_baseline_count = self.analyses.count_documents({
            "user_id": user_id,
            "filename": {"$regex": BASELINE_REGEX, "$options": "i"}
        })
        if user_baseline_count > 0:
            logger.info(f"Baseline analyses already exist for user {user_id} (count={user_baseline_count}) – skipping load.")
            return True

        # 2) If global baselines exist, copy them for the user
        global_baselines = list(self.analyses.find({
            "user_id": -1,
            "filename": {"$regex": BASELINE_REGEX, "$options": "i"}
        }))
        if global_baselines:
            logger.info(f"Found {len(global_baselines)} global baselines – cloning for user {user_id}")
            inserted = 0
            for baseline in global_baselines:
                clone = baseline.copy()
                clone.pop("_id", None)
                clone["user_id"] = user_id
                clone.pop("username", None)
                try:
                    self.analyses.insert_one(clone)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Could not clone baseline {baseline.get('filename')}: {e}")
            logger.info(f"Cloned {inserted} baselines for user {user_id}")
            return inserted > 0

        # 3) Otherwise create global baselines from dataset (and also a user copy if user_id != -1)
        logger.info("No global baselines found – creating from dataset files")
        try:
            from src.database.models import SAMPLE_UNIVERSITIES
            from pathlib import Path
            from src.nlp.text_processor import TextProcessor
            from src.nlp.theme_extractor import ThemeExtractor
            from src.nlp.policy_classifier import PolicyClassifier

            dataset_path = Path("/Users/jaai/Desktop/PROJECT MASTER/App and Report/PolicyCraft/App/PolicyCraft/data/policies/clean_dataset")
            if not dataset_path.exists():
                logger.error(f"Dataset path not found for baseline import: {dataset_path}")
                return False

            text_processor = TextProcessor()
            theme_extractor = ThemeExtractor()
            policy_classifier = PolicyClassifier()
            inserted = 0
            failed = 0

            for key, uni in SAMPLE_UNIVERSITIES.items():
                file_path = dataset_path / uni["file"]
                baseline_filename = f"[BASELINE] {uni['name']}"

                logger.info(f"Processing baseline: {baseline_filename} from file {file_path}")

                # Create global baseline if absent
                if not self.analyses.find_one({"user_id": -1, "filename": baseline_filename}):
                    if file_path.exists():
                        extracted_text = text_processor.extract_text_from_file(str(file_path))
                        if extracted_text:
                            cleaned_text = text_processor.clean_text(extracted_text)
                            text_length = len(cleaned_text) if cleaned_text else 0

                            # Derive real themes and classification from content (no constants)
                            derived_themes = theme_extractor.extract_themes(cleaned_text)
                            derived_classification = policy_classifier.classify_policy(cleaned_text)

                            global_payload = {
                                "user_id": -1,
                                "document_id": uni["file"],
                                "filename": baseline_filename,
                                "analysis_date": datetime.now(timezone.utc),
                                "text_data": {
                                    "original_text": extracted_text,
                                    "cleaned_text": cleaned_text,
                                    "text_length": text_length,
                                },
                                "themes": derived_themes,
                                "classification": derived_classification,
                                "summary": {},
                                "is_baseline": True,
                            }
                            self.analyses.insert_one(global_payload)
                            inserted += 1
                        else:
                            logger.warning(f"Failed to extract text from {file_path}")
                            failed += 1
                            continue
                    else:
                        logger.warning(f"File not found: {file_path}")
                        failed += 1
                        continue

                # Create user copy (if requested user is not global)
                if user_id != -1:
                    doc = self.analyses.find_one({"user_id": -1, "filename": baseline_filename})
                    if doc:
                        clone = doc.copy()
                        clone.pop("_id", None)
                        clone["user_id"] = user_id
                        clone.pop("username", None)
                        self.analyses.insert_one(clone)
                        inserted += 1

            logger.info(f"Created {inserted} baseline analyses for user {user_id} from dataset. Failures: {failed}")
            return inserted > 0
        except Exception as e:
            logger.error(f"Error creating baselines from dataset: {e}", exc_info=True)
            return False