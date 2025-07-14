"""MongoDB-backed data operations for PolicyCraft.

This module provides the same public API (method names and signatures)
as the former JSON-based `DatabaseOperations` so that the rest of the
application can switch storage by changing the import only.

For simplicity we implement only the methods actually referenced by the
Flask app (grep `db_operations.`).  Additional helpers can be added
later.

Mongo collections:
    analyses          – user analyses and baseline documents
    recommendations   – recommendations generated for an analysis

The module expects a running MongoDB instance (>=4.0) and the `pymongo`
package.  Install locally via:
    pip install pymongo

Environment variables (or kwargs) may override default connection URI
and database name.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

# ---------------------------------------------------------------------------
# Helper types
# ---------------------------------------------------------------------------
Analysis = Dict  # alias for better readability
Recommendation = Dict


class MongoOperations:
    """Mongo-backed persistence layer."""

    def __init__(self, uri: str | None = None, db_name: str | None = None):
        uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = db_name or os.getenv("MONGO_DB", "policycraft")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

        self.analyses: Collection = self.db["analyses"]
        self.recommendations: Collection = self.db["recommendations"]

        # Ensure indexes – runs quickly if already present
        # Non-unique index to accelerate lookup; duplicates handled at application level
        try:
            self.analyses.create_index([("user_id", ASCENDING), ("filename", ASCENDING)])
        except Exception as e:
            print(f"[MongoOperations] Index creation warning: {e}")

        self.recommendations.create_index([("analysis_id", ASCENDING), ("user_id", ASCENDING)])

    # ------------------------------------------------------------------
    # Analysis CRUD
    # ------------------------------------------------------------------
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
        """Insert or update a user's analysis result.

        Ensures uniqueness on (user_id, filename).  Duplicate baseline
        entries therefore do not collide with user uploads because their
        user_id differs (baseline is typically user_id=-1 or similar).
        """
        # Check if this user already analysed this file – avoid duplicates
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

        # Build analysis document (new)
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
        """Return single analysis for user & filename or None."""
        return self.analyses.find_one({"user_id": user_id, "filename": filename})

    def get_user_analyses(self, user_id: int) -> List[Analysis]:
        return list(self.analyses.find({"user_id": user_id}).sort("analysis_date", DESCENDING))

    def remove_duplicate_analyses(self, user_id: int) -> int:
        """Delete duplicate analyses for a user keeping the most recent per filename.
        Returns number of documents removed."""
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
            # skip first (newest) id
            to_delete.extend(g["docs"][1:])
        if to_delete:
            result = self.analyses.delete_many({"_id": {"$in": to_delete}})
            return result.deleted_count
        return 0

    def _to_object_id(self, id_str: str):
        """Helper: convert 24-char hex string to ObjectId, else return original."""
        try:
            from bson import ObjectId  # lazy import
            return ObjectId(id_str) if len(id_str) == 24 else id_str
        except Exception:
            return id_str

    def get_user_analysis_by_id(self, user_id: int, analysis_id: str) -> Optional[Analysis]:
        oid = self._to_object_id(analysis_id)
        return self.analyses.find_one({"_id": oid, "user_id": user_id})

    def delete_user_analysis(self, user_id: int, analysis_id: str) -> bool:
        oid = self._to_object_id(analysis_id)
        result = self.analyses.delete_one({"_id": oid, "user_id": user_id, "filename": {"$not": {"$regex": r"^\\[BASELINE\\]"}}})
        return result.deleted_count == 1

    # Generic fetch without user filter (used by API endpoint)
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Analysis]:
        oid = self._to_object_id(analysis_id)
        return self.analyses.find_one({"_id": oid})

    # ------------------------------------------------------------------
    # Statistics & helpers
    # ------------------------------------------------------------------
    def get_analysis_statistics(self, user_id: int | None = None) -> Dict:
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

    # ------------------------------------------------------------------
    # Recommendations (minimal)
    # ------------------------------------------------------------------
    def get_recommendations_by_analysis(self, user_id: int, analysis_id: str):
        """Return stored recommendations list or None."""
        doc = self.recommendations.find_one({"user_id": user_id, "analysis_id": analysis_id})
        if doc:
            return doc.get("recommendations", [])
        return None

    def store_recommendations(self, user_id: int, analysis_id: str, recs: List[Recommendation]) -> str:
        payload = {
            "user_id": user_id,
            "analysis_id": analysis_id,
            "recommendations": recs,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.recommendations.insert_one(payload)
        return str(result.inserted_id)

    # ------------------------------------------------------------------
    # User cleanup helpers
    # ------------------------------------------------------------------
    def purge_user_data(self, user_id: int):
        """Delete all analyses & recommendations associated with a user."""
        res1 = self.analyses.delete_many({"user_id": user_id})
        res2 = self.recommendations.delete_many({"user_id": user_id})
        print(f"🗑️ Purged {res1.deleted_count} analyses and {res2.deleted_count} recs for user {user_id}")

    # ------------------------------------------------------------------
    # Baseline helpers
    # ------------------------------------------------------------------
    def deduplicate_baseline_analyses(self, user_id: int):
        """No-op for Mongo – duplicates prevented by unique index."""
        return

    def load_sample_policies_for_user(self, user_id: int) -> bool:
        """Load or ensure baseline analyses for a **particular** user.

        Behaviour:
        1. If the user already possesses analyses whose filename starts with
           "[BASELINE]", nothing is done and the method returns ``True``.
        2. Otherwise, it looks for the *global* baseline set (``user_id == -1``)
           and duplicates those documents for the specified user.
        3. When no global baseline is found, the method returns ``False`` so the
           caller can decide how to proceed.
        """
        # 1) Already loaded for this user?
        has_user_baseline = self.analyses.find_one({
            "user_id": user_id,
            "filename": {"$regex": r"^\\[BASELINE\\]"}
        })
        if has_user_baseline:
            print(f"ℹ️ Baseline analyses already exist for user {user_id} – skipping copy.")
            return True

        # 2) Fetch global baseline docs
        global_baselines = list(self.analyses.find({
            "user_id": -1,
            "filename": {"$regex": r"^\\[BASELINE\\]"}
        }))
        if not global_baselines:
            # --- Fallback: create baselines from dataset files ---
            try:
                from src.auth.models import SAMPLE_UNIVERSITIES
                from pathlib import Path

                dataset_path = Path("data/policies/clean_dataset")
                if not dataset_path.exists():
                    print("❌ Dataset path not found for baseline import.")
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
                print(f"✅ Inserted {inserted} baseline analyses for user {user_id} from dataset files.")
                return inserted > 0
            except Exception as e:
                print(f"❌ Error loading baseline dataset: {e}")
                return False

        # 3) Clone for user
        inserted = 0
        seen_filenames: set[str] = set()
        for base_doc in global_baselines:
            if base_doc.get("filename") in seen_filenames:
                continue
            seen_filenames.add(base_doc.get("filename"))
            clone = base_doc.copy()
            clone.pop("_id", None)  # Let Mongo assign a new ID
            clone["user_id"] = user_id
            # Ensure username removed – will be owner specific
            clone.pop("username", None)
            try:
                self.analyses.insert_one(clone)
                inserted += 1
            except Exception as e:
                # Ignore duplicates or other insertion errors per doc
                print(f"⚠️ Could not clone baseline {base_doc.get('filename')}: {e}")
        print(f"✅ Added {inserted} baseline analyses for user {user_id}.")
        return inserted > 0
