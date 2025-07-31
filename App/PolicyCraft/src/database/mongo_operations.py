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
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

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
            print(f"[MongoOperations] Index creation warning: {e}")

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
        return list(self.analyses.find({"user_id": user_id}).sort("analysis_date", DESCENDING))

    def remove_duplicate_analyses(self, user_id: int) -> int:
        """
        Delete duplicate analyses for a user keeping the most recent per filename.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of documents removed
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"analysis_date": -1}},  # newest first
            {"$group": {
                "_id": "$filename",
                "docs": {"$push": "$_id"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]
        groups = list(self.analyses.aggregate(pipeline))
        to_delete = []
        for g in groups:
            # skip first (newest) id, delete the rest
            to_delete.extend(g["docs"][1:])
        if to_delete:
            result = self.analyses.delete_many({"_id": {"$in": to_delete}})
            return result.deleted_count
        return 0

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
            "filename": {"$not": {"$regex": r"^\\[BASELINE\\]"}}
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
            "user_id": user_id,
            "analysis_id": analysis_id,
            "recommendations": recs,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.recommendations.insert_one(payload)
        return str(result.inserted_id)

    # User data cleanup helpers

    def purge_user_data(self, user_id: int):
        """
        Delete all analyses and recommendations associated with a user.
        
        Args:
            user_id: User identifier whose data should be purged
        """
        res1 = self.analyses.delete_many({"user_id": user_id})
        res2 = self.recommendations.delete_many({"user_id": user_id})
        print(f"Purged {res1.deleted_count} analyses and {res2.deleted_count} recommendations for user {user_id}")

    # Baseline policy management helpers

    def deduplicate_baseline_analyses(self, user_id: int):
        """
        Remove duplicate baseline analyses for a given user, keeping the newest document.

        Duplicate means same user_id and filename. Keep the most recent (analysis_date max).
        
        Args:
            user_id: User identifier to deduplicate baseline analyses for
        """
        pipeline = [
            {"$match": {"user_id": user_id, "filename": {"$regex": r"^\\[BASELINE\\]", "$options": "i"}}},
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
            {"$match": {"filename": {"$regex": r"^\\[BASELINE\\]", "$options": "i"}}},
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
        3. When no global baseline is found, the method returns False so the
           caller can decide how to proceed.
           
        Args:
            user_id: User identifier to load sample policies for
            
        Returns:
            bool: True if baseline policies are available, False otherwise
        """
        # Check if user already has baseline analyses
        has_user_baseline = self.analyses.find_one({
            "user_id": user_id,
            "filename": {"$regex": r"^\\[BASELINE\\]"}
        })
        if has_user_baseline:
            print(f"Baseline analyses already exist for user {user_id} – skipping copy.")
            return True

        # Fetch global baseline documents
        global_baselines = list(self.analyses.find({
            "user_id": -1,
            "filename": {"$regex": r"^\\[BASELINE\\]"}
        }))
        if not global_baselines:
            # Fallback: create baselines from dataset files
            try:
                from src.database.models import SAMPLE_UNIVERSITIES
                from pathlib import Path

                dataset_path = Path("data/policies/clean_dataset")
                if not dataset_path.exists():
                    print("Dataset path not found for baseline import.")
                    return False

                inserted = 0
                for key, uni in SAMPLE_UNIVERSITIES.items():
                    file_path = dataset_path / uni["file"]
                    baseline_filename = f"[BASELINE] {uni['name']} - {uni['file']}"

                    # Avoid duplicates just in case
                    if self.analyses.find_one({"user_id": user_id, "filename": baseline_filename}):
                        continue

                    payload: Analysis = {
                        "user_id": user_id,
                        "document_id": f"sample_{key}",
                        "filename": baseline_filename,
                        "analysis_date": datetime.now(timezone.utc),
                        "text_data": {
                            "original_text": f"Sample policy from {uni['name']}",
                            "cleaned_text": f"Sample policy from {uni['name']} ({uni['country']})",
                            "text_length": 0,
                        },
                        "themes": [{"name": t, "score": 0.8, "confidence": 85} for t in uni.get("themes", [])],
                        "classification": {
                            "classification": uni.get("classification", "Unknown"),
                            "confidence": 85,
                            "source": "Sample Dataset",
                        },
                        "summary": {},
                    }
                    self.analyses.insert_one(payload)
                    inserted += 1
                print(f"Inserted {inserted} baseline analyses for user {user_id} from dataset files.")
                return inserted > 0
            except Exception as e:
                print(f"Error loading baseline dataset: {e}")
                return False

        # Clone global baselines for the specified user
        inserted = 0
        seen_filenames: set[str] = set()
        for base_doc in global_baselines:
            if base_doc.get("filename") in seen_filenames:
                continue
            seen_filenames.add(base_doc.get("filename"))
            clone = base_doc.copy()
            clone.pop("_id", None)  # Let MongoDB assign a new ID
            clone["user_id"] = user_id
            # Ensure username removed as it will be owner specific
            clone.pop("username", None)
            try:
                self.analyses.insert_one(clone)
                inserted += 1
            except Exception as e:
                # Ignore duplicates or other insertion errors per document
                print(f"Could not clone baseline {base_doc.get('filename')}: {e}")
        print(f"Added {inserted} baseline analyses for user {user_id}.")
        return inserted > 0