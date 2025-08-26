"""
Main Flask Application for PolicyCraft AI Policy Analysis Platform.

This is the main Flask application file that orchestrates the PolicyCraft platform,
providing comprehensive AI policy analysis capabilities for higher education institutions.
The application integrates multiple analysis engines, literature processing, and 
recommendation systems to deliver actionable insights for AI policy development.

Key Features:
- Multi-file policy document upload and batch processing
- Comprehensive policy analysis using NLP and machine learning
- Intelligent recommendation generation with academic literature integration
- Interactive dashboard with visualisations and export capabilities
- Administrative interface for literature and user management
- Secure user authentication and session management

Architecture:
- Flask web framework with Blueprint-based modular routing
- MongoDB for persistent data storage
- Integrated NLP pipeline using spaCy and custom classification models
- Literature processing engine with knowledge base management
- Export capabilities supporting PDF, Word, Excel, and JSON formats

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

# Load environment variables from a .env file if present
from dotenv import load_dotenv
load_dotenv()

def _fetch_analysis_for_recommendations(analysis_id):
    """Fetch analysis by user first, then globally, mirroring logs and test-temporary permission notes."""
    logger.info("Attempting to get user's analysis...")
    analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
    if analysis:
        logger.info("Found analysis in user's analyses")
        logger.info(f"Analysis details - User ID: {analysis.get('user_id')}, Is Baseline: {analysis.get('is_baseline', False)}")
        return analysis

    logger.warning(f"{ANALYSIS_NOT_FOUND} in user's analyses, trying global lookup...")
    analysis = db_operations.get_analysis_by_id(analysis_id)
    if analysis:
        logger.info("Found analysis in global collection")
        logger.info(f"Analysis details - ID: {analysis.get('_id')}")
        logger.info(f"Analysis owner: User ID: {analysis.get('user_id')}, Username: {analysis.get('username')}")
        logger.info(f"Is baseline: {analysis.get('is_baseline', False)}")
        logger.info(f"Analysis user_id: {analysis.get('user_id')}, Current user ID: {current_user.id}")
        logger.info(f"Analysis username: {analysis.get('username')}, Current username: {getattr(current_user, 'username', 'N/A')}")
        return analysis
    return None

def _extract_cleaned_text_with_logging(analysis):
    """Extract cleaned text and log sizes as in original code."""
    text_data = analysis.get('text_data', {})
    cleaned_text = text_data.get('cleaned_text', text_data.get('original_text', ''))
    logger.info(f"Extracted data - Themes: {len(analysis.get('themes', []))}, Classification: {analysis.get('classification', {})}")
    logger.info(f"Text data length: {len(cleaned_text) if cleaned_text else 0} chars")
    return cleaned_text

def _load_or_generate_recommendations(analysis_id, cleaned_text, themes=None, classification=None):
    """Load stored recommendations; always (re)build narrative and metadata.

    Returns a complete package compatible with RecommendationEngine, so that the template has
    access to 'narrative', 'analysis_metadata', etc. When stored recommendations exist,
    we replace them in the generated package to preserve recommendation content.
    """
    try:
        stored_recs = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)

        # Run engine to build coverage, sources and narrative
        engine_package = recommendation_engine.generate_recommendations(
            themes=themes or [],
            classification=classification or {},
            text=cleaned_text,
            analysis_id=analysis_id,
        )

        if stored_recs:
            # Merge recommendations: keep rich fields from engine (e.g. sources, implementation_steps),
            # but include user content/edits from storage. Link by title; no title → by index.
            engine_recs = engine_package.get('recommendations', []) or []

            def norm_title(rec):
                t = (rec or {}).get('title')
                return (t or '').strip().lower()

            engine_by_title = {norm_title(r): r for r in engine_recs if norm_title(r)}
            used_engine_titles = set()
            merged = []

            for idx, s in enumerate(stored_recs):
                base = None
                key = norm_title(s)
                if key and key in engine_by_title:
                    base = engine_by_title[key]
                    used_engine_titles.add(key)
                elif idx < len(engine_recs):
                    base = engine_recs[idx]
                else:
                    base = {}

                # Merge fields: prefer stored when present, otherwise engine
                m = {}
                m['title'] = s.get('title') or base.get('title')
                m['description'] = s.get('description') or base.get('description')
                m['priority'] = (s.get('priority') or base.get('priority'))
                m['timeframe'] = (s.get('timeframe') or base.get('timeframe'))

                # Implementation steps: prefer stored, else engine
                steps = s.get('implementation_steps') or base.get('implementation_steps') or []
                m['implementation_steps'] = steps

                # Sources: normalise to list and preserve richest available
                def to_list(srcs, single):
                    if srcs:
                        return list(srcs)
                    if single:
                        return [single]
                    return []

                s_sources = to_list(s.get('sources'), s.get('source'))
                e_sources = to_list(base.get('sources'), base.get('source'))
                m['sources'] = s_sources or e_sources
                # Keep backward compatibility: also set single 'source' if only one
                m['source'] = m['sources'][0] if isinstance(m.get('sources'), list) and len(m['sources']) == 1 else s.get('source') or base.get('source')

                # Include any additional engine fields not explicitly handled
                for k, v in (base or {}).items():
                    if k not in m and v is not None:
                        m[k] = v
                # Overlay any additional stored fields
                for k, v in (s or {}).items():
                    if v is not None:
                        m[k] = v

                merged.append(m)

            # Append engine-only recommendations not matched by title
            for e in engine_recs:
                key = norm_title(e)
                if key and key in used_engine_titles:
                    continue
                # avoid duplicates by simple title check against merged
                if any(norm_title(x) and norm_title(x) == key for x in merged):
                    continue
                merged.append(e)

            engine_package['recommendations'] = merged
            # Mark metadata that recommendations come from database and engine
            meta = engine_package.get('analysis_metadata', {})
            meta['methodology'] = (meta.get('methodology') or 'Engine') + ' + Stored Recommendations (merged)'
            engine_package['analysis_metadata'] = meta
            return engine_package

        # No stored recommendations - use full package from engine
        return engine_package

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return None

def _get_or_create_analysis_record(filename: str, is_baseline: bool, file_path: str):
    """Get existing analysis or run new one and return complete data.
    Returns: extracted_text, cleaned_text, themes, classification, analysis_id
    Raises ValueError('no_text') if text extraction failed (maintains existing behaviour).
    """
    existing = _get_existing_analysis_record(filename, is_baseline)
    if existing:
        themes, classification, cleaned_text, extracted_text, analysis_id = _unpack_existing_analysis(existing)
        return extracted_text, cleaned_text, themes, classification, analysis_id

    # Robust path: always attempt fallback extraction and safe downstream steps.
    # Derive a human-friendly university/institution name for placeholder messaging.
    uni_guess = filename.split('-')[0].replace('university', '').strip().title() or 'User Institution'
    try:
        extracted_text = _extract_text_with_fallback(file_path, uni_guess)
        cleaned_text = _clean_text_safe(extracted_text, filename)
        themes = _extract_themes_safe(cleaned_text, filename)
        classification = _classify_policy_safe(cleaned_text, filename)
    except Exception as e:
        logger.error(f"Dashboard: Robust analysis pipeline failed for {filename}: {e}")
        # Absolute fallback to minimal safe values (should rarely happen)
        extracted_text = (
            f"AI Policy document from {uni_guess}. This is a placeholder text as the original document "
            f"could not be processed due to: {e}"
        )
        cleaned_text = extracted_text
        themes = [
            {"name": "Policy", "score": 0.8, "confidence": 75},
            {"name": THEME_AI_ETHICS, "score": 0.7, "confidence": 70},
        ]
        classification = {
            "classification": "Moderate",
            "confidence": 75,
            "source": SOURCE_BASELINE_DEFAULT,
        }

    analysis_id = _store_analysis_results(filename, extracted_text, cleaned_text, themes, classification)
    return extracted_text, cleaned_text, themes, classification, analysis_id

def _build_basic_export_data(analysis_id, analysis, recommendations, recommendation_package=None):
    """Build the base export data package used by PDF/Word/Excel (without charts)."""
    # Extract confidence factors and calculate confidence percentage
    confidence_factors = {}
    if recommendation_package and isinstance(recommendation_package, dict):
        package_analysis = recommendation_package.get('analysis', {})
        confidence_factors = package_analysis.get('confidence_factors') or package_analysis.get('confidence', {}).get('factors', {})
        # Debug logging
        logger.info(f"Export binary: confidence_factors from package: {confidence_factors}")
    else:
        confidence_factors = analysis.get('confidence_factors', {})
        # Debug logging
        logger.info(f"Export binary: confidence_factors from analysis: {confidence_factors}")
    
    confidence_raw = analysis.get('classification', {}).get('confidence', 0)
    confidence_pct = confidence_raw * 100 if confidence_raw <= 1 else confidence_raw
    
    return {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': analysis.get('classification', {}).get('classification', 'Unknown'),
            'confidence': confidence_raw,
            'confidence_pct': confidence_pct,
            'confidence_factors': confidence_factors,
            'analysis_id': analysis_id,
            'themes': analysis.get('themes', [])
        },
        'recommendations': recommendations,
        'generated_date': datetime.now().isoformat(),
        'total_recommendations': len(recommendations),
        'methodology': 'PolicyCraft local analysis pipeline (text extraction → classification → theme detection → rules‑based + ML heuristics).'
    }

def _require_analysis_or_redirect(analysis_id):
    """Ensure analysis exists; otherwise flash and redirect."""
    analysis = _get_export_analysis(analysis_id)
    if analysis is None:
        logger.error(f"Analysis {analysis_id} not found in global lookup")
        flash(f'{ANALYSIS_NOT_FOUND}.', 'error')
        return None, redirect(url_for('recommendations'))
    return analysis, None

def _require_recommendations_or_redirect(analysis_id):
    """Ensure recommendations exist; otherwise flash and redirect to generator."""
    # This function is no longer needed since export works directly from recommendations page
    return None, None

def _prepare_basic_export_data_or_error(analysis_id):
    """Fetch analysis and recommendations; return (export_data, None) or (None, (json, code))."""
    analysis = _get_export_analysis(analysis_id)
    if not analysis:
        return None, (jsonify({'error': ANALYSIS_NOT_FOUND}), 404)

    # Ensure we get full package including narrative for binary exports
    try:
        prep, err = _prepare_recommendation_inputs(analysis_id)
        if err:
            return None, err
        _, themes, classification, cleaned_text = prep
        package = _load_or_generate_recommendations(
            analysis_id,
            cleaned_text,
            themes=themes,
            classification=classification,
        )
        if not package:
            return None, (jsonify({'error': NO_RECOMMENDATIONS_FOUND}), 404)
        recommendations = package.get('recommendations', [])
        narrative = package.get('narrative', {})
    except Exception:
        # No fallback needed - if package generation fails, return error
        return None, (jsonify({'error': NO_RECOMMENDATIONS_FOUND}), 404)

    base = _build_basic_export_data(analysis_id, analysis, recommendations, package)
    base['narrative'] = narrative
    # Add charts for binary exports
    try:
        themes = analysis.get('themes', [])
        classification = analysis.get('classification', {})
        cleaned_text = analysis.get('text_data', {}).get('cleaned_text', '')
        base['charts'] = chart_generator.generate_analysis_charts(themes, classification, cleaned_text)
    except Exception as chart_error:
        logger.error(f"Error generating charts: {chart_error}")
        base['charts'] = {}
    return base, None

def _make_binary_response(binary_data: bytes, content_type: str, filename: str):
    """Create a binary HTTP response with appropriate headers."""
    response = make_response(binary_data)
    response.headers['Content-Type'] = content_type
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def _export_binary_via_engine(export_data: dict, analysis_id: str, fmt: str):
    """Common export helper for PDF/Word/Excel. fmt in {'pdf','word','excel'}."""
    from src.export import ExportEngine
    export_engine = ExportEngine()
    if fmt == 'pdf':
        binary = export_engine.export_to_pdf(export_data)
        ctype = 'application/pdf'
        ext = 'pdf'
    elif fmt == 'word':
        binary = export_engine.export_to_word(export_data)
        ctype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ext = 'docx'
    elif fmt == 'excel':
        binary = export_engine.export_to_excel(export_data)
        ctype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
    return _make_binary_response(binary, ctype, f'PolicyCraft_Analysis_{analysis_id}.{ext}')

def _build_recommendation_data(analysis_id, analysis, themes, classification, recommendation_package):
    """Build the data dict for recommendations template, matching original keys."""
    # Normalise confidence to 0-100%
    raw_conf = (classification or {}).get('confidence', 0)
    try:
        conf_val = float(raw_conf if raw_conf is not None else 0)
    except Exception:
        conf_val = 0.0
    if conf_val <= 1.0:
        conf_pct = round(conf_val * 100.0, 1)
    else:
        conf_pct = round(conf_val, 1)
    # Clamp to [0, 100]
    conf_pct = max(0.0, min(100.0, conf_pct))

    extended = recommendation_package.get('analysis', {}) if isinstance(recommendation_package, dict) else {}
    
    # Debug logging
    logger.info(f"Export view: extended data keys: {list(extended.keys()) if extended else 'None'}")
    logger.info(f"Export view: confidence_factors: {extended.get('confidence_factors')}")
    logger.info(f"Export view: confidence data: {extended.get('confidence')}")
    
    # Build the data structure for template
    template_data = {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': classification.get('classification', 'Unknown'),
            'confidence': classification.get('confidence', 0),
            'confidence_pct': conf_pct,
            'confidence_factors': extended.get('confidence_factors') or extended.get('confidence', {}).get('factors'),
            'stakeholders': extended.get('stakeholders'),
            'risk_benefit': extended.get('risk_benefit'),
            'analysis_id': analysis_id,
            'themes_count': len(themes)
        },
        'recommendations': recommendation_package.get('recommendations', []),
        'coverage_analysis': recommendation_package.get('coverage_analysis', {}),
        'gaps': recommendation_package.get('identified_gaps', []),
        'generated_date': recommendation_package.get('analysis_metadata', {}).get('generated_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        'methodology': recommendation_package.get('analysis_metadata', {}).get('methodology', 'Ethical Framework Analysis'),
        'academic_sources': recommendation_package.get('analysis_metadata', {}).get('academic_sources', []),
        'summary': recommendation_package.get('summary', {}),
        'total_recommendations': len(recommendation_package.get('recommendations', [])),
        'narrative': recommendation_package.get('narrative', {})
    }
    
    # Debug the final template data
    logger.info(f"Export view: Final template data structure:")
    logger.info(f"  - analysis.confidence_factors: {template_data['analysis'].get('confidence_factors')}")
    logger.info(f"  - analysis.stakeholders: {template_data['analysis'].get('stakeholders')}")
    logger.info(f"  - analysis.risk_benefit: {template_data['analysis'].get('risk_benefit')}")
    
    return template_data

    return {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': classification.get('classification', 'Unknown'),
            'confidence': classification.get('confidence', 0),
            'confidence_pct': conf_pct,
            'confidence_factors': extended.get('confidence_factors') or extended.get('confidence', {}).get('factors'),
            'stakeholders': extended.get('stakeholders'),
            'risk_benefit': extended.get('risk_benefit'),
            'analysis_id': analysis_id,
            'themes_count': len(themes)
        },
        'recommendations': recommendation_package.get('recommendations', []),
        'coverage_analysis': recommendation_package.get('coverage_analysis', {}),
        'gaps': recommendation_package.get('identified_gaps', []),
        'generated_date': recommendation_package.get('analysis_metadata', {}).get('generated_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        'methodology': recommendation_package.get('analysis_metadata', {}).get('methodology', 'Ethical Framework Analysis'),
        'academic_sources': recommendation_package.get('analysis_metadata', {}).get('academic_sources', []),
        'summary': recommendation_package.get('summary', {}),
        'total_recommendations': len(recommendation_package.get('recommendations', [])),
        'narrative': recommendation_package.get('narrative', {})
    }

def _store_recommendations_safe(analysis_id, recommendation_package):
    """Store recommendations, logging but not failing flow on errors."""
    try:
        rec_id = db_operations.store_recommendations(
            user_id=current_user.id,
            analysis_id=analysis_id,
            recs=recommendation_package.get('recommendations', [])
        )
        logger.info(f"Recommendations stored with ID: {rec_id}")
    except Exception as e:
        logger.warning(f"Could not store recommendations: {e}")

def _fallback_recommendations_response(analysis_id, analysis):
    """Construct fallback response identical to original error path."""
    try:
        # Compute normalised confidence percentage (0–100) for template safety
        raw_conf = 0
        try:
            if analysis and isinstance(analysis.get('classification'), dict):
                raw_conf = analysis.get('classification', {}).get('confidence', 0) or 0
        except Exception:
            raw_conf = 0
        try:
            conf_val = float(raw_conf)
        except Exception:
            conf_val = 0.0
        if conf_val <= 1.0:
            conf_pct = round(conf_val * 100.0, 1)
        else:
            conf_pct = round(conf_val, 1)
        conf_pct = max(0.0, min(100.0, conf_pct))

        basic_data = {
            'analysis': {
                'filename': (analysis or {}).get('filename', 'Unknown') if analysis else 'Unknown',
                'classification': (analysis or {}).get('classification', {}).get('classification', 'Unknown') if analysis else 'Unknown',
                'analysis_id': analysis_id,
                'confidence_pct': conf_pct,
            },
            'recommendations': [
                {
                    'title': 'Policy Review Required',
                    'description': 'Conduct comprehensive review of AI policy to ensure alignment with current best practices.',
                    'priority': 'high',
                    'source': 'Fallback System',
                    'timeframe': '3-6 months',
                    'implementation_steps': [
                        'Review current policy framework',
                        'Consult with stakeholders',
                        'Implement evidence-based improvements'
                    ]
                }
            ],
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'methodology': 'Basic Template (Fallback)',
            'total_recommendations': 1,
            'error_note': 'Advanced analysis temporarily unavailable'
        }
        flash('Using basic recommendations due to processing error.', 'warning')
        return render_template('recommendations.html', data=basic_data)
    except Exception as fallback_error:
        logger.error(f"Fallback recommendation generation failed: {str(fallback_error)}")
        flash('Error generating recommendations. Please try again.', 'error')
        return redirect(url_for('dashboard'))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

def validate_dependencies():
    """
    Comprehensive dependency validation before application startup.
    Validates all critical libraries and models required for full functionality.
    """
    import sys
    validation_results = []
    critical_failures = []
    warnings = []
    
    print("PolicyCraft Dependency Validation")
    print("=" * 50)
    
    # Core Python packages
    core_packages = [
        ('flask', 'Flask web framework'),
        ('pymongo', 'MongoDB driver'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('requests', 'HTTP client'),
        ('dotenv', 'Environment variables (python-dotenv)')
    ]
    
    for package, description in core_packages:
        try:
            __import__(package.replace('-', '_'))
            validation_results.append(f" {description}: {package}")
        except ImportError as e:
            critical_failures.append(f"ERROR: {description}: {package} - {str(e)}")
    
    # NLP and ML packages
    nlp_packages = [
        ('spacy', 'Natural Language Processing'),
        ('sklearn', 'Machine Learning (scikit-learn)'),
        ('nltk', 'Natural Language Toolkit'),
        ('sentence_transformers', 'Sentence embeddings'),
        ('contractions', 'Text preprocessing')
    ]
    
    for package, description in nlp_packages:
        try:
            __import__(package.replace('-', '_'))
            validation_results.append(f" {description}: {package}")
        except ImportError as e:
            critical_failures.append(f"ERROR: {description}: {package} - {str(e)}")
    
    # Document processing packages
    doc_packages = [
        ('pypdf', 'PDF processing'),
        ('docx', 'Word document processing (python-docx)'),
        ('fitz', 'Advanced PDF processing (PyMuPDF)'),
        ('pdfplumber', 'PDF text extraction')
    ]
    
    for package, description in doc_packages:
        try:
            __import__(package)
            validation_results.append(f" {description}: {package}")
        except ImportError as e:
            warnings.append(f"WARNING:  {description}: {package} - {str(e)}")
    
    # Visualization packages
    viz_packages = [
        ('plotly', 'Interactive visualisations'),
        ('kaleido', 'Static image export'),
        ('reportlab', 'PDF generation'),
        ('xlsxwriter', 'Excel export')
    ]
    
    for package, description in viz_packages:
        try:
            __import__(package)
            validation_results.append(f" {description}: {package}")
        except ImportError as e:
            warnings.append(f"WARNING:  {description}: {package} - {str(e)}")
    
    # Critical NLP models and data
    print("\n🧠 NLP Models and Data Validation")
    print("-" * 30)
    
    # spaCy model validation
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        validation_results.append(" spaCy English model: en_core_web_sm")
        print(" spaCy en_core_web_sm model loaded successfully")
    except Exception as e:
        critical_failures.append(f"ERROR: spaCy English model: en_core_web_sm - {str(e)}")
        print(f"ERROR: spaCy model error: {str(e)}")
    
    # SentenceTransformer model validation
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        validation_results.append(" SentenceTransformer model: all-MiniLM-L6-v2")
        print(" SentenceTransformer all-MiniLM-L6-v2 model loaded successfully")
    except Exception as e:
        critical_failures.append(f"ERROR: SentenceTransformer model: all-MiniLM-L6-v2 - {str(e)}")
        print(f"ERROR: SentenceTransformer error: {str(e)}")
    
    # NLTK data validation
    try:
        import nltk
        nltk_resources = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        for resource in nltk_resources:
            try:
                nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else 
                              f'corpora/{resource}' if resource in ['stopwords', 'wordnet'] else 
                              f'taggers/{resource}')
                validation_results.append(f" NLTK resource: {resource}")
            except LookupError:
                warnings.append(f"WARNING:  NLTK resource missing: {resource}")
    except ImportError as e:
        warnings.append(f"WARNING:  NLTK validation failed: {str(e)}")
    
    # Recommendation Engine validation
    print("\n🎯 Recommendation Engine Validation")
    print("-" * 30)
    
    try:
        from src.recommendation.engine import RecommendationEngine
        from src.analysis_engine.engine import PolicyAnalysisEngine
        
        # Test knowledge base integration
        kb_path = 'docs/knowledge_base'
        if os.path.exists(kb_path):
            try:
                engine = RecommendationEngine(knowledge_base_path=kb_path)
                validation_results.append("RecommendationEngine: Initialized successfully")
                print("RecommendationEngine initialized with knowledge base")
            except Exception as e:
                if "knowledge base is not available" in str(e):
                    warnings.append("RecommendationEngine: Knowledge base empty (will be populated on document upload)")
                    print("Knowledge base empty - recommendations available after document upload")
                else:
                    critical_failures.append(f"RecommendationEngine error: {str(e)}")
        else:
            warnings.append("Knowledge base directory missing (will be created on first use)")
            print("Knowledge base directory will be created on first use")
        
        # Test advanced analysis engine
        try:
            analysis_engine = PolicyAnalysisEngine()
            validation_results.append("Advanced PolicyAnalysisEngine: Available")
            print("Advanced analysis engine loaded successfully")
        except Exception as e:
            warnings.append(f"Advanced analysis engine: {str(e)}")
            print(f"Advanced analysis engine error: {str(e)}")
            
    except ImportError as e:
        critical_failures.append(f"Recommendation engine components: {str(e)}")
        print(f"Recommendation engine import error: {str(e)}")

    # Environment variables validation
    print("\nEnvironment Configuration")
    print("-" * 30)
    
    env_vars = [
        ('FEATURE_ADVANCED_ENGINE', 'Advanced analysis engine'),
        ('MONGODB_URI', 'MongoDB connection (optional)'),
        ('SECRET_KEY', 'Flask secret key (optional)')
    ]
    
    for var, description in env_vars:
        value = os.environ.get(var)
        if value:
            validation_results.append(f"{description}: {var} = {value}")
            print(f"{description}: {var} = {value}")
        else:
            warnings.append(f"{description}: {var} not set")
            print(f"{description}: {var} not set")
    
    # Summary
    print("\nValidation Summary")
    print("=" * 50)
    print(f"Successful validations: {len(validation_results)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Critical failures: {len(critical_failures)}")
    
    if critical_failures:
        print("\nCRITICAL FAILURES:")
        for failure in critical_failures:
            print(f"   {failure}")
        print("\nTo fix critical failures:")
        print("   pip install -r requirements.txt")
        print("   python -m spacy download en_core_web_sm")
        print("\nApplication startup ABORTED due to missing critical dependencies.")
        sys.exit(1)
    
    if warnings:
        print("\nWARNINGS (non-critical):")
        for warning in warnings:
            print(f"   {warning}")
        print("\nApplication will start with reduced functionality.")
    
    print("\nAll critical dependencies validated. Starting application...")
    print("=" * 50)

# Import configuration
from config import get_config, create_secure_directories

# Import analysis modules
# Constants for duplicated literals
DOCX_EXTENSION = '.docx'
TIMEZONE_SUFFIX = '+00:00'
BASELINE_PREFIX = '[BASELINE]'
ANALYSIS_NOT_FOUND = 'Analysis not found'
NO_RECOMMENDATIONS_FOUND = 'No recommendations found for this analysis'
# Newly extracted string constants (SonarCloud code smells)
THEME_AI_ETHICS = 'AI Ethics'
SOURCE_BASELINE_CREATION = 'Baseline Creation'
SOURCE_BASELINE_DEFAULT = 'Baseline Creation (Default)'
# Template constants to avoid duplicated literals
ABOUT_TEMPLATE = 'about.html'
PUBLIC_ABOUT_TEMPLATE = 'public/about.html'

from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.database.mongo_operations import MongoOperations as DatabaseOperations
from src.recommendation.engine import RecommendationEngine
from src.export.export_engine import ExportEngine
from src.auth.routes import auth_bp
from src.admin.routes import admin_bp
from src.database.models import db, User
from src.literature.literature_engine import LiteratureEngine
from src.literature.knowledge_manager import KnowledgeBaseManager as KnowledgeManager
from src.utils.auto_document_manager import AutoDocumentManager
from src.visualisation.charts import ChartGenerator
from src.scripts.clean_dataset import process_new_upload


def clean_baseline_filename(filename):
    """Remove BASELINE prefix and clean filename for display"""
    if filename.startswith(BASELINE_PREFIX + " "):
        clean_name = filename.replace(BASELINE_PREFIX + " ", "")
        if clean_name.endswith(".pdf"):
            clean_name = clean_name.replace(".pdf", "")
        return clean_name
    return filename

def clean_university_name(filename):
    """
    Clean filename to display only the university name without technical prefixes.
    
    This function removes timestamp prefixes and file extensions to present
    a clean, user-friendly university name for display purposes.
    """
    # Remove timestamp prefixes
    if '_' in filename:
        clean_name = filename.split('_', 2)[-1] if len(filename.split('_')) > 2 else filename.split('_')[-1]
    else:
        clean_name = filename

    # Remove file extensions and common suffixes
    clean_name = (
        clean_name
        .replace('.pdf', '')
        .replace(DOCX_EXTENSION, '')
        .replace('.doc', '')
        .replace('.txt', '')
        .replace('-ai-policy', '')
        .replace('_ai_policy', '')
    )

    name_lower = clean_name.lower()

    # Special composite case first
    if 'leeds' in name_lower and 'trinity' in name_lower:
        return 'Leeds Trinity University'

    # Keyword mapping to canonical names
    keyword_map = [
        ('harvard', 'Harvard University'),
        ('stanford', 'Stanford University'),
        ('mit', 'MIT'),
        ('cambridge', 'University of Cambridge'),
        ('oxford', 'Oxford University'),
        ('belfast', 'Belfast University'),
        ('edinburgh', 'Edinburgh University'),
        ('columbia', 'Columbia University'),
        ('cornell', 'Cornell University'),
        ('chicago', 'University of Chicago'),
        ('imperial', 'Imperial College London'),
        ('tokyo', 'University of Tokyo'),
        ('jagiellonian', 'Jagiellonian University'),
        ('liverpool', 'University of Liverpool'),
    ]

    for keyword, canonical in keyword_map:
        if keyword in name_lower:
            return canonical

    # Generic cleanup fallback
    clean_name = clean_name.replace('-', ' ').replace('_', ' ').title()
    return clean_name[:30] + '...' if len(clean_name) > 30 else clean_name

def clean_filename(filename):
    """
    Clean filename to show document name without timestamp and user ID prefixes.
    
    Removes technical prefixes added during upload process to present
    clean filenames for user interface display.
    """
    if '_' in filename:
        parts = filename.split('_')
        if len(parts) >= 3:
            clean_name = '_'.join(parts[2:])
        else:
            clean_name = filename
    else:
        clean_name = filename
    return clean_name

def format_british_date(date_str):
    """
    Format date string to British DD/MM/YYYY style.
    
    Converts various date formats to the standardised British format
    for consistent presentation throughout the application interface.
    """
    try:
        from datetime import datetime
        if isinstance(date_str, str):
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', TIMEZONE_SUFFIX))
            else:
                dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        else:
            dt = date_str
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return str(date_str)[:10] if len(str(date_str)) > 10 else str(date_str)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Application factory function for PolicyCraft Flask application.
    
    Initializes and configures the Flask application with all necessary
    extensions, blueprints, and database connections.
    
    Resources are initialised eagerly during startup.
    """
    # CRITICAL: Validate all dependencies before creating app (production)
    validate_dependencies()
    
    # Create secure directories first
    create_secure_directories()
    
    # Initialise Flask application
    app = Flask(__name__, 
               template_folder='src/web/templates',
               static_folder='src/web/static')
    # Avoid 308 redirects in tests for trailing slash differences
    app.url_map.strict_slashes = False
    
    # Load configuration (explicit env to satisfy linter and keep behaviour)
    config_env = os.environ.get('FLASK_ENV', 'development')
    config_obj = get_config(config_env)
    app.config.from_object(config_obj)
    
    # Initialise extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login session management."""
        return User.query.get(int(user_id))
    
    # Register blueprints (eager)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # CSRF protection and csrf_token for templates (available for all app instances)
    if app.config.get('WTF_CSRF_ENABLED', False):
        CSRFProtect(app)
        logger.info("CSRF protection enabled")
    else:
        logger.info("CSRF protection disabled")
    
    # Ensure csrf_token available globally in Jinja
    from flask_wtf.csrf import generate_csrf
    app.jinja_env.globals['csrf_token'] = generate_csrf
    @app.context_processor
    def inject_csrf_token():
        """Provide csrf_token() callable to Jinja templates even when CSRF is disabled (testing)."""
        return {'csrf_token': (lambda: generate_csrf())}

    # Make current_user available in all templates
    @app.context_processor
    def inject_current_user():
        """Make current_user available in all templates."""
        return {'current_user': current_user}
    
    # Define core routes on this app instance so tests using a fresh app have them
    @app.route('/')
    def index():
        """
        Landing page route for PolicyCraft application.
        """
        logger.info("Landing page accessed")
        return render_template("index.html")

    @app.route('/about')
    def about():
        """Minimal about page used by tests/templates."""
        # Prefer the public/about.html if present, fallback to about.html, then plain text
        public_about = os.path.join(app.template_folder, *PUBLIC_ABOUT_TEMPLATE.split('/'))
        root_about = os.path.join(app.template_folder, ABOUT_TEMPLATE)
        if os.path.exists(public_about):
            return render_template(PUBLIC_ABOUT_TEMPLATE)
        if os.path.exists(root_about):
            return render_template(ABOUT_TEMPLATE)
        return "About PolicyCraft", 200, {"Content-Type": "text/plain; charset=utf-8"}

    # Initialize database tables eagerly at startup (Flask 3 removed before_first_request)
    with app.app_context():
        from src.database.models import init_db
        init_db(app)  # Initialise database tables with app context
    
    return app

