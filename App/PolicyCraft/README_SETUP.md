# PolicyCraft Setup Guide

## Quick Start (Automated)

For automated installation of all dependencies:

```bash
python setup_dependencies.py
python app.py
```

## Manual Installation

If you prefer manual setup:

### 1. Install Python packages
```bash
pip install -r requirements.txt
```

### 2. Download NLP models
```bash
# spaCy English model (REQUIRED)
python -m spacy download en_core_web_sm

# NLTK data (REQUIRED for enhanced text processing)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

### 3. Enable advanced features (RECOMMENDED)
```bash
echo "FEATURE_ADVANCED_ENGINE=1" >> .env
```

### 4. Start application
```bash
python app.py
```

## Dependency Validation

PolicyCraft includes comprehensive startup validation that will:
- ✅ Check all required Python packages
- ✅ Validate NLP models (spaCy, SentenceTransformers)
- ✅ Verify NLTK data availability
- ✅ Check environment configuration
- ❌ **ABORT startup** if critical dependencies are missing
- ⚠️  Show warnings for optional components

If validation fails, the application will display detailed error messages and installation instructions.

## Troubleshooting

### Common Issues

**spaCy model not found:**
```bash
python -m spacy download en_core_web_sm
```

**NLTK data missing:**
```bash
python -c "import nltk; nltk.download('all')"
```

**SentenceTransformers download issues:**
- Ensure internet connection
- Check firewall settings
- Models are downloaded automatically on first use

### Full Functionality Check

The application validates these components at startup:

**Core Dependencies (CRITICAL):**
- Flask, pymongo, pandas, numpy, requests
- spaCy with en_core_web_sm model
- SentenceTransformers with all-MiniLM-L6-v2 model
- scikit-learn, NLTK, contractions

**Document Processing (RECOMMENDED):**
- PyMuPDF (fitz), python-docx, pypdf, pdfplumber

**Visualization (RECOMMENDED):**
- plotly, kaleido, reportlab, xlsxwriter

**Environment (OPTIONAL):**
- FEATURE_ADVANCED_ENGINE=1 (enables advanced analysis)
- MONGODB_URI (for custom database)
- SECRET_KEY (for production security)

If any CRITICAL dependency is missing, the application will not start and will provide specific installation instructions.