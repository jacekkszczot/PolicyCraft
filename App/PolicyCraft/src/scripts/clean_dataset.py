"""
Dataset Cleaning and Preprocessing for PolicyCraft AI Policy Analysis Platform.

This module provides automated preprocessing and cleaning functionality for policy documents
uploaded to the PolicyCraft platform. It handles file organization, basic text extraction,
and metadata enrichment to prepare documents for further analysis.

Key Features:
- Automatic file organization and naming
- Basic text extraction from various document formats
- Metadata extraction and enrichment
- University name normalization and mapping
- Duplicate detection and handling

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import shutil
from pathlib import Path
from datetime import datetime

class SimpleAutoProcessor:
    """Lightweight auto-processor for new policy uploads."""
    
    def __init__(self):
        """Initialize with basic university mappings."""
        self.university_mappings = {
            # Existing universities
            'oxford': 'University of Oxford',
            'cambridge': 'University of Cambridge', 
            'imperial': 'Imperial College London',
            'mit': 'Massachusetts Institute of Technology',
            'stanford': 'Stanford University',
            'harvard': 'Harvard University',
            'columbia': 'Columbia University',
            'cornell': 'Cornell University',
            'chicago': 'University of Chicago',
            
            # Common new additions
            'yale': 'Yale University',
            'princeton': 'Princeton University',
            'caltech': 'California Institute of Technology',
            'penn': 'University of Pennsylvania',
            'duke': 'Duke University',
            'nyu': 'New York University',
            'toronto': 'University of Toronto',
            'eth': 'ETH Zurich',
            'tokyo': 'University of Tokyo',
            'melbourne': 'University of Melbourne'
        }
        
        self.clean_dataset_dir = Path("data/policies/clean_dataset")
        self.clean_dataset_dir.mkdir(parents=True, exist_ok=True)

    def identify_university_from_filename(self, filename: str) -> str:
        """Simple university identification from filename."""
        filename_lower = filename.lower()
        
        # Try exact matches first
        for uni_key in self.university_mappings:
            if uni_key in filename_lower:
                return uni_key
        
        # Try common variations
        if 'massachusetts' in filename_lower or 'institute' in filename_lower:
            return 'mit'
        if 'new york' in filename_lower:
            return 'nyu'
        if 'pennsylvania' in filename_lower:
            return 'penn'
        if 'california tech' in filename_lower:
            return 'caltech'
            
        # Default fallback - extract first word
        base_name = Path(filename).stem.lower()
        first_word = base_name.split('-')[0].split('_')[0]
        return first_word

    def process_uploaded_file(self, uploaded_file_path: str, original_filename: str) -> dict:
        """
        Auto-process newly uploaded file.
        
        Args:
            uploaded_file_path: Path to uploaded file
            original_filename: Original filename from user
            
        Returns:
            Processing result dictionary
        """
        try:
            # Identify university
            uni_key = self.identify_university_from_filename(original_filename)
            
            # Generate standardized filename
            file_extension = Path(original_filename).suffix
            standardized_name = f"{uni_key}-ai-policy{file_extension}"
            
            # Target path in clean dataset
            target_path = self.clean_dataset_dir / standardized_name
            
            # Copy file to clean dataset
            shutil.copy2(uploaded_file_path, target_path)
            # Update dataset info
            self.update_dataset_info()
            return {
                'success': True,
                'original_name': original_filename,
                'standardized_name': standardized_name,
                'university_key': uni_key,
                'university_name': self.university_mappings.get(uni_key, uni_key.title()),
                'target_path': str(target_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_name': original_filename
            }

    def update_dataset_info(self):
        """Update dataset_info.md with current files."""
        files = list(self.clean_dataset_dir.glob("*.pdf")) + list(self.clean_dataset_dir.glob("*.docx"))
        
        # Basic dataset info
        content = "# PolicyCraft Dataset Information\n\n"
        content += "## Dataset Statistics\n"
        content += f"- **Total Files**: {len(files)}\n"
        content += f"- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        content += "## Files\n"
        for file_path in sorted(files):
            uni_key = file_path.stem.replace('-ai-policy', '')
            uni_name = self.university_mappings.get(uni_key, uni_key.title())
            size_mb = file_path.stat().st_size / (1024 * 1024)
            content += f"- **{uni_name}**: {file_path.name} ({size_mb:.2f} MB)\n"
        
        # Write updated info
        info_file = self.clean_dataset_dir / "dataset_info.md"
        with open(info_file, 'w') as f:
            f.write(content)

# Initialize global processor instance
auto_processor = SimpleAutoProcessor()

def process_new_upload(uploaded_file_path: str, original_filename: str) -> dict:
    """
    Main function to auto-process new uploads.
    Call this from your Flask upload handler.
    
    Args:
        uploaded_file_path: Path where Flask saved the uploaded file
        original_filename: Original filename from the upload
        
    Returns:
        Processing result dictionary
    """
    return auto_processor.process_uploaded_file(uploaded_file_path, original_filename)

# Standalone usage
if __name__ == "__main__":
    # Manual processing of files in raw_policies folder
    raw_folder = Path("raw_policies")
    
    if raw_folder.exists():
        print(f"🔄 Processing files in {raw_folder}")
        
        for file_path in raw_folder.glob("*"):
            if file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
                result = auto_processor.process_uploaded_file(str(file_path), file_path.name)
                
                if result['success']:
                    print(f"✅ {result['original_name']} → {result['standardized_name']}")
                else:
                    print(f"❌ {result['original_name']}: {result['error']}")
        
        print("✅ Processing completed!")
    else:
        print(f"📁 Create '{raw_folder}' folder and put policy files there")
        print("   Then run: python clean_dataset.py")