# Create Flask app and initialize modules
app = create_app()

 
# Lazy initialisation wrappers to avoid heavy startup costs
class _LazyObject:
    """Defers creation of the underlying object until first attribute access."""
    def __init__(self, factory, name: str):
        self._factory = factory
        self._obj = None
        self._name = name

    def _get(self):
        if self._obj is None:
            import time as _time
            start = _time.time()
            self._obj = self._factory()
            logger.info(f"Initialised {self._name} in {_time.time()-start:.3f}s")
        return self._obj

    def __getattr__(self, item):
        return getattr(self._get(), item)

# Lazy instances replacing eager globals
knowledge_base_path = "docs/knowledge_base"  # Use same path as LiteratureEngine
text_processor = _LazyObject(lambda: TextProcessor(), "TextProcessor")
theme_extractor = _LazyObject(lambda: ThemeExtractor(), "ThemeExtractor")
policy_classifier = _LazyObject(lambda: PolicyClassifier(), "PolicyClassifier")
db_operations = _LazyObject(lambda: DatabaseOperations(uri="mongodb://localhost:27017", db_name="policycraft"), "DatabaseOperations")
chart_generator = _LazyObject(lambda: ChartGenerator(), "ChartGenerator")
recommendation_engine = _LazyObject(lambda: RecommendationEngine(knowledge_base_path=knowledge_base_path), "RecommendationEngine")


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Validates file type against configured allowed extensions
    to ensure only supported document formats are processed.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_upload_folder():
    """
    Create upload folder if it doesn't exist.
    
    Ensures the designated upload directory exists for storing
    user-uploaded policy documents.
    """
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"Created upload folder: {upload_folder}")

