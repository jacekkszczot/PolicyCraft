#!/usr/bin/env python
"""
Script to update all existing policy classifications in the database to use only
standardised categories: Restrictive, Moderate, and Permissive.

This script connects to the MongoDB database and updates all documents in the 'analyses'
collection to ensure they use only the standardised classification categories.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import sys
import os
from pymongo import MongoClient

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the standardisation function from app.py
from app import _standardize_classification

def update_classifications():
    """
    Update all existing policy classifications in the database to use only
    standardised categories: Restrictive, Moderate, and Permissive.
    """
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["policycraft"]
    analyses = db["analyses"]
    
    print("Connected to MongoDB database.")
    print("Starting classification standardisation...")
    
    # Get total count for progress reporting
    total_analyses = analyses.count_documents({})
    print(f"Found {total_analyses} analyses to process.")
    
    # Counter for updates
    updated_count = 0
    
    # Process all analyses
    for analysis in analyses.find():
        updated = False
        
        # Check if classification exists and needs updating
        if 'classification' in analysis:
            if isinstance(analysis['classification'], dict):
                if 'classification' in analysis['classification']:
                    old_classification = analysis['classification']['classification']
                    new_classification = _standardize_classification(old_classification)
                    
                    if old_classification != new_classification:
                        # Update the classification
                        analyses.update_one(
                            {"_id": analysis["_id"]},
                            {"$set": {"classification.classification": new_classification}}
                        )
                        updated = True
                        print(f"Updated: {old_classification} → {new_classification}")
            
            elif isinstance(analysis['classification'], str):
                old_classification = analysis['classification']
                new_classification = _standardize_classification(old_classification)
                
                if old_classification != new_classification:
                    # Update the classification
                    analyses.update_one(
                        {"_id": analysis["_id"]},
                        {"$set": {"classification": new_classification}}
                    )
                    updated = True
                    print(f"Updated: {old_classification} → {new_classification}")
        
        if updated:
            updated_count += 1
    
    print(f"Classification standardisation complete.")
    print(f"Updated {updated_count} out of {total_analyses} analyses.")

if __name__ == "__main__":
    update_classifications()
    print("Script completed successfully.")
