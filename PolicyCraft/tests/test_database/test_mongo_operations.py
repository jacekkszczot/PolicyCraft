"""
Test Suite for MongoDB Operations in PolicyCraft AI Policy Analysis Platform.

This module contains comprehensive tests for the MongoOperations class, which handles
all database interactions with MongoDB for the PolicyCraft application. The tests
verify the correct storage, retrieval, and management of policy analyses and
recommendations in the database.

Key Test Areas:
- Storage and retrieval of policy analysis results
- Management of recommendation data
- Database connection and error handling
- Data integrity and isolation

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import pytest
from src.database.mongo_operations import MongoOperations


@pytest.fixture(scope="module")
def mongo_db():
    """Provide a clean test database and tear it down afterwards."""
    db = MongoOperations(uri="mongodb://localhost:27017", db_name="policycraft_test")
    # Ensure isolation
    db.analyses.delete_many({})
    db.recommendations.delete_many({})
    yield db
    # Cleanup
    db.analyses.delete_many({})
    db.recommendations.delete_many({})


def test_store_and_fetch_analysis(mongo_db):
    analysis_id = mongo_db.store_user_analysis_results(
        user_id=42,
        filename="dummy.txt",
        original_text="orig",
        cleaned_text="clean",
        themes=[],
        classification={"classification": "Moderate", "confidence": 80},
        document_id=None,
        username="tester",
    )
    result = mongo_db.get_user_analysis_by_id(42, analysis_id)
    assert result is not None
    assert result["filename"] == "dummy.txt"


def test_store_and_fetch_recommendations(mongo_db):
    analysis_id = mongo_db.store_user_analysis_results(
        user_id=1,
        filename="sample.txt",
        original_text="o",
        cleaned_text="c",
        themes=[],
        classification={"classification": "Low", "confidence": 70},
    )
    recs = [{"text": "Improve disclosure", "priority": "high"}]
    mongo_db.store_recommendations(1, analysis_id, recs)
    fetched = mongo_db.get_recommendations_by_analysis(1, analysis_id)
    assert fetched and fetched[0]["text"].startswith("Improve")