# Main application routes

def _to_epoch(val):
    """Convert supported date formats to POSIX timestamp for consistent sorting."""
    try:
        if isinstance(val, datetime):
            return val.replace(tzinfo=None).timestamp()
        if isinstance(val, str):
            dt = datetime.fromisoformat(val.replace('Z', TIMEZONE_SUFFIX))
            return dt.replace(tzinfo=None).timestamp()
    except Exception:
        pass
    return 0

def _get_uploaded_files_from_request(req):
    """Extract list of uploaded files from Flask request supporting multiple field names."""
    files = []
    try:
        # Common patterns: 'file' single/multiple, or 'files[]'
        if 'files[]' in req.files:
            files = req.files.getlist('files[]')
        elif 'file' in req.files:
            files = req.files.getlist('file')
    except Exception as e:
        logger.error(f"Upload error: could not read files from request: {e}")
        files = []
    # Filter out empty filenames
    return [f for f in files if getattr(f, 'filename', '')]

def _process_uploaded_files(uploaded_files):
    """Validate and save uploaded files. Returns (successful_uploads, failed_uploads)."""
    create_upload_folder()
    successful = []
    failed = []
    for f in uploaded_files:
        original_name = f.filename
        if not original_name:
            failed.append({'filename': original_name or 'unknown', 'reason': 'Empty filename'})
            continue
        if not allowed_file(original_name):
            failed.append({'filename': original_name, 'reason': 'Disallowed file type'})
            continue
        try:
            safe_name = secure_filename(original_name)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            unique_name = f"{current_user.id}_{timestamp}_{safe_name}"
            dest_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            f.save(dest_path)
            logger.info(f"Saved uploaded file: {dest_path}")
            successful.append({'original': original_name, 'unique': unique_name})
        except Exception as e:
            logger.error(f"Failed to save uploaded file {original_name}: {e}")
            failed.append({'filename': original_name, 'reason': 'Save failed'})
    return successful, failed

