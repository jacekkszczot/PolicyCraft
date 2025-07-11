"""
Script to fix baseline filenames in the database.
Ensures all baseline files have the [BASELINE] prefix and proper formatting.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database.operations import DatabaseOperations

def fix_baseline_filenames():
    """Update baseline filenames in the database to follow the correct format."""
    db = DatabaseOperations()
    updated_count = 0
    
    # Get all analyses that should be marked as baseline
    for analysis in db.storage['analyses']:
        filename = analysis.get('filename', '')
        document_id = analysis.get('document_id', '')
        
        # Check if this is a baseline analysis but doesn't have the prefix
        is_baseline = (
            'clean_dataset' in filename or 
            (isinstance(document_id, str) and document_id.startswith('sample_'))
        )
        
        if is_baseline and not filename.startswith('[BASELINE]'):
            # Extract university name from filename or use a default
            uni_name = 'Sample University'
            if ' - ' in filename:
                # If already has a university name in the format "University - filename"
                parts = filename.split(' - ', 1)
                if len(parts) > 1:
                    uni_name = parts[0]
                    filename = parts[1]
            
            # Update the filename with the [BASELINE] prefix
            new_filename = f"[BASELINE] {uni_name} - {os.path.basename(filename)}"
            print(f"Updating filename: {analysis['filename']} -> {new_filename}")
            analysis['filename'] = new_filename
            updated_count += 1
    
    if updated_count > 0:
        db._save_storage()
        print(f"✅ Updated {updated_count} baseline filenames")
    else:
        print("ℹ️ No baseline filenames needed updating")

if __name__ == "__main__":
    print("🔧 Starting baseline filename fix script...")
    fix_baseline_filenames()
    print("✅ Script completed")
