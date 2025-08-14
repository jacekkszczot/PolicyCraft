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
        logger.warning("Temporary disabling permission checks for testing")
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

def _load_or_generate_recommendations(analysis_id, cleaned_text):
    """Load stored recommendations or generate new ones with debug prints; return package or None on error."""
    stored_recs = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)
    if stored_recs:
        return {
            'recommendations': stored_recs,
            'analysis_metadata': {
                'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'methodology': 'Previously generated'
            }
        }

def _get_or_create_analysis_record(filename: str, is_baseline: bool, file_path: str):
    """Pobierz istniejącą analizę lub uruchom nową i zwróć komplet danych.
    Zwraca: extracted_text, cleaned_text, themes, classification, analysis_id
    Rzuca ValueError('no_text'), jeśli nie udało się wydobyć tekstu (zachowanie jak dotychczas).
    """
    existing = _get_existing_analysis_record(filename, is_baseline)
    if existing:
        themes, classification, cleaned_text, extracted_text, analysis_id = _unpack_existing_analysis(existing)
        return extracted_text, cleaned_text, themes, classification, analysis_id

    extracted_text, cleaned_text, themes, classification = _extract_and_analyse_text(file_path)
    if not extracted_text:
        raise ValueError('no_text')
    analysis_id = _store_analysis_results(filename, extracted_text, cleaned_text, themes, classification)
    return extracted_text, cleaned_text, themes, classification, analysis_id

def _build_basic_export_data(analysis_id, analysis, recommendations):
    """Zbuduj bazowy pakiet danych exportu używany przez PDF/Word/Excel (bez wykresów)."""
    return {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': analysis.get('classification', {}).get('classification', 'Unknown'),
            'confidence': analysis.get('classification', {}).get('confidence', 0),
            'analysis_id': analysis_id,
            'themes': analysis.get('themes', [])
        },
        'recommendations': recommendations,
        'generated_date': datetime.now().isoformat(),
        'total_recommendations': len(recommendations)
    }

def _prepare_basic_export_data_or_error(analysis_id):
    """Pobierz analizę i rekomendacje; zwróć (export_data, None) albo (None, (json, code))."""
    analysis = _get_export_analysis(analysis_id)
    if not analysis:
        return None, (jsonify({'error': ANALYSIS_NOT_FOUND}), 404)
    recommendations = _get_export_recommendations(analysis_id)
    if not recommendations:
        return None, (jsonify({'error': NO_RECOMMENDATIONS_FOUND}), 404)
    return _build_basic_export_data(analysis_id, analysis, recommendations), None

def _make_binary_response(binary_data: bytes, content_type: str, filename: str):
    """Utwórz binarną odpowiedź HTTP z odpowiednimi nagłówkami."""
    response = make_response(binary_data)
    response.headers['Content-Type'] = content_type
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

    try:
        print("\n===== GENERATING RECOMMENDATIONS WITH KNOWLEDGE BASE =====\n")
        recommendations = recommendation_engine.generate_recommendations(
            policy_text=cleaned_text,
            institution_type="university",
            analysis_id=analysis_id
        )
        print("\n===== RECOMMENDATIONS GENERATED =====\n")

        for i, rec in enumerate(recommendations.get("recommendations", [])):
            print(f"Recommendation {i+1}: {rec.get('title', 'Unknown')}")
            print(f"  Sources: {rec.get('sources', [])}")
            print(f"  References: {len(rec.get('references', []))} items")
        print("\n===== END OF RECOMMENDATIONS DEBUG =====\n")

        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return None