def _parse_batch_file_list(files_param: str):
    """Parse comma-separated file list from URL path parameter."""
    if not files_param:
        return []
    return [p for p in files_param.split(',') if p]

def _authorize_batch_files(file_list):
    """Ensure all files belong to current user."""
    prefix = f"{current_user.id}_"
    return all(name.startswith(prefix) for name in file_list)

def _process_single_batch_file(filename: str):
    """Process a single uploaded user file; returns (result_dict, ok_bool)."""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            logger.error(f"Batch: file not found: {file_path}")
            return {'filename': filename, 'error': 'File not found'}, False

        # Robust extraction path (mirrors single-analysis behaviour)
        uni_guess = filename.split('-')[0].replace('university', '').strip().title() or 'User Institution'
        try:
            extracted_text = _extract_text_with_fallback(file_path, uni_guess)
            cleaned_text = _clean_text_safe(extracted_text, filename)
            themes = _extract_themes_safe(cleaned_text, filename)
            classification = _classify_policy_safe(cleaned_text, filename)
        except Exception as e:
            logger.error(f"Batch: robust extraction failed for {filename}: {e}")
            extracted_text = (
                f"AI Policy document from {uni_guess}. This is a placeholder text as the original document "
                f"could not be processed due to: {e}"
            )
            cleaned_text = extracted_text
            themes = [
                {"name": "Policy", "score": 0.8, "confidence": 75},
                {"name": THEME_AI_ETHICS, "score": 0.7, "confidence": 70},
            ]
            classification = {
                "classification": "Moderate",
                "confidence": 75,
                "source": SOURCE_BASELINE_DEFAULT,
            }

        analysis_id = _store_analysis_results(filename, extracted_text, cleaned_text, themes, classification)
        charts, text_stats, theme_summary, classification_details = _generate_analysis_derivatives(cleaned_text, themes, classification)
        result_payload = _build_results_payload(filename, analysis_id, themes, classification, charts,
                                                text_stats, theme_summary, classification_details,
                                                extracted_text, cleaned_text)
        # Add minimal flags for batch UI
        result_payload['ok'] = True
        return result_payload, True
    except Exception as e:
        logger.error(f"Batch: error processing {filename}: {e}")
        return {'filename': filename, 'error': str(e)}, False

def _summarize_batch_results(file_list, successful_analyses, failed_analyses):
    """Create a summary dict for batch analysis template."""
    total = len(file_list)
    return {
        'total_files': total,
        'successful': successful_analyses,
        'failed': failed_analyses,
        'success_rate': round((successful_analyses / total) * 100, 2) if total else 0.0
    }

def _process_batch_files(file_list):
    """Process the list of files in batch mode and return (results, ok_count, fail_count)."""
    batch_results = []
    successful_analyses = 0
    failed_analyses = 0

    for filename in file_list:
        result, ok = _process_single_batch_file(filename)
        batch_results.append(result)
        if ok:
            successful_analyses += 1
        else:
            failed_analyses += 1

    return batch_results, successful_analyses, failed_analyses

def _combine_stats(stats1, stats2):
    """Combine two sets of statistics with weighted averaging."""
    total1 = stats1.get('total', 0)
    total2 = stats2.get('total', 0)
    total = total1 + total2
    
    if total == 0:
        return {
            'total': 0,
            'avg_confidence': 0,
            'avg_themes_per_analysis': 0
        }
    
    # Calculate weighted average for confidence and themes
    conf1 = (stats1.get('avg_confidence', 0) or 0) * total1
    conf2 = (stats2.get('avg_confidence', 0) or 0) * total2
    
    themes1 = (stats1.get('avg_themes_per_analysis', 0) or 0) * total1
    themes2 = (stats2.get('avg_themes_per_analysis', 0) or 0) * total2
    
    return {
        'total': total,
        'avg_confidence': round((conf1 + conf2) / total, 1) if total > 0 else 0,
        'avg_themes_per_analysis': round((themes1 + themes2) / total, 1) if total > 0 else 0
    }

def _extract_text_with_fallback(file_path: str, university_name: str) -> str:
    """Extract text with size checks and fallbacks for PDF/DOCX. Returns non-empty text (may be placeholder)."""
    try:
        if not os.path.exists(file_path):
            logger.error(f"Dashboard: File does not exist: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.warning(f"Dashboard: Empty file detected: {file_path} (0 bytes)")
            raise ValueError(f"Empty file: {file_path}")

        logger.info(f"Dashboard: Attempting to extract text from {file_path} ({file_size} bytes)")
        extracted_text = text_processor.extract_text_from_file(file_path)
        text_length = len(extracted_text) if extracted_text else 0
        logger.info(f"Dashboard: Extracted {text_length} characters from {file_path}")

        if not extracted_text or text_length < 50:
            logger.warning(f"Dashboard: Insufficient text extracted from {file_path} ({text_length} chars), attempting fallback extraction")
            lower = file_path.lower()
            if lower.endswith('.pdf'):
                extracted_text = _fallback_extract_pdf(file_path, extracted_text)
            else:
                extracted_text = _fallback_extract_docx(file_path, extracted_text)

        return _ensure_minimal_text(extracted_text, file_path, university_name)
    except Exception as e:
        logger.error(f"Dashboard: Text extraction failed for {file_path}: {e}")
        return (
            f"AI Policy document from {university_name}. This is a placeholder text as the original document "
            f"could not be processed due to: {e}"
        )

def _fallback_extract_pdf(file_path: str, current_text: str) -> str:
    """Fallback extraction for PDF using pdfplumber (without hard global dependencies)."""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            fb_text = "".join((page.extract_text() or "") + "\n" for page in pdf.pages)
        if fb_text and len(fb_text) > (len(current_text) if current_text else 0):
            logger.info(f"Dashboard: Fallback PDF extraction successful, got {len(fb_text)} characters")
            return fb_text
    except Exception as e:
        logger.warning(f"Dashboard: PDF fallback extraction failed: {e}")
    return current_text

def _fallback_extract_docx(file_path: str, current_text: str) -> str:
    """Fallback extraction for DOCX/DOC using python-docx (Document)."""
    lower = file_path.lower()
    doc_exts = (DOCX_EXTENSION, '.doc') if 'DOCX_EXTENSION' in globals() else ('.docx', '.doc')
    if not lower.endswith(doc_exts):
        return current_text
    try:
        from docx import Document
        doc = Document(file_path)
        fb_text = "\n".join([para.text for para in doc.paragraphs if para.text])
        if fb_text and len(fb_text) > (len(current_text) if current_text else 0):
            logger.info(f"Dashboard: Fallback DOCX extraction successful, got {len(fb_text)} characters")
            return fb_text
    except Exception as e:
        logger.warning(f"Dashboard: DOCX fallback extraction failed: {e}")
    return current_text

def _ensure_minimal_text(extracted_text: str, file_path: str, university_name: str) -> str:
    """Ensure minimal placeholder text if extraction fails or is too short."""
    if not extracted_text or len(extracted_text) < 20:
        logger.warning(f"Dashboard: Using minimal placeholder text for {file_path}")
        return (
            f"AI Policy document from {university_name}. This is a placeholder text as the original document "
            f"could not be fully processed."
        )
    return extracted_text

def _clean_text_safe(extracted_text: str, missing_file: str) -> str:
    """Clean text with fallback to original on error."""
    try:
        cleaned = text_processor.clean_text(extracted_text)
        logger.info(f"Dashboard: Cleaned text for {missing_file}, now {len(cleaned)} characters")
        return cleaned
    except Exception as e:
        logger.error(f"Dashboard: Text cleaning failed for {missing_file}: {e}")
        logger.info("Dashboard: Using original text as fallback after cleaning failure")
        return extracted_text

def _extract_themes_safe(cleaned_text: str, missing_file: str):
    """Extract themes with sensible defaults on error/empty result."""
    try:
        themes = theme_extractor.extract_themes(cleaned_text)
        logger.info(f"Dashboard: Extracted {len(themes) if themes else 0} themes from {missing_file}")
        if not themes:
            raise ValueError("No themes extracted")
        return themes
    except Exception as e:
        logger.error(f"Dashboard: Theme extraction failed for {missing_file}: {e}")
        return [
            {"name": "Policy", "score": 0.8, "confidence": 75},
            {"name": THEME_AI_ETHICS, "score": 0.7, "confidence": 70},
            {"name": "Guidelines", "score": 0.6, "confidence": 65}
        ]

def _classify_policy_safe(cleaned_text: str, missing_file: str) -> dict:
    """Classify text and normalize to dict; fall back to defaults on error."""
    try:
        classification = policy_classifier.classify_policy(cleaned_text)
        if isinstance(classification, str):
            return {
                "classification": _standardize_classification(classification),
                "confidence": 80,
                "source": SOURCE_BASELINE_CREATION
            }
        if isinstance(classification, dict) and 'classification' in classification:
            cls = _standardize_classification(classification.get('classification', 'Moderate'))
            classification['classification'] = cls
            classification.setdefault('source', SOURCE_BASELINE_CREATION)
            classification.setdefault('confidence', 80)
            return classification
        logger.warning(f"Dashboard: Unexpected classification format for {missing_file}: {classification}")
    except Exception as e:
        logger.error(f"Dashboard: Classification failed for {missing_file}: {e}")
    return {
        "classification": "Moderate",
        "confidence": 75,
        "source": SOURCE_BASELINE_DEFAULT
    }

def _ensure_defaults_for_storage(extracted_text: str, cleaned_text: str, themes, classification: dict, university_name: str):
    """Ensure default values for storing the baseline analysis (without changing behaviour)."""
    if not extracted_text:
        extracted_text = f"AI Policy document from {university_name}. This is a placeholder text."
    if not cleaned_text:
        cleaned_text = extracted_text
    if not themes:
        themes = [{"name": "Policy", "score": 0.8, "confidence": 75}]
    if not classification or not isinstance(classification, dict):
        classification = {
            "classification": "Moderate",
            "confidence": 75,
            "source": SOURCE_BASELINE_DEFAULT
        }
    return extracted_text, cleaned_text, themes, classification

def _prepare_storage_metadata(missing_file: str, extracted_text: str) -> dict:
    """Build storage metadata consistent with the existing format."""
    return {
        "source_file": missing_file,
        "extraction_method": "dashboard_baseline_creation",
        "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text_length": len(extracted_text) if extracted_text else 0,
        "is_baseline": True
    }

def _build_placeholder_analysis(missing_file: str,
                                baseline_filename: str,
                                university_name: str,
                                classification: dict,
                                themes,
                                extracted_text: str,
                                cleaned_text: str,
                                store_error: Exception) -> dict:
    """Build an analysis placeholder in case of a storage error, consistent with the current format."""
    return {
        '_id': f"placeholder_{missing_file.replace('.', '_')}",
        'filename': baseline_filename,
        'document_id': missing_file,
        'title': f"Policy from {university_name}",
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_id': -1,
        'is_user_analysis': False,
        'is_baseline': True,
        'classification': classification,
        'score': 50,
        'themes': themes,
        'summary': f"This is a placeholder for {missing_file}. Storage error: {store_error}",
        'text_data': {
            'original_text': (extracted_text or '')[:1000] if extracted_text else "No text extracted",
            'cleaned_text': (cleaned_text or '')[:1000] if cleaned_text else "No cleaned text",
            'text_length': len(extracted_text) if extracted_text else 0
        }
    }

def _store_baseline_or_placeholder(analyses_by_filename: dict,
                                   missing_file: str,
                                   baseline_filename: str,
                                   extracted_text: str,
                                   cleaned_text: str,
                                   themes,
                                   classification: dict,
                                   university_name: str) -> None:
    """Store baseline analysis or create a placeholder on failure; updates analyses_by_filename in-place."""
    try:
        extracted_text, cleaned_text, themes, classification = _ensure_defaults_for_storage(
            extracted_text, cleaned_text, themes, classification, university_name
        )

        metadata = _prepare_storage_metadata(missing_file, extracted_text)

        logger.info(f"Dashboard: Storing baseline analysis for {missing_file} with {len(extracted_text)} chars of text")
        analysis_id = db_operations.store_user_analysis_results(
            user_id=-1,
            filename=baseline_filename,
            original_text=extracted_text,
            cleaned_text=cleaned_text,
            themes=themes,
            classification=classification,
            document_id=missing_file
        )

        logger.info(f"Dashboard: Successfully stored baseline analysis with ID {analysis_id}")
        new_analysis = db_operations.get_analysis_by_id(analysis_id)
        if new_analysis:
            new_analysis['is_baseline'] = True
            new_analysis['is_user_analysis'] = False
            analyses_by_filename[missing_file] = new_analysis
            logger.info(f"Dashboard: Added proper baseline analysis for {missing_file} with ID {analysis_id}")
            return
        else:
            logger.error(f"Dashboard: Failed to retrieve newly created analysis for {missing_file}")
            raise RuntimeError("retrieve_failed")

    except (ValueError, KeyError, RuntimeError, OSError) as store_error:
        logger.error(f"Dashboard: Error storing baseline analysis: {store_error}")
        placeholder_analysis = _build_placeholder_analysis(
            missing_file,
            baseline_filename,
            university_name,
            classification,
            themes,
            extracted_text,
            cleaned_text,
            store_error
        )
        analyses_by_filename[missing_file] = placeholder_analysis
        logger.info(f"Dashboard: Added placeholder analysis for {missing_file} due to storage error")
def _create_missing_baselines(clean_dataset_dir, missing_files, analyses_by_filename):
    """Create baseline analyses for missing files using safe helpers."""
    for missing_file in missing_files:
        # Skip auxiliary/helper files
        if 'guidance' in missing_file.lower() or missing_file == 'dataset_info.md':
            continue

        file_path = os.path.join(clean_dataset_dir, missing_file)
        if not os.path.exists(file_path):
            logger.error(f"Dashboard: Missing file not found: {file_path}")
            continue

        university_name = missing_file.split('-')[0].replace('university', '').strip().title()
        if not university_name:
            university_name = missing_file.split('.')[0].replace('university', '').strip().title()

        baseline_filename = f"{BASELINE_PREFIX} {university_name}"
        logger.info(f"Dashboard: Creating baseline analysis for {missing_file} as '{baseline_filename}'")

        try:
            extracted_text = _extract_text_with_fallback(file_path, university_name)
            cleaned_text = _clean_text_safe(extracted_text, missing_file)
            themes = _extract_themes_safe(cleaned_text, missing_file)
            classification = _classify_policy_safe(cleaned_text, missing_file)

            _store_baseline_or_placeholder(
                analyses_by_filename,
                missing_file,
                baseline_filename,
                extracted_text,
                cleaned_text,
                themes,
                classification,
                university_name
            )
        except Exception as e:
            logger.error(f"Dashboard: Error creating baseline analysis for {missing_file}: {str(e)}")
            if missing_file not in analyses_by_filename:
                placeholder_analysis = {
                    '_id': f"placeholder_{missing_file.replace('.', '_')}",
                    'filename': baseline_filename or f"{BASELINE_PREFIX} {missing_file}",
                    'document_id': missing_file,
                    'title': f"Policy from {university_name or missing_file.split('-')[0].title()}",
                    'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'user_id': -1,
                    'is_user_analysis': False,
                    'is_baseline': True,
                    'is_placeholder': True,
                    'classification': {
                        "classification": "Moderate",
                        "confidence": 75,
                        "source": "Placeholder"
                    },
                    'score': 50,
                    'themes': [{"name": "Policy", "score": 0.8, "confidence": 75}],
                    'summary': f"This is a placeholder for {missing_file}. The original file could not be processed.",
                    'text_data': {
                        'original_text': f"Placeholder for {missing_file}",
                        'cleaned_text': f"Placeholder for {missing_file}",
                        'text_length': 0
                    }
                }
                analyses_by_filename[missing_file] = placeholder_analysis
                logger.info(f"Dashboard: Added placeholder analysis for {missing_file} due to general error")
def _normalize_classification_field(processed_analysis: dict) -> None:
    """Ensure classification is present, standardized, and valid; logs unexpected types."""
    if 'classification' not in processed_analysis:
        processed_analysis['classification'] = 'Moderate'
        return

    cls_field = processed_analysis['classification']
    if isinstance(cls_field, dict):
        cls = cls_field.get('classification', 'Moderate')
        processed_analysis['classification']['classification'] = _standardize_classification(cls)
    elif isinstance(cls_field, str):
        processed_analysis['classification'] = _standardize_classification(cls_field)
    else:
        processed_analysis['classification'] = 'Moderate'
        logger.error(f"Dashboard error: Unexpected classification type: {type(cls_field)}")


def _ensure_required_defaults(processed_analysis: dict) -> None:
    """Ensure presence of title, summary, themes, and score fields with sensible defaults."""
    if 'title' not in processed_analysis:
        processed_analysis['title'] = processed_analysis.get('filename', 'Untitled Policy')
    if 'summary' not in processed_analysis:
        processed_analysis['summary'] = 'No summary available'
    if 'themes' not in processed_analysis:
        processed_analysis['themes'] = []
    if 'score' not in processed_analysis:
        processed_analysis['score'] = 50


def _format_analysis_date_inplace(processed_analysis: dict) -> None:
    """Format analysis_date to '%Y-%m-%d %H:%M:%S' string while being tolerant of types."""
    if 'analysis_date' not in processed_analysis:
        processed_analysis['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return

    date_val = processed_analysis['analysis_date']
    if hasattr(date_val, 'strftime'):
        processed_analysis['analysis_date'] = date_val.strftime('%Y-%m-%d %H:%M:%S')
        return
    if isinstance(date_val, str):
        try:
            dt = datetime.fromisoformat(date_val.replace('Z', TIMEZONE_SUFFIX))
            processed_analysis['analysis_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            # Keep original string if parsing fails
            pass


def _process_analyses_for_display(analyses):
    """Process analyses for display by converting dates and preparing data."""
    processed = []
    for analysis in analyses:
        if not isinstance(analysis, dict):
            logger.error(f"Dashboard error: Skipping non-dict analysis: {type(analysis)}")
            continue

        processed_analysis = analysis.copy()
        _normalize_classification_field(processed_analysis)
        _ensure_required_defaults(processed_analysis)
        _format_analysis_date_inplace(processed_analysis)
        processed.append(processed_analysis)
    return processed

def _standardize_classification(classification):
    """
    Standardize classification to use only Restrictive, Moderate, or Permissive.
    Maps legacy categories to standard ones.
    """
    # Map of legacy categories to standard categories
    category_map = {
        # Standard categories (keep as is)
        'Restrictive': 'Restrictive',
        'Moderate': 'Moderate',
        'Permissive': 'Permissive',
        
        # Legacy categories (map to standard)
        'Educational': 'Moderate',
        'Research-focused': 'Permissive',
        'Comprehensive': 'Moderate',
        'Balanced': 'Moderate',  # Just in case
        
        # Default for unknown
        'Unknown': 'Moderate'
    }
    
    # Return standardized classification or default to Moderate if not in map
    return category_map.get(classification, 'Moderate')

def _increment_classification_counts(classification_counts: dict, classification_value) -> None:
    """Normalise and increment classification count. Logs unexpected types."""
    if isinstance(classification_value, dict):
        cls = classification_value.get('classification', 'Moderate')
    elif isinstance(classification_value, str):
        cls = classification_value
    else:
        cls = 'Moderate'
        logger.error(f"Analytics error: Unexpected classification type: {type(classification_value)}")
    standardized_cls = _standardize_classification(cls)
    classification_counts[standardized_cls] = classification_counts.get(standardized_cls, 0) + 1


def _accumulate_theme_frequencies(theme_frequencies: dict, themes_value) -> None:
    """Accumulate per-theme frequencies from a possibly invalid themes payload."""
    themes_list = themes_value if isinstance(themes_value, list) else []
    for theme in themes_list:
        if isinstance(theme, dict):
            theme_name = theme.get('name', 'Unknown')
        else:
            theme_name = str(theme)
        theme_frequencies[theme_name] = theme_frequencies.get(theme_name, 0) + 1


def _ensure_all_standard_classes(counts: dict) -> None:
    for cls in ['Restrictive', 'Moderate', 'Permissive']:
        counts.setdefault(cls, 0)


def _calculate_analytics(analyses):
    """Calculate analytics (classifications and themes) from analyses."""
    classification_counts = {}
    theme_frequencies = {}

    for analysis in analyses:
        if not isinstance(analysis, dict):
            logger.error(f"Analytics error: Skipping non-dict analysis: {type(analysis)}")
            continue

        _increment_classification_counts(classification_counts, analysis.get('classification', 'Moderate'))
        _accumulate_theme_frequencies(theme_frequencies, analysis.get('themes', []))

    _ensure_all_standard_classes(classification_counts)
    return classification_counts, theme_frequencies

def _get_minimal_dashboard_data(user):
    """Return minimal dashboard data for error cases."""
    return {
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name()
        },
        'total_policies': 0,
        'classification_counts': {},
        'theme_frequencies': {},
        'charts': {},
        'recent_analyses': [],
        'statistics': {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}
    }

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard with comprehensive analysis data for authenticated users.
    
    Provides overview of user's policy analyses, statistics, and charts
    with baseline policy comparisons and performance metrics.
    """
    try:
        logger.info(f"Dashboard accessed by user: {current_user.username}")

        user_analyses, baseline_analyses = _get_user_and_baseline_analyses(current_user.id)
        combined_analyses = _prepare_combined_analyses(user_analyses, baseline_analyses)

        _load_sample_policies_if_needed(user_analyses)

        dashboard_data = _prepare_dashboard_data(current_user, user_analyses, combined_analyses)
        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Dashboard loaded with limited data due to an error.', 'warning')
        return render_template('dashboard.html', data=_get_minimal_dashboard_data(current_user))

def _get_clean_dataset_dir():
    """Return absolute path to clean_dataset directory."""
    from pathlib import Path
    return Path(__file__).resolve().parent / 'data' / 'policies' / 'clean_dataset'

def _list_clean_dataset_files(clean_dataset_dir):
    """List valid policy files from clean_dataset directory."""
    logger.info(f"Dashboard: Using clean_dataset directory: {clean_dataset_dir}")
    files = []
    if os.path.exists(clean_dataset_dir):
        for filename in os.listdir(clean_dataset_dir):
            if filename.endswith(('.pdf', DOCX_EXTENSION)) and 'guidance' not in filename.lower():
                files.append(filename)
    logger.info(f"Dashboard: Found {len(files)} policy files in clean_dataset")
    return files

def _get_user_and_baseline_analyses(user_id: int):
    """Fetch and log user and baseline analyses after deduplication."""
    db_operations.deduplicate_baseline_analyses(user_id)
    user_analyses = db_operations.get_user_analyses(user_id)
    baseline_analyses = db_operations.get_user_analyses(-1)
    logger.info(f"Dashboard: Found {len(user_analyses)} user analyses and {len(baseline_analyses)} baseline analyses")
    return user_analyses, baseline_analyses

def _prepare_combined_analyses(user_analyses, baseline_analyses):
    """Prepare merged, baseline-complete, sorted analyses list with logs preserved."""
    clean_dataset_dir = _get_clean_dataset_dir()
    clean_dataset_files = _list_clean_dataset_files(clean_dataset_dir)

    analyses_by_filename = _merge_user_and_baseline_analyses(user_analyses, baseline_analyses)
    missing_files = _identify_missing_clean_files(clean_dataset_files, analyses_by_filename)
    logger.info(f"Dashboard: Missing files from clean_dataset: {missing_files}")
    _create_missing_baselines(clean_dataset_dir, missing_files, analyses_by_filename)

    combined_analyses = list(analyses_by_filename.values())
    logger.info(f"Dashboard: Combined into {len(combined_analyses)} total analyses")
    displayed_files = [analysis.get('filename', '') for analysis in combined_analyses]
    logger.info(f"Dashboard: Displaying analyses for: {sorted(displayed_files)}")
    combined_analyses.sort(key=lambda a: _to_epoch(a.get('analysis_date')), reverse=True)
    return combined_analyses

def _merge_user_and_baseline_analyses(user_analyses, baseline_analyses):
    """Merge analyses preferring user analyses over baseline ones."""
    analyses_by_filename = {}
    for analysis in user_analyses:
        filename = analysis.get('filename', '')
        if not filename:
            continue
        analyses_by_filename[filename] = analysis
        analysis['is_user_analysis'] = True
    for analysis in baseline_analyses:
        filename = analysis.get('filename', '')
        if not filename or filename in analyses_by_filename:
            continue
        analyses_by_filename[filename] = analysis
        analysis['is_user_analysis'] = False
    return analyses_by_filename

def _identify_missing_clean_files(clean_dataset_files, analyses_by_filename):
    """Return clean_dataset files that are not represented in analyses."""
    missing_files = []
    for clean_file in clean_dataset_files:
        found = False
        for filename in analyses_by_filename.keys():
            analysis = analyses_by_filename[filename]
            if clean_file == filename or (analysis.get('document_id') and clean_file == analysis.get('document_id')):
                found = True
                logger.info(f"Dashboard: Found match for {clean_file} in analysis {filename}")
                break
        if not found:
            missing_files.append(clean_file)
    return missing_files

def _load_sample_policies_if_needed(user_analyses):
    """Load sample policies if user has none."""
    if not any(a.get('filename','').startswith(BASELINE_PREFIX) for a in user_analyses):
        try:
            loaded = db_operations.load_sample_policies_for_user(current_user.id)
            if loaded:
                flash('Sample baseline policies have been loaded to your dashboard.', 'success')
        except Exception as e:
            logger.error(f"Failed to auto-load baseline policies: {e}")

def _prepare_dashboard_data(user, user_analyses, combined_analyses):
    """Prepare the complete dashboard data structure."""
    # Generate charts
    dashboard_charts = _safe_generate_dashboard_charts(user_analyses)

    # Log analyses before analytics calculation
    for i, analysis in enumerate(combined_analyses):
        logger.info(f"Dashboard debug: Analysis {i} type: {type(analysis)}")
        if isinstance(analysis, dict):
            cls = analysis.get('classification', 'Not found')
            logger.info(f"Dashboard debug: Analysis {i} classification type: {type(cls)}, value: {cls}")
        else:
            logger.error(f"Dashboard debug: Analysis {i} is not a dict: {type(analysis)}")

    # Calculate analytics
    classification_counts, theme_frequencies = _safe_calculate_analytics(combined_analyses)

    # Get combined statistics
    db_stats = _safe_get_combined_stats(user.id)

    # Prepare user data
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.get_full_name(),
        'institution': getattr(user, 'institution', None),
        'role': getattr(user, 'role', 'user')
    }
    
    # Process analyses for display
    processed_analyses = _safe_process_analyses_for_display(combined_analyses)
    
    dashboard_data = {
        'user': user_data,
        'total_policies': len(combined_analyses),
        'classification_counts': classification_counts,
        'theme_frequencies': theme_frequencies,
        'charts': dashboard_charts,
        'recent_analyses': processed_analyses,
        'statistics': db_stats
    }

    # Log dashboard data structure
    logger.info(f"Dashboard debug: Dashboard data keys: {list(dashboard_data.keys())}")
    
    return dashboard_data

def _safe_generate_dashboard_charts(user_analyses):
    """Generate charts with error handling and concise logging."""
    try:
        return chart_generator.generate_user_dashboard_charts(user_analyses)
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return {}

def _safe_calculate_analytics(combined_analyses):
    """Calculate analytics with fallbacks; log concise error."""
    try:
        classification_counts, theme_frequencies = _calculate_analytics(combined_analyses)
        logger.info(f"Dashboard debug: Classification counts: {classification_counts}")
        return classification_counts, theme_frequencies
    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        return {'Restrictive': 0, 'Moderate': 0, 'Permissive': 0}, {}

def _safe_get_combined_stats(user_id: int):
    """Fetch and combine DB stats with rounding; on error return zeros."""
    try:
        user_stats = db_operations.get_analysis_statistics(user_id)
        baseline_stats = db_operations.get_analysis_statistics(-1)
        combined_stats = _combine_stats(user_stats, baseline_stats)
        return {
            'total_analyses': combined_stats.get('total', 0),
            'avg_confidence': round(combined_stats.get('avg_confidence', 0), 1),
            'avg_themes_per_analysis': round(combined_stats.get('avg_themes_per_analysis', 0), 1)
        }
    except Exception as e:
        logger.error(f"DB stats error: {e}")
        return {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}

def _safe_process_analyses_for_display(combined_analyses):
    """Process analyses for display with error handling and debug logs."""
    try:
        processed = _process_analyses_for_display(combined_analyses)
        logger.info(f"Dashboard: Processed {len(processed)} analyses for display")
        for i, analysis in enumerate(processed[:3]):
            logger.info(f"Dashboard debug: Processed analysis {i} keys: {list(analysis.keys())}")
            if 'classification' in analysis:
                logger.info(f"Dashboard debug: Processed analysis {i} classification type: {type(analysis['classification'])}, value: {analysis['classification']}")
        return processed
    except Exception as e:
        logger.error(f"Processing analyses error: {e}")
        return []

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """
    File upload with multi-file support for policy documents.
    
    Handles both single and multiple file uploads, validates file types,
    and initiates the document processing pipeline.
    """
    if request.method == 'GET':
        logger.info(f"Upload page accessed by user: {current_user.username}")
        return render_template('upload.html')
    
    # Handle file uploads
    uploaded_files = _get_uploaded_files_from_request(request)
    max_files = app.config.get('MAX_FILES_PER_UPLOAD', 10)
    early = _validate_upload_request(uploaded_files, max_files)
    if early is not None:
        return early

    successful_uploads, failed_uploads = _process_uploaded_files(uploaded_files)
    
    # Provide feedback
    outcome = _handle_upload_outcome(successful_uploads, failed_uploads)
    if outcome is not None:
        return outcome
    return redirect(request.url)

def _validate_upload_request(uploaded_files, max_files):
    """Validate upload input. Returns a Response or None if OK."""
    if not uploaded_files:
        flash('No files selected', 'error')
        return redirect(request.url)
    if len(uploaded_files) > max_files:
        flash(f'Too many files. Maximum {max_files} files allowed.', 'error')
        return redirect(request.url)
    return None

def _handle_upload_outcome(successful_uploads, failed_uploads):
    """Build the appropriate redirect and flash messages after upload, or return None."""
    if successful_uploads:
        if len(successful_uploads) == 1:
            flash('File uploaded successfully! Starting analysis...', 'success')
            return redirect(url_for('analyse_document', filename=successful_uploads[0]['unique']))
        flash(f"{len(successful_uploads)} files uploaded successfully! Starting batch analysis...", 'success')
        file_list = [f['unique'] for f in successful_uploads]
        return redirect(url_for('batch_analyse', files=','.join(file_list)))
    if failed_uploads:
        error_msg = f"{len(failed_uploads)} files failed to upload: " + ", ".join([f['filename'] for f in failed_uploads])
        flash(error_msg, 'error')
        # no redirect here – let the caller decide (upload_file -> request.url)
    return None

@app.route('/batch-analyse/<path:files>')
@login_required
def batch_analyse(files):
    """
    Batch analysis for multiple uploaded files.
    
    Processes multiple documents simultaneously through the AI analysis
    pipeline and provides consolidated results and statistics.
    """
    try:
        file_list = _parse_batch_file_list(files)
        if not _authorize_batch_files(file_list):
            return _flash_and_redirect('upload_file', 'Access denied. You can only analyse your own documents.', 'error')

        logger.info(f"Starting batch analysis of {len(file_list)} files")

        batch_results, successful_analyses, failed_analyses = _process_batch_files(file_list)

        batch_summary = _summarize_batch_results(file_list, successful_analyses, failed_analyses)

        return render_template('batch_analysis.html',
                               results=batch_results,
                               summary=batch_summary)
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return _flash_and_redirect('upload_file', 'Error during batch analysis. Please try again.', 'error')

def _is_authorised_for_filename(filename: str, is_baseline: bool) -> bool:
    """Authorisation: allow baseline files to all, user files must be prefixed with user id."""
    # Baseline files are accessible to all users for comparison purposes
    return is_baseline or filename.startswith(f"{current_user.id}_")

def _resolve_file_path_for_analysis(filename: str, is_baseline: bool):
    """Resolve file path for user or baseline document and log details.

    Returns a tuple: (file_path, original_display_name, mapped_filename)
    """
    if is_baseline:
        # Map display name back to actual filename
        original_filename = filename.split(' - ')[-1] if ' - ' in filename else filename.replace(BASELINE_PREFIX + ' ', '')
        university_file_mapping = {
            'University of Oxford': 'oxford-ai-policy.pdf',
            'University of Cambridge': 'cambridge-ai-policy.pdf',
            'Imperial College London': 'imperial-ai-policy.docx',
            'University of Edinburgh': 'edinburgh university-ai-policy.pdf',
            'Leeds Trinity University': 'leeds trinity university-ai-policy.pdf',
            'MIT': 'mit-ai-policy.pdf',
            'Harvard University': 'harvard-ai-policy.pdf',
            'Stanford University': 'stanford-ai-policy.pdf',
            'University of Tokyo': 'tokyo-ai-policy.docx',
            'Jagiellonian University': 'jagiellonian university-ai-policy.pdf',
            'Belfast University': 'belfast university-ai-policy.pdf',
            'University of Chicago': 'chicago-ai-policy.docx',
            'Columbia University': 'columbia-ai-policy.pdf',
            'Cornell University': 'cornell-ai-policy.docx',
            'University of Liverpool': 'liverpool policy-ai-policy.pdf'
        }
        actual_filename = university_file_mapping.get(original_filename, original_filename)
        clean_dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'policies', 'clean_dataset')
        file_path = os.path.join(clean_dataset_dir, actual_filename)
        logger.info(f"Baseline analysis - Display name: {original_filename}")
        logger.info(f"Baseline analysis - Mapped filename: {actual_filename}")
        logger.info(f"Baseline analysis - File path: {file_path}")
        logger.info(f"Baseline analysis - File exists: {os.path.exists(file_path)}")
        return file_path, original_filename, actual_filename
    else:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"User analysis - File path: {file_path}")
        logger.info(f"User analysis - File exists: {os.path.exists(file_path)}")
        return file_path, None, None

def _get_existing_analysis_record(filename: str, is_baseline: bool):
    """Fetch existing analysis by filename for user, with baseline fallback (-1)."""
    existing = db_operations.get_analysis_by_filename(current_user.id, filename)
    if not existing and is_baseline:
        existing = db_operations.get_analysis_by_filename(-1, filename)
    return existing

def _unpack_existing_analysis(existing):
    """Return tuple (themes, classification, cleaned_text, extracted_text, analysis_id)."""
    themes = existing.get('themes', [])
    classification = existing.get('classification', {})
    cleaned_text = existing.get('text_data', {}).get('cleaned_text', '')
    extracted_text = existing.get('text_data', {}).get('original_text', '')
    analysis_id = str(existing.get('_id'))
    return themes, classification, cleaned_text, extracted_text, analysis_id

def _extract_and_analyse_text(file_path: str):
    """Extract text from file, clean it, derive themes and classification."""
    extracted_text = text_processor.extract_text_from_file(file_path)
    if not extracted_text:
        return None, None, None, None
    cleaned_text = text_processor.clean_text(extracted_text)
    themes = theme_extractor.extract_themes(cleaned_text)
    classification = policy_classifier.classify_policy(cleaned_text)
    return extracted_text, cleaned_text, themes, classification

def _store_analysis_results(filename, extracted_text, cleaned_text, themes, classification):
    """Store analysis results in DB and return analysis_id."""
    return db_operations.store_user_analysis_results(
        user_id=current_user.id,
        filename=filename,
        original_text=extracted_text,
        cleaned_text=cleaned_text,
        themes=themes,
        classification=classification,
        username=getattr(current_user, 'username', None)
    )

def _generate_analysis_derivatives(cleaned_text, themes, classification):
    """Generate charts and summaries used by results view."""
    charts = chart_generator.generate_analysis_charts(themes, classification, cleaned_text)
    text_stats = text_processor.get_text_statistics(cleaned_text)
    theme_summary = theme_extractor.get_theme_summary(themes)
    classification_details = policy_classifier.get_classification_details(cleaned_text)
    return charts, text_stats, theme_summary, classification_details

def _build_results_payload(filename, analysis_id, themes, classification, charts,
                           text_stats, theme_summary, classification_details,
                           extracted_text, cleaned_text):
    """Build the results dict passed to results.html, preserving original structure."""
    
    # Convert Plotly Figure objects to JSON for template rendering
    import plotly.utils
    charts_json = {}
    if charts:
        for chart_name, chart_obj in charts.items():
            if hasattr(chart_obj, 'to_json'):
                # It's a Plotly Figure object
                charts_json[chart_name] = chart_obj.to_json()
            else:
                # It's already a string or other format
                charts_json[chart_name] = chart_obj
    
    return {
        'filename': filename,
        'analysis_id': analysis_id,
        'themes': themes,
        'classification': classification,
        'charts': charts_json,
        'text_stats': text_stats,
        'theme_summary': theme_summary,
        'classification_details': classification_details,
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user': current_user,
        'processing_summary': {
            'original_length': len(extracted_text) if extracted_text else 0,
            'cleaned_length': len(cleaned_text) if cleaned_text else 0,
            'themes_found': len(themes) if themes else 0,
            'classification_confidence': (classification or {}).get('confidence', 0),
            'processing_method': (classification or {}).get('method', 'N/A')
        }
    }

@app.route('/analyse/<filename>')
@login_required
def analyse_document(filename):
    """
    Document analysis pipeline for individual policy files.
    
    Processes a single document through the complete AI analysis workflow
    including text extraction, theme analysis, and policy classification.
    """
    try:
        is_baseline = filename.startswith(BASELINE_PREFIX)

        early = _authorize_analysis_or_redirect(filename, is_baseline)
        if early is not None:
            return early

        file_path, early = _resolve_and_validate_path_or_redirect(filename, is_baseline)
        if early is not None:
            return early

        logger.info(f"Starting analysis of file: {filename}")

        extracted_text, cleaned_text, themes, classification, analysis_id = _get_or_create_analysis_record(
            filename, is_baseline, file_path
        )

        charts, text_stats, theme_summary, classification_details = _generate_analysis_derivatives(cleaned_text, themes, classification)

        logger.info(f"Analysis completed successfully for: {filename}")

        results = _build_results_payload(filename, analysis_id, themes, classification, charts,
                                         text_stats, theme_summary, classification_details,
                                         extracted_text, cleaned_text)

        return render_template('results.html', results=results)

    except Exception as e:
        logger.error(f"Error during analysis of {filename}: {str(e)}")
        return _flash_and_redirect('upload_file', 'Error analysing document. Please try again.', 'error')

def _authorize_analysis_or_redirect(filename: str, is_baseline: bool):
    """Authorise analysis request or return a redirect Response if not allowed."""
    if not _is_authorised_for_filename(filename, is_baseline):
        return _flash_and_redirect('upload_file', 'Access denied. You can only analyse your own documents or baseline policies.', 'error')
    return None

def _resolve_and_validate_path_or_redirect(filename: str, is_baseline: bool):
    """Resolve path for analysis and ensure it exists; return (path, redirect_or_none)."""
    file_path, _, _ = _resolve_file_path_for_analysis(filename, is_baseline)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None, _flash_and_redirect('upload_file', 'File not found', 'error')
    return file_path, None

@app.route('/validate/<analysis_id>')
@login_required
def validate_analysis(analysis_id):
    """
    Return JSON with citation validation issues for given analysis.
    
    Validates the academic sources and citations used in recommendations
    to ensure proper referencing standards.
    """
    from flask import jsonify
    analysis = db_operations.get_analysis_by_id(analysis_id)
    if not analysis:
        return jsonify({"error": ANALYSIS_NOT_FOUND}), 404
    recs = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)
    if not recs:
        # fallback: any user_id
        any_doc = db_operations.recommendations.find_one({"analysis_id": analysis_id})
        if any_doc:
            recs = any_doc.get("recommendations", [])
        else:
            # As a last resort, generate recommendations on the fly for validation
            text_data = analysis.get('text_data', {})
            cleaned_text = text_data.get('cleaned_text', text_data.get('original_text', ''))
            rec_package = recommendation_engine.generate_recommendations(
                themes=analysis.get('themes', []),
                classification=analysis.get('classification', {}),
                text=cleaned_text,
                analysis_id=analysis_id,
            )
            recs = rec_package.get('recommendations', [])
    from src.utils.validation import validate_recommendation_sources
    issues = validate_recommendation_sources(recs)
    return jsonify({"issues": issues})

def _prepare_recommendation_inputs(analysis_id):
    """
    Fetches and validates input for recommendations.
    Returns a tuple: ((analysis, themes, classification, cleaned_text), None) or (None, response)
    where 'response' is the redirect/response to return in case of an error.
    """
    analysis = _fetch_analysis_for_recommendations(analysis_id)
    if analysis is None:
        logger.error(f"Analysis {analysis_id} not found in global lookup")
        flash(f'{ANALYSIS_NOT_FOUND}.', 'error')
        return None, redirect(url_for('dashboard'))

    themes = analysis.get('themes', [])
    classification = analysis.get('classification', {})
    cleaned_text = _extract_cleaned_text_with_logging(analysis)

    if not cleaned_text:
        logger.error("No text content found in analysis to generate recommendations")
        flash('Analysis text not found. Cannot generate recommendations.', 'warning')
        return None, redirect(url_for('dashboard'))

    return (analysis, themes, classification, cleaned_text), None

@app.route('/recommendations/<analysis_id>')
@login_required
def get_recommendations(analysis_id):
    """
    Generate evidence-based recommendations for policy improvement.
    
    Creates detailed, academic-quality recommendations based on ethical
    AI framework analysis and institutional context assessment.
    """
    try:
        logger.info("=== Starting recommendation generation ===")
        logger.info(f"User ID: {current_user.id}, Username: {getattr(current_user, 'username', 'N/A')}")
        logger.info(f"Analysis ID: {analysis_id}")

        prep, error = _prepare_recommendation_inputs(analysis_id)
        if error:
            return error
        analysis, themes, classification, cleaned_text = prep

        recommendation_package = _load_or_generate_recommendations(
            analysis_id,
            cleaned_text,
            themes=themes,
            classification=classification,
        )
        if recommendation_package is None:
            flash('Unable to generate recommendation, please contact with administrator. This will be sorted soon.', 'error')
            return redirect(url_for('dashboard'))

        recommendation_data = _build_recommendation_data(analysis_id, analysis, themes, classification, recommendation_package)
        logger.info(f"Generated {recommendation_data['total_recommendations']} recommendations")
        try:
            has_narr = bool(recommendation_data.get('narrative', {}).get('html'))
            logger.info(f"Narrative present: {has_narr}")
        except Exception as _e:
            logger.warning(f"Could not determine narrative presence: {_e}")

        _store_recommendations_safe(analysis_id, recommendation_package)

        return render_template('recommendations.html', data=recommendation_data)

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return _fallback_recommendations_response(analysis_id, locals().get('analysis'))


def _get_analysis_for_deletion(user_id: int, analysis_id: str):
    """Fetch the user's analysis to delete or return None."""
    return db_operations.get_user_analysis_by_id(user_id, analysis_id)

def _is_protected_baseline(filename: str) -> bool:
    """Check whether the file is a baseline policy protected from deletion."""
    return bool(filename and filename.startswith(BASELINE_PREFIX))

def _build_possible_filenames(filename: str, user_id: int, document_id: str) -> list:
    """Build a list of possible filenames to clean up after deleting the analysis."""
    names = [filename]
    if user_id is not None:
        names.append(f"{user_id}_{filename}")
    if document_id:
        names.append(document_id)
    if not filename.lower().endswith('.pdf'):
        names.append(f"{filename}.pdf")
        if user_id is not None:
            names.append(f"{user_id}_{filename}.pdf")
    # Filter out empty/duplicate entries, preserving order
    seen = set()
    ordered = []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered

def _cleanup_analysis_files(upload_folder: str, possible_filenames: list) -> None:
    """Attempt to delete physical files linked to the analysis; do not raise exceptions."""
    for fname in possible_filenames:
        file_path = os.path.join(upload_folder, fname)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Successfully deleted file: {file_path}")
                break  # stop after the first successful deletion
            except Exception as e:
                logger.warning(f"Could not delete file {file_path}: {e}")

def _delete_analysis_record(user_id: int, analysis_id: str) -> bool:
    """Delete the user's analysis record; return True/False according to the DB outcome."""
    return db_operations.delete_user_analysis(user_id, analysis_id)

def _cleanup_analysis_files_after_deletion(analysis: dict, upload_folder: str) -> None:
    """Perform cleanup of files linked to the analysis after it is removed (without raising exceptions)."""
    try:
        filename = analysis.get('filename', '')
        possible_filenames = _build_possible_filenames(
            filename,
            analysis.get('user_id', None),
            analysis.get('document_id', '')
        )
        _cleanup_analysis_files(upload_folder, possible_filenames)
    except Exception as e:
        logger.error(f"Error during file cleanup for analysis {analysis.get('_id', 'unknown')}: {str(e)}")

def _fetch_analysis_or_redirect_for_delete(user_id: int, analysis_id: str):
    """Fetch analysis and enforce deletion guards; return (analysis, redirect_response_or_None)."""
    analysis = _get_analysis_for_deletion(user_id, analysis_id)
    if not analysis:
        flash(f'{ANALYSIS_NOT_FOUND} or access denied.', 'error')
        return None, redirect(url_for('dashboard'))
    if _is_protected_baseline(analysis.get('filename', '')):
        flash('Baseline policies cannot be deleted.', 'warning')
        return None, redirect(url_for('dashboard'))
    return analysis, None

@app.route('/delete_analysis/<analysis_id>', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """Delete a user's analysis and associated files."""
    try:
        analysis, redirect_resp = _fetch_analysis_or_redirect_for_delete(current_user.id, analysis_id)
        if redirect_resp:
            return redirect_resp
        
        # Delete the analysis record
        if _delete_analysis_record(current_user.id, analysis_id):
            # Clean up associated files
            _cleanup_analysis_files_after_deletion(analysis, app.config['UPLOAD_FOLDER'])
            flash('Analysis deleted successfully.', 'success')
        else:
            flash('Failed to delete analysis.', 'error')
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {str(e)}")
        flash('An error occurred while deleting the analysis.', 'error')
        return redirect(url_for('dashboard'))

@login_required
def api_explain_analysis(analysis_id):
    """
    Return JSON with classification explanation keywords.
    
    Provides key terms that influenced the AI policy classification
    decision for transparency and explainability purposes.
    """
    try:
        analysis = db_operations.get_analysis_by_id(analysis_id)
        if not analysis or analysis.get('user_id') != current_user.id:
            return jsonify({'error': ANALYSIS_NOT_FOUND}), 404

        cleaned_text = analysis.get('text_data', {}).get('cleaned_text', '')
        if not cleaned_text:
            return jsonify({'error': 'No cleaned text available'}), 400

        classifier = PolicyClassifier()
        keywords = classifier.explain_classification(cleaned_text, top_n=15)
        result = [{"term": kw, "category": cat, "score": score} for kw, cat, score in keywords]
        return jsonify({'analysis_id': analysis_id, 'keywords': result})
    except Exception as e:
        logger.error(f"API explain error for analysis {analysis_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analysis/<analysis_id>')
@login_required
def api_get_analysis(analysis_id):
    """
    API endpoint to retrieve analysis results in JSON format.
    
    Provides programmatic access to stored analysis data
    for integration with external systems or applications.
    """
    try:
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        if analysis:
            return jsonify({'success': True, 'data': analysis})
        else:
            return jsonify({'success': False, 'error': ANALYSIS_NOT_FOUND}), 404
    except Exception as e:
        logger.error(f"API error for analysis {analysis_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Public routes

# Error handlers

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 not found errors."""
    logger.warning(f"404 error: {request.url}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 internal server errors."""
    logger.error(f"500 error: {str(error)}")
    return render_template('errors/500.html'), 500

# Export routes

# Export view route removed - export now works directly from recommendations page

def _get_export_analysis(analysis_id):
    """Fetch analysis first from user's scope, then globally; return dict or None. Includes logging identical to original flow."""
    logger.info("Attempting to get user's analysis...")
    analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
    if analysis:
        logger.info("Found analysis in user's analyses")
        logger.info(f"Analysis details - Filename: {analysis.get('filename')}, ID: {analysis_id}")
        return analysis

    logger.info(f"{ANALYSIS_NOT_FOUND} in user's analyses, trying global lookup...")
    analysis = db_operations.get_analysis_by_id(analysis_id)
    if analysis:
        logger.info("Found analysis in global collection")
        logger.info(f"Analysis details - Filename: {analysis.get('filename')}, ID: {analysis_id}")
        return analysis
    return None

# Helper functions for export view removed - no longer needed

@app.route('/export/<analysis_id>/pdf')
@login_required
def export_pdf(analysis_id):
    """
    Export recommendations and analysis results as PDF.
    
    Generates a PDF document containing all recommendations and
    analysis results for the specified analysis.
    """
    try:
        export_data, error = _prepare_basic_export_data_or_error(analysis_id)
        if error:
            return error
        return _export_binary_via_engine(export_data, analysis_id, 'pdf')
    except Exception as e:
        logger.error(f"Error exporting to PDF: {str(e)}")
        return jsonify({'error': 'Error generating PDF export'}), 500

@app.route('/export/<analysis_id>/word')
@login_required
def export_word(analysis_id):
    """
    Export recommendations and analysis results as Word document.
    
    Generates a Word document containing all recommendations and
    analysis results for the specified analysis.
    """
    try:
        export_data, error = _prepare_basic_export_data_or_error(analysis_id)
        if error:
            return error
        return _export_binary_via_engine(export_data, analysis_id, 'word')
    except Exception as e:
        logger.error(f"Error exporting to Word: {str(e)}")
        return jsonify({'error': 'Error generating Word export'}), 500

@app.route('/export/<analysis_id>/excel')
@login_required
def export_excel(analysis_id):
    """
    Export recommendations and analysis results as Excel spreadsheet.
    
    Generates an Excel spreadsheet containing all recommendations and
    analysis results for the specified analysis.
    """
    try:
        export_data, error = _prepare_basic_export_data_or_error(analysis_id)
        if error:
            return error
        return _export_binary_via_engine(export_data, analysis_id, 'excel')
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return jsonify({'error': 'Error generating Excel export'}), 500

# Register template filters
app.jinja_env.filters["clean_university_name"] = clean_university_name
app.jinja_env.filters["clean_filename"] = clean_filename
app.jinja_env.filters["format_british_date"] = format_british_date

# Import and register additional template filters
from src.web.utils.template_utils import clean_literature_name
app.jinja_env.filters["clean_literature_name"] = clean_literature_name

def _flash_and_redirect(endpoint: str, message: str, category: str, **kwargs):
    """Utility: flash a message and redirect to a named endpoint."""
    flash(message, category)
    return redirect(url_for(endpoint, **kwargs))

def handle_first_login_onboarding(user_id: int) -> bool:
    """
    Handle automatic onboarding for new users by loading sample policies.
    
    Provides new users with baseline policy examples to demonstrate
    the system capabilities and provide comparison benchmarks.
    """
    try:
        from src.database.models import User

        user = User.query.get(user_id)
        if not user:
            return False

        if not user.is_first_login():
            return False

        logger.info(f"Starting onboarding for new user: {user.username}")

        success = db_operations.load_sample_policies_for_user(user_id)
        if success:
            return _complete_onboarding_with_message(user, "Welcome! We have loaded 15 sample university policies to get you started.", "success")

        # Fallback: treat as success if baselines already exist
        if _baseline_exists_for_user(user_id):
            logger.info("Baselines already exist; marking onboarding complete.")
            return _complete_onboarding_with_message(user, "Welcome! Sample policies are already available in your dashboard.", "info")

        logger.warning(f"Onboarding failed for user: {user.username}")
        flash("Welcome! There was an issue loading sample policies.", "warning")
        return False

    except Exception as e:
        logger.error(f"Error in onboarding: {e}")
        return False

def _baseline_exists_for_user(user_id: int) -> bool:
    """Check if user already has any baseline analyses available."""
    try:
        user_analyses = db_operations.get_user_analyses(user_id)
        return any(a.get('filename', '').startswith(BASELINE_PREFIX) for a in user_analyses)
    except Exception as _:
        return False

def _complete_onboarding_with_message(user, message: str, category: str) -> bool:
    """Mark onboarding complete, log, flash message, and return True."""
    user.complete_onboarding()
    logger.info(f"Onboarding completed for user: {user.username}")
    flash(message, category)
    return True

if __name__ == '__main__':
    """Run the PolicyCraft application in development mode."""
    
    # CRITICAL: Validate all dependencies before starting application
    validate_dependencies()
    
    os.makedirs('logs', exist_ok=True)
    create_upload_folder()
    
    logger.info("Starting PolicyCraft Application")
    
    # Note: Automatic document scanning disabled to prevent excessive backups
    # Documents are now processed on-demand when uploaded via admin interface
    logger.info("Automatic document scanning disabled - documents processed on upload")
    
    # Respect environment variables for host/port; default to localhost:5001
    host = os.getenv('HOST', 'localhost')
    try:
        port = int(os.getenv('PORT', '5001'))
    except ValueError:
        port = 5001

    print(f"PolicyCraft starting at: http://{host}:{port}")
    
    # Disable the auto-reloader to avoid infinite restart loops caused by
    # file change notifications in venv/site-packages (macOS fsevents).
    app.run(debug=True, host=host, port=port, use_reloader=False)