def _build_recommendation_data(analysis_id, analysis, themes, classification, recommendation_package):
    """Build the data dict for recommendations template, matching original keys."""
    return {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': classification.get('classification', 'Unknown'),
            'confidence': classification.get('confidence', 0),
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
        'total_recommendations': len(recommendation_package.get('recommendations', []))
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
        basic_data = {
            'analysis': {
                'filename': (analysis or {}).get('filename', 'Unknown') if analysis else 'Unknown',
                'classification': (analysis or {}).get('classification', {}).get('classification', 'Unknown') if analysis else 'Unknown',
                'analysis_id': analysis_id
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
"""
Main Flask application for PolicyCraft - AI Policy Analysis Framework.
Clean version without onboarding features.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

# Import configuration
from config import get_config, create_secure_directories

# Import authentication components
from src.database.models import User, db, init_db
from src.auth.routes import auth_bp
from src.admin.routes import admin_bp

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
from src.recommendation.engine import RecommendationGenerator as RecommendationEngine
from src.export.export_engine import ExportEngine
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
    
    # Remove file extensions
    clean_name = clean_name.replace('.pdf', '').replace(DOCX_EXTENSION, '').replace('.doc', '').replace('.txt', '')
    clean_name = clean_name.replace('-ai-policy', '').replace('_ai_policy', '')
    
    # Map to clean university names
    name_lower = clean_name.lower()
    if 'harvard' in name_lower:
        return 'Harvard University'
    elif 'stanford' in name_lower:
        return 'Stanford University'
    elif 'mit' in name_lower:
        return 'MIT'
    elif 'cambridge' in name_lower:
        return 'University of Cambridge'
    elif 'oxford' in name_lower:
        return 'Oxford University'
    elif 'belfast' in name_lower:
        return 'Belfast University'
    elif 'edinburgh' in name_lower:
        return 'Edinburgh University'
    elif 'columbia' in name_lower:
        return 'Columbia University'
    elif 'cornell' in name_lower:
        return 'Cornell University'
    elif 'chicago' in name_lower:
        return 'University of Chicago'
    elif 'imperial' in name_lower:
        return 'Imperial College London'
    elif 'tokyo' in name_lower:
        return 'University of Tokyo'
    elif 'jagiellonian' in name_lower:
        return 'Jagiellonian University'
    elif 'leeds' in name_lower and 'trinity' in name_lower:
        return 'Leeds Trinity University'
    elif 'liverpool' in name_lower:
        return 'University of Liverpool'
    else:
        # Generic cleanup
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
    
    Initialises and configures the Flask application with all necessary
    extensions, blueprints, and database connections.
    """
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
    
    # Register blueprints (auth without prefix to expose /login and /logout)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # CSRF protection and csrf_token for templates (available for all app instances)
    CSRFProtect(app)
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

    # Initialise database and create tables
    with app.app_context():
        init_db(app)
    
    return app

# Create Flask app and initialize modules
app = create_app()

 

text_processor = TextProcessor()
theme_extractor = ThemeExtractor()
policy_classifier = PolicyClassifier()
db_operations = DatabaseOperations(uri="mongodb://localhost:27017", db_name="policycraft")
chart_generator = ChartGenerator()
# Initialise recommendation engine with knowledge base path (unified with admin panel)
knowledge_base_path = "docs/knowledge_base"  # Use same path as LiteratureEngine
recommendation_engine = RecommendationEngine(knowledge_base_path=knowledge_base_path)


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

        extracted_text, cleaned_text, themes, classification = _extract_and_analyse_text(file_path)
        if not extracted_text:
            return {'filename': filename, 'error': 'Text extraction failed'}, False

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
    return {
        'requested': len(file_list),
        'successful': successful_analyses,
        'failed': failed_analyses,
        'filenames': file_list,
    }

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
    """Fallback ekstrakcji dla PDF przy użyciu pdfplumber (bez twardych zależności globalnych)."""
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
    """Fallback ekstrakcji dla DOCX/DOC przy użyciu python-docx (Document)."""
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
    """Zapewnij minimalny tekst zastępczy jeśli ekstrakcja nieudana lub zbyt krótka."""
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
    """Zapewnij domyślne wartości do zapisu analizy bazowej (bez zmiany zachowania)."""
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
    """Zbuduj metadane zapisu zgodnie z dotychczasowym formatem."""
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
    """Zbuduj placeholder analizy w przypadku błędu zapisu, zgodnie z aktualnym formatem."""
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
            document_id=missing_file,
            metadata=metadata
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
    """Utwórz analizy bazowe dla brakujących plików używając bezpiecznych helperów."""
    for missing_file in missing_files:
        # Pomiń pliki pomocnicze
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
        
        # Get and prepare analyses
        db_operations.deduplicate_baseline_analyses(current_user.id)
        user_analyses = db_operations.get_user_analyses(current_user.id)
        baseline_analyses = db_operations.get_user_analyses(-1)
        
        logger.info(f"Dashboard: Found {len(user_analyses)} user analyses and {len(baseline_analyses)} baseline analyses")
        
        # Load all clean_dataset policies without duplicates
        # This ensures we show exactly 15 unique policies from clean_dataset
        clean_dataset_dir = _get_clean_dataset_dir()
        clean_dataset_files = _list_clean_dataset_files(clean_dataset_dir)
        
        # Merge user and baseline analyses
        analyses_by_filename = _merge_user_and_baseline_analyses(user_analyses, baseline_analyses)
        
        # Identify missing clean_dataset files and ensure baselines exist
        missing_files = _identify_missing_clean_files(clean_dataset_files, analyses_by_filename)
        logger.info(f"Dashboard: Missing files from clean_dataset: {missing_files}")
        
        # Add missing files as proper baseline analyses via helper
        _create_missing_baselines(clean_dataset_dir, missing_files, analyses_by_filename)

        # Combine all analyses into a single list
        combined_analyses = list(analyses_by_filename.values())
        logger.info(f"Dashboard: Combined into {len(combined_analyses)} total analyses")
        
        # Log the filenames of all analyses being displayed
        displayed_files = [analysis.get('filename', '') for analysis in combined_analyses]
        logger.info(f"Dashboard: Displaying analyses for: {sorted(displayed_files)}")
        
        # Sort by date (newest first)
        combined_analyses.sort(key=lambda a: _to_epoch(a.get('analysis_date')), reverse=True)
        
        # Load sample policies if needed
        _load_sample_policies_if_needed(user_analyses)
        
        # Generate dashboard data
        dashboard_data = _prepare_dashboard_data(
            current_user, 
            user_analyses, 
            combined_analyses
        )
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Dashboard loaded with limited data due to an error.', 'warning')
        return render_template('dashboard.html', data=_get_minimal_dashboard_data(current_user))

def _get_clean_dataset_dir():
    """Return absolute path to clean_dataset directory."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'policies', 'clean_dataset')

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
    try:
        dashboard_charts = chart_generator.generate_user_dashboard_charts(user_analyses)
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        dashboard_charts = {}
    
    # Log analyses before analytics calculation
    for i, analysis in enumerate(combined_analyses):
        logger.info(f"Dashboard debug: Analysis {i} type: {type(analysis)}")
        if isinstance(analysis, dict):
            cls = analysis.get('classification', 'Not found')
            logger.info(f"Dashboard debug: Analysis {i} classification type: {type(cls)}, value: {cls}")
        else:
            logger.error(f"Dashboard debug: Analysis {i} is not a dict: {type(analysis)}")
    
    # Calculate analytics
    try:
        classification_counts, theme_frequencies = _calculate_analytics(combined_analyses)
        logger.info(f"Dashboard debug: Classification counts: {classification_counts}")
    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        import traceback
        logger.error(f"Analytics calculation traceback: {traceback.format_exc()}")
        classification_counts = {'Restrictive': 0, 'Moderate': 0, 'Permissive': 0}
        theme_frequencies = {}
    
    # Get combined statistics
    try:
        user_stats = db_operations.get_analysis_statistics(user.id)
        baseline_stats = db_operations.get_analysis_statistics(-1)
        combined_stats = _combine_stats(user_stats, baseline_stats)
        
        db_stats = {
            'total_analyses': combined_stats.get('total', 0),
            'avg_confidence': round(combined_stats.get('avg_confidence', 0), 1),
            'avg_themes_per_analysis': round(combined_stats.get('avg_themes_per_analysis', 0), 1)
        }
    except Exception as e:
        logger.error(f"DB stats error: {e}")
        db_stats = {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}
    
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
    try:
        processed_analyses = _process_analyses_for_display(combined_analyses)
        logger.info(f"Dashboard: Processed {len(processed_analyses)} analyses for display")
        
        # Debug first few processed analyses
        for i, analysis in enumerate(processed_analyses[:3]):
            logger.info(f"Dashboard debug: Processed analysis {i} keys: {list(analysis.keys())}")
            if 'classification' in analysis:
                logger.info(f"Dashboard debug: Processed analysis {i} classification type: {type(analysis['classification'])}, value: {analysis['classification']}")
    except Exception as e:
        logger.error(f"Processing analyses error: {e}")
        import traceback
        logger.error(f"Processing analyses traceback: {traceback.format_exc()}")
        processed_analyses = []
    
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
    if not uploaded_files:
        flash('No files selected', 'error')
        return redirect(request.url)

    # Check file limit
    max_files = app.config.get('MAX_FILES_PER_UPLOAD', 10)
    if len(uploaded_files) > max_files:
        flash(f'Too many files. Maximum {max_files} files allowed.', 'error')
        return redirect(request.url)

    successful_uploads, failed_uploads = _process_uploaded_files(uploaded_files)
    
    # Provide feedback
    if successful_uploads:
        if len(successful_uploads) == 1:
            flash('File uploaded successfully! Starting analysis...', 'success')
            return redirect(url_for('analyse_document', filename=successful_uploads[0]['unique']))
        else:
            flash(f'{len(successful_uploads)} files uploaded successfully! Starting batch analysis...', 'success')
            file_list = [f['unique'] for f in successful_uploads]
            return redirect(url_for('batch_analyse', files=','.join(file_list)))
    
    if failed_uploads:
        error_msg = f"{len(failed_uploads)} files failed to upload: " + ", ".join([f['filename'] for f in failed_uploads])
        flash(error_msg, 'error')
    
    return redirect(request.url)

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
            flash('Access denied. You can only analyse your own documents.', 'error')
            return redirect(url_for('upload_file'))

        logger.info(f"Starting batch analysis of {len(file_list)} files")

        batch_results = []
        successful_analyses = 0
        failed_analyses = 0

        for i, filename in enumerate(file_list, 1):
            result, ok = _process_single_batch_file(filename)
            batch_results.append(result)
            if ok:
                successful_analyses += 1
            else:
                failed_analyses += 1

        batch_summary = _summarize_batch_results(file_list, successful_analyses, failed_analyses)

        return render_template('batch_analysis.html',
                               results=batch_results,
                               summary=batch_summary)
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        flash('Error during batch analysis. Please try again.', 'error')
        return redirect(url_for('upload_file'))

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
    return {
        'filename': filename,
        'analysis_id': analysis_id,
        'themes': themes,
        'classification': classification,
        'charts': charts,
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

        if not _is_authorised_for_filename(filename, is_baseline):
            flash('Access denied. You can only analyse your own documents or baseline policies.', 'error')
            return redirect(url_for('upload_file'))

        file_path, _, _ = _resolve_file_path_for_analysis(filename, is_baseline)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            flash('File not found', 'error')
            return redirect(url_for('upload_file'))

        logger.info(f"Starting analysis of file: {filename}")

        try:
            extracted_text, cleaned_text, themes, classification, analysis_id = _get_or_create_analysis_record(
                filename, is_baseline, file_path
            )
        except ValueError:
            flash('Could not extract text from file', 'error')
            return redirect(url_for('upload_file'))

        charts, text_stats, theme_summary, classification_details = _generate_analysis_derivatives(cleaned_text, themes, classification)

        logger.info(f"Analysis completed successfully for: {filename}")

        results = _build_results_payload(filename, analysis_id, themes, classification, charts,
                                         text_stats, theme_summary, classification_details,
                                         extracted_text, cleaned_text)

        return render_template('results.html', results=results)

    except Exception as e:
        logger.error(f"Error during analysis of {filename}: {str(e)}")
        flash('Error analysing document. Please try again.', 'error')
        return redirect(url_for('upload_file'))

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
                policy_text=cleaned_text,
                analysis_id=analysis_id
            )
            recs = rec_package.get('recommendations', [])
    from src.utils.validation import validate_recommendation_sources
    issues = validate_recommendation_sources(recs)
    return jsonify({"issues": issues})

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

        analysis = _fetch_analysis_for_recommendations(analysis_id)
        if analysis is None:
            logger.error(f"Analysis {analysis_id} not found in global lookup")
            flash(f'{ANALYSIS_NOT_FOUND}.', 'error')
            return redirect(url_for('dashboard'))

        themes = analysis.get('themes', [])
        classification = analysis.get('classification', {})
        cleaned_text = _extract_cleaned_text_with_logging(analysis)

        if not cleaned_text:
            logger.error("No text content found in analysis to generate recommendations")
            flash('Analysis text not found. Cannot generate recommendations.', 'warning')
            return redirect(url_for('dashboard'))

        recommendation_package = _load_or_generate_recommendations(analysis_id, cleaned_text)
        if recommendation_package is None:
            flash('Error generating recommendations. Please try again.', 'error')
            return redirect(url_for('dashboard'))

        recommendation_data = _build_recommendation_data(analysis_id, analysis, themes, classification, recommendation_package)
        logger.info(f"Generated {recommendation_data['total_recommendations']} recommendations")

        _store_recommendations_safe(analysis_id, recommendation_package)

        return render_template('recommendations.html', data=recommendation_data)

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return _fallback_recommendations_response(analysis_id, locals().get('analysis'))


@app.route('/delete_analysis/<analysis_id>', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """
    Delete user analysis with appropriate security checks.
    
    Removes analysis records from database while protecting baseline
    policies from accidental deletion.
    """
    logger.info(f"Attempting deletion of analysis {analysis_id} by user {current_user.id}")
    try:
        # Get analysis to check ownership and type
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        if not analysis:
            flash(f'{ANALYSIS_NOT_FOUND} or access denied.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if it's a baseline policy (protect from deletion)
        filename = analysis.get('filename', '')
        if filename.startswith(BASELINE_PREFIX):
            flash('Baseline policies cannot be deleted.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Delete the analysis and related data
        success = db_operations.delete_user_analysis(current_user.id, analysis_id)
        if success:
            # Try to delete the physical file if it exists
            try:
                # Check multiple possible file locations and naming patterns
                possible_filenames = [
                    filename,  # Original filename
                    f"{current_user.id}_{filename}",  # Prefixed with user ID
                    analysis.get('document_id', '')  # Document ID if different
                ]
                
                # Also check for files with .pdf extension if original doesn't have it
                if not filename.lower().endswith('.pdf'):
                    possible_filenames.append(f"{filename}.pdf")
                    possible_filenames.append(f"{current_user.id}_{filename}.pdf")
                
                # Try each possible filename
                for fname in possible_filenames:
                    if not fname:  # Skip empty filenames
                        continue
                        
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"Successfully deleted file: {file_path}")
                            break  # Stop after first successful deletion
                        except Exception as e:
                            logger.warning(f"Could not delete file {file_path}: {e}")
            
            except Exception as e:
                logger.error(f"Error during file cleanup for analysis {analysis_id}: {str(e)}")
                # Don't fail the whole operation if file deletion fails
            
            flash('Analysis and related data deleted successfully.', 'success')
        else:
            logger.error(f"Failed to delete analysis {analysis_id} for user {current_user.id}")
            flash('Error deleting analysis. Please try again or contact support if the issue persists.', 'error')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}")
        flash('Error deleting analysis.', 'error')
        return redirect(url_for('dashboard'))

# API routes for additional functionality

@app.route('/api/explain/<analysis_id>')
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

@app.route('/export/<analysis_id>')
@login_required
def export_view(analysis_id):
    """
    Display export view for recommendations and analysis results.
    
    Renders a dedicated template for exporting recommendations and
    analysis results to various formats (PDF, Word, Excel).
    """
    try:
        logger.info("=== Starting export view preparation ===")
        logger.info(f"User ID: {current_user.id}, Analysis ID: {analysis_id}")

        analysis = _get_export_analysis(analysis_id)
        if analysis is None:
            logger.error(f"Analysis {analysis_id} not found in global lookup")
            flash(f'{ANALYSIS_NOT_FOUND}.', 'error')
            return redirect(url_for('recommendations'))

        recommendations = _get_export_recommendations(analysis_id)
        if not recommendations:
            logger.warning(f"No recommendations found for analysis {analysis_id}")
            flash(f'{NO_RECOMMENDATIONS_FOUND}.', 'warning')
            return redirect(url_for('get_recommendations', analysis_id=analysis_id))

        charts = _generate_export_charts(analysis)
        export_data = _build_export_view_data(analysis_id, analysis, recommendations, charts)

        return render_template('export_recommendations.html', data=export_data)

    except Exception as e:
        logger.error(f"Error preparing export view: {str(e)}")
        logger.exception("Full traceback for export view error:")
        flash('Error preparing export view. Please try again.', 'error')
        return redirect(url_for('dashboard'))

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

def _get_export_recommendations(analysis_id):
    """Fetch recommendations for the current user and given analysis; includes logging consistent with original code."""
    logger.info(f"Attempting to get recommendations for analysis {analysis_id}...")
    recommendations = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)
    if recommendations:
        logger.info(f"Found {len(recommendations)} recommendations for analysis {analysis_id}")
    return recommendations

def _generate_export_charts(analysis):
    """Generate charts for export view with error handling and logging."""
    logger.info("Generating charts for export view...")
    themes = analysis.get('themes', [])
    classification = analysis.get('classification', {})
    cleaned_text = analysis.get('text_data', {}).get('cleaned_text', '')
    try:
        charts = chart_generator.generate_analysis_charts(themes, classification, cleaned_text)
        logger.info(f"Generated {len(charts)} charts for export view")
        return charts
    except Exception as chart_error:
        logger.error(f"Error generating charts: {chart_error}")
        return {}

def _build_export_view_data(analysis_id, analysis, recommendations, charts):
    """Build the data dict passed to the export template, mirroring original structure."""
    return {
        'analysis': {
            'filename': analysis.get('filename', 'Unknown'),
            'classification': analysis.get('classification', {}).get('classification', 'Unknown'),
            'confidence': analysis.get('classification', {}).get('confidence', 0),
            'analysis_id': analysis_id,
            'themes': analysis.get('themes', []),
            'text_data': analysis.get('text_data', {})
        },
        'recommendations': recommendations,
        'generated_date': datetime.now().isoformat(),
        'total_recommendations': len(recommendations),
        'charts': charts
    }

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
        from src.export import ExportEngine
        export_engine = ExportEngine()
        pdf_data = export_engine.export_to_pdf(export_data)
        return _make_binary_response(pdf_data, 'application/pdf', f'PolicyCraft_Analysis_{analysis_id}.pdf')
        
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
        from src.export import ExportEngine
        export_engine = ExportEngine()
        docx_data = export_engine.export_to_word(export_data)
        return _make_binary_response(
            docx_data,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            f'PolicyCraft_Analysis_{analysis_id}.docx'
        )
        
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
        from src.export import ExportEngine
        export_engine = ExportEngine()
        excel_data = export_engine.export_to_excel(export_data)
        return _make_binary_response(
            excel_data,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            f'PolicyCraft_Analysis_{analysis_id}.xlsx'
        )
        
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
            
        # Check if user needs onboarding
        if user.is_first_login():
            logger.info(f"Starting onboarding for new user: {user.username}")
            
            # Load sample policies automatically
            success = db_operations.load_sample_policies_for_user(user_id)
            
            if success:
                # Mark onboarding as completed
                user.complete_onboarding()
                logger.info(f"Onboarding completed for user: {user.username}")
                flash("Welcome! We have loaded 15 sample university policies to get you started.", "success")
                return True
            else:
                # If sample load failed, but user already has baseline analyses, treat as success
                # Robust baseline detection check if ANY analysis filename starts with BASELINE
                try:
                    user_analyses = db_operations.get_user_analyses(user_id)
                    baseline_exists = any(a.get('filename', '').startswith(BASELINE_PREFIX) for a in user_analyses)
                except Exception as _:
                    baseline_exists = False
                if baseline_exists:
                    user.complete_onboarding()
                    logger.info(f"Baseline analyses detected despite load failure onboarding marked complete for {user.username}")
                    flash("Welcome! Sample policies are already available in your dashboard.", "info")
                    return True
                logger.warning(f"Onboarding failed for user: {user.username}")
                flash("Welcome! There was an issue loading sample policies.", "warning")
                
        return False
        
    except Exception as e:
        logger.error(f"Error in onboarding: {e}")
        return False

if __name__ == '__main__':
    """Run the PolicyCraft application in development mode."""
    os.makedirs('logs', exist_ok=True)
    create_upload_folder()
    
    logger.info("Starting PolicyCraft Application")
    
    # Note: Automatic document scanning disabled to prevent excessive backups
    # Documents are now processed on-demand when uploaded via admin interface
    logger.info("Automatic document scanning disabled - documents processed on upload")
    
    print("PolicyCraft starting at: http://localhost:5001")
    
    app.run(debug=True, host='localhost', port=5001)