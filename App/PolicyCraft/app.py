"""
Main Flask application for PolicyCraft - AI Policy Analysis Framework.
Clean version without onboarding features.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.database.mongo_operations import MongoOperations as DatabaseOperations
from src.visualisation.charts import ChartGenerator
from src.recommendation.engine import RecommendationEngine
from src.scripts.clean_dataset import process_new_upload


def clean_baseline_filename(filename):
    """Remove [BASELINE] prefix and clean filename for display"""
    if filename.startswith("[BASELINE] "):
        clean_name = filename.replace("[BASELINE] ", "")
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
    clean_name = clean_name.replace('.pdf', '').replace('.docx', '').replace('.doc', '').replace('.txt', '')
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
        return 'Cambridge University'
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
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        else:
            dt = date_str
        return dt.strftime('%d/%m/%Y')
    except Exception as e:
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
    
    # Initialize Flask application
    app = Flask(__name__, 
               template_folder='src/web/templates',
               static_folder='src/web/static')
    
    # Load configuration
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # Initialize extensions
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
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    
    # Make current_user available in all templates
    @app.context_processor
    def inject_current_user():
        """Make current_user available in all templates."""
        return {'current_user': current_user}
    
    # Initialize database and create tables
    with app.app_context():
        init_db(app)
    
    return app

# Create Flask app and initialize modules
app = create_app()

# Initialize CSRF protection
csrf = CSRFProtect(app)

text_processor = TextProcessor()
theme_extractor = ThemeExtractor()
policy_classifier = PolicyClassifier()
db_operations = DatabaseOperations(uri="mongodb://localhost:27017", db_name="policycraft")
chart_generator = ChartGenerator()
recommendation_engine = RecommendationEngine()


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

@app.route('/')
def index():
    """
    Landing page route for PolicyCraft application.
    
    Displays the main homepage with application overview
    and navigation options for users.
    """
    logger.info("Landing page accessed")
    return render_template("index.html")

def _to_epoch(val):
    """Convert supported date formats to POSIX timestamp for consistent sorting."""
    try:
        if isinstance(val, datetime):
            return val.replace(tzinfo=None).timestamp()
        if isinstance(val, str):
            dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None).timestamp()
    except Exception:
        pass
    return 0

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

def _process_analyses_for_display(analyses):
    """Process analyses for display by converting dates and preparing data."""
    processed = []
    for analysis in analyses:
        processed_analysis = analysis.copy()
        if 'analysis_date' in processed_analysis:
            if hasattr(processed_analysis['analysis_date'], 'strftime'):
                processed_analysis['analysis_date'] = processed_analysis['analysis_date'].strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(processed_analysis['analysis_date'], str):
                try:
                    dt = datetime.fromisoformat(processed_analysis['analysis_date'].replace('Z', '+00:00'))
                    processed_analysis['analysis_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
        processed.append(processed_analysis)
    return processed

def _calculate_analytics(analyses):
    """Calculate analytics (classifications and themes) from analyses."""
    classification_counts = {}
    theme_frequencies = {}
    
    for analysis in analyses:
        # Count classifications
        classification = analysis.get('classification', {})
        cls = classification.get('classification', 'Unknown') if isinstance(classification, dict) else 'Unknown'
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
        
        # Count theme frequencies
        themes = analysis.get('themes', [])
        for theme in themes:
            theme_name = theme.get('name', 'Unknown') if isinstance(theme, dict) else str(theme)
            theme_frequencies[theme_name] = theme_frequencies.get(theme_name, 0) + 1
    
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
        
        # Merge analyses with user versions taking precedence
        analyses_by_filename = {a['filename']: a for a in baseline_analyses}
        analyses_by_filename.update({a['filename']: a for a in user_analyses})
        combined_analyses = list(analyses_by_filename.values())
        
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

def _load_sample_policies_if_needed(user_analyses):
    """Load sample policies if user has none."""
    if not any(a.get('filename','').startswith('[BASELINE]') for a in user_analyses):
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
    
    # Calculate analytics
    classification_counts, theme_frequencies = _calculate_analytics(combined_analyses)
    
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
    processed_analyses = _process_analyses_for_display(combined_analyses)
    
    return {
        'user': user_data,
        'total_policies': len(combined_analyses),
        'classification_counts': classification_counts,
        'theme_frequencies': theme_frequencies,
        'charts': dashboard_charts,
        'recent_analyses': processed_analyses,
        'statistics': db_stats
    }

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
    uploaded_files = request.files.getlist('files[]')
    
    # Fallback for single file upload
    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        single_file = request.files.get('file')
        if single_file and single_file.filename != '':
            uploaded_files = [single_file]
    
    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        flash('No files selected', 'error')
        return redirect(request.url)
    
    # Check file limit
    if len(uploaded_files) > app.config.get('MAX_FILES_PER_UPLOAD', 10):
        flash(f'Too many files. Maximum {app.config.get("MAX_FILES_PER_UPLOAD", 10)} files allowed.', 'error')
        return redirect(request.url)
    
    successful_uploads = []
    failed_uploads = []
    
    # Process each file
    for file in uploaded_files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            try:
                # Secure the filename and save file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                unique_filename = f"{current_user.id}_{timestamp}{filename}"
                
                create_upload_folder()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Process uploaded file
                processing_result = process_new_upload(file_path, file.filename)
                if processing_result['success']:
                    logger.info(f"Auto-processed: {processing_result['standardized_name']}")
                else:
                    logger.warning(f"Processing failed: {processing_result['error']}")

                successful_uploads.append({
                    'original': file.filename,
                    'unique': unique_filename,
                    'size': os.path.getsize(file_path)
                })
                
                logger.info(f"File uploaded successfully: {unique_filename}")
                
            except Exception as e:
                failed_uploads.append({
                    'filename': file.filename,
                    'error': str(e)
                })
                logger.error(f"Error uploading file {file.filename}: {str(e)}")
        else:
            failed_uploads.append({
                'filename': file.filename,
                'error': 'Invalid file type'
            })
    
    # Provide feedback
    if successful_uploads:
        if len(successful_uploads) == 1:
            flash(f'File uploaded successfully! Starting analysis...', 'success')
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
        file_list = files.split(',')
        
        # Security check
        for filename in file_list:
            if not filename.startswith(f"{current_user.id}_"):
                flash('Access denied. You can only analyse your own documents.', 'error')
                return redirect(url_for('upload_file'))
        
        logger.info(f"Starting batch analysis of {len(file_list)} files")
        
        batch_results = []
        successful_analyses = 0
        failed_analyses = 0
        
        for i, filename in enumerate(file_list, 1):
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                if not os.path.exists(file_path):
                    failed_analyses += 1
                    continue
                
                # Run AI pipeline
                extracted_text = text_processor.extract_text_from_file(file_path)
                if not extracted_text:
                    failed_analyses += 1
                    continue
                
                cleaned_text = text_processor.clean_text(extracted_text)
                themes = theme_extractor.extract_themes(cleaned_text)
                classification = policy_classifier.classify_policy(cleaned_text)
                
                # Store in database
                analysis_id = db_operations.store_user_analysis_results(
                    user_id=current_user.id,
                    filename=filename,
                    original_text=extracted_text,
                    cleaned_text=cleaned_text,
                    themes=themes,
                    classification=classification
                )
                
                # Generate charts
                charts = chart_generator.generate_analysis_charts(themes, classification, cleaned_text)
                
                batch_results.append({
                    'filename': filename,
                    'original_filename': filename.split('_', 2)[-1],
                    'analysis_id': analysis_id,
                    'themes': themes[:5],
                    'classification': classification,
                    'charts': charts,
                    'text_length': len(cleaned_text),
                    'theme_count': len(themes),
                    'status': 'success'
                })
                
                successful_analyses += 1
                
            except Exception as e:
                logger.error(f"Error analyzing {filename}: {str(e)}")
                batch_results.append({
                    'filename': filename,
                    'original_filename': filename.split('_', 2)[-1],
                    'status': 'failed',
                    'error': str(e)
                })
                failed_analyses += 1
        
        # Generate batch summary
        if successful_analyses > 0:
            all_classifications = [r['classification']['classification'] for r in batch_results if r['status'] == 'success']
            classification_summary = {cls: all_classifications.count(cls) for cls in set(all_classifications)}
            
            all_themes = []
            for result in batch_results:
                if result['status'] == 'success':
                    all_themes.extend([theme['name'] for theme in result['themes']])
            
            from collections import Counter
            theme_summary = dict(Counter(all_themes).most_common(10))
            
            batch_summary = {
                'total_files': len(file_list),
                'successful': successful_analyses,
                'failed': failed_analyses,
                'classification_summary': classification_summary,
                'theme_summary': theme_summary,
                'avg_confidence': sum([r['classification']['confidence'] for r in batch_results if r['status'] == 'success']) / successful_analyses if successful_analyses > 0 else 0
            }
        else:
            batch_summary = {
                'total_files': len(file_list),
                'successful': 0,
                'failed': failed_analyses,
                'classification_summary': {},
                'theme_summary': {},
                'avg_confidence': 0
            }
        
        logger.info(f"Batch analysis completed: {successful_analyses}/{len(file_list)} successful")
        
        return render_template('batch_results.html', {
            'results': batch_results,
            'summary': batch_summary,
            'user': current_user,
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        flash('Error during batch analysis. Please try again.', 'error')
        return redirect(url_for('upload_file'))

@app.route('/analyse/<filename>')
@login_required
def analyse_document(filename):
    """
    Document analysis pipeline for individual policy files.
    
    Processes a single document through the complete AI analysis workflow
    including text extraction, theme analysis, and policy classification.
    """
    try:
        is_baseline = filename.startswith('[BASELINE]')
        
        # Security check - allow baseline files or user's own files
        if not (is_baseline or filename.startswith(f"{current_user.id}_")):
            flash('Access denied. You can only analyse your own documents or baseline policies.', 'error')
            return redirect(url_for('upload_file'))
        
        # Determine the correct file path
        if is_baseline:
            # Extract original filename from the formatted baseline name
            original_filename = filename.split(' - ')[-1] if ' - ' in filename else filename.replace('[BASELINE] ', '')
            file_path = os.path.join('data', 'policies', 'clean_dataset', original_filename)
        else:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('upload_file'))
        
        logger.info(f"Starting analysis of file: {filename}")
        
        # Check if analysis already exists to avoid duplication
        existing_analysis = db_operations.get_analysis_by_filename(current_user.id, filename)
        if not existing_analysis and is_baseline:
            # For baseline, check global baseline record (user_id = -1)
            existing_analysis = db_operations.get_analysis_by_filename(-1, filename)
        if existing_analysis:
            themes = existing_analysis.get('themes', [])
            classification = existing_analysis.get('classification', {})
            cleaned_text = existing_analysis.get('text_data', {}).get('cleaned_text', '')
            extracted_text = existing_analysis.get('text_data', {}).get('original_text', '')
            analysis_id = str(existing_analysis['_id'])
        else:
            # Extract and process text
            extracted_text = text_processor.extract_text_from_file(file_path)
            if not extracted_text:
                flash('Could not extract text from file', 'error')
                return redirect(url_for('upload_file'))
            
            cleaned_text = text_processor.clean_text(extracted_text)
            themes = theme_extractor.extract_themes(cleaned_text)
            classification = policy_classifier.classify_policy(cleaned_text)
            
            # Store results in database (handles update if exists)
            analysis_id = db_operations.store_user_analysis_results(
                user_id=current_user.id,
                filename=filename,
                original_text=extracted_text,
                cleaned_text=cleaned_text,
                themes=themes,
                classification=classification,
                username=getattr(current_user, 'username', None)
            )
        
        # Generate visualizations
        charts = chart_generator.generate_analysis_charts(themes, classification, cleaned_text)
        
        # Prepare comprehensive results
        text_stats = text_processor.get_text_statistics(cleaned_text)
        theme_summary = theme_extractor.get_theme_summary(themes)
        classification_details = policy_classifier.get_classification_details(cleaned_text)
        
        logger.info(f"Analysis completed successfully for: {filename}")
        
        results = {
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
                'original_length': len(extracted_text),
                'cleaned_length': len(cleaned_text),
                'themes_found': len(themes),
                'classification_confidence': classification.get('confidence', 0),
                'processing_method': classification.get('method', 'N/A')
            }
        }
        
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
        return jsonify({"error": "Analysis not found"}), 404
    recs = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)
    if not recs:
        # fallback: any user_id
        any_doc = db_operations.recommendations.find_one({"analysis_id": analysis_id})
        if any_doc:
            recs = any_doc.get("recommendations", [])
        else:
            # As a last resort, generate recommendations on the fly for validation
            themes = analysis.get('themes', [])
            classification = analysis.get('classification', {})
            text_data = analysis.get('text_data', {})
            cleaned_text = text_data.get('cleaned_text', text_data.get('original_text', ''))
            rec_package = recommendation_engine.generate_recommendations(
                themes=themes,
                classification=classification,
                text=cleaned_text,
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
        logger.info(f"=== Starting recommendation generation ===")
        logger.info(f"User ID: {current_user.id}, Username: {getattr(current_user, 'username', 'N/A')}")
        logger.info(f"Analysis ID: {analysis_id}")
        
        # Get the analysis data (try by user id, fallback to global and verify ownership)
        logger.info("Attempting to get user's analysis...")
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        
        if analysis:
            logger.info("Found analysis in user's analyses")
            logger.info(f"Analysis details - User ID: {analysis.get('user_id')}, Is Baseline: {analysis.get('is_baseline', False)}")
        else:
            logger.warning(f"Analysis not found in user's analyses, trying global lookup...")
            analysis = db_operations.get_analysis_by_id(analysis_id)
            
            if analysis:
                logger.info("Found analysis in global collection")
                logger.info(f"Analysis details - ID: {analysis.get('_id')}")
                logger.info(f"Analysis owner: User ID: {analysis.get('user_id')}, Username: {analysis.get('username')}")
                logger.info(f"Is baseline: {analysis.get('is_baseline', False)}")
                
                # Tymczasowe wyłączenie sprawdzania uprawnień do testów
                logger.warning("Temporary disabling permission checks for testing")
                logger.info(f"Analysis user_id: {analysis.get('user_id')}, Current user ID: {current_user.id}")
                logger.info(f"Analysis username: {analysis.get('username')}, Current username: {getattr(current_user, 'username', 'N/A')}")
                
                # Tymczasowo zezwalaj na dostęp do wszystkich analiz
                # TODO: Przywrócić sprawdzanie uprawnień po zakończeniu testów
                # is_baseline = analysis.get('is_baseline', False)
                # is_owner = (
                #     str(analysis.get('user_id')) in [str(current_user.id), 'None', ''] or 
                #     str(analysis.get('username')) == str(getattr(current_user, 'username', ''))
                # )
                # 
                # logger.info(f"Access check - is_baseline: {is_baseline}, is_owner: {is_owner}")
                # 
                # if not (is_baseline or is_owner):
                #     logger.error(f"Access denied for user {current_user.id} to analysis {analysis_id}")
                #     logger.error(f"User ID match: {str(analysis.get('user_id')) == str(current_user.id)}")
                #     logger.error(f"Username match: {str(analysis.get('username')) == str(getattr(current_user, 'username', ''))}")
                #     flash('You do not have permission to view this analysis.', 'error')
                #     return redirect(url_for('dashboard'))
            else:
                logger.error(f"Analysis {analysis_id} not found in global lookup")
                flash('Analysis not found.', 'error')
                return redirect(url_for('dashboard'))
        
        logger.info(f"Found analysis data for ID: {analysis_id}")
        
        # Extract analysis components with logging
        themes = analysis.get('themes', [])
        classification = analysis.get('classification', {})
        text_data = analysis.get('text_data', {})
        cleaned_text = text_data.get('cleaned_text', text_data.get('original_text', ''))
        
        logger.info(f"Extracted data - Themes: {len(themes)}, Classification: {classification}")
        logger.info(f"Text data length: {len(cleaned_text) if cleaned_text else 0} chars")
        
        if not cleaned_text:
            logger.error("No text content found in analysis to generate recommendations")
            flash('Analysis text not found. Cannot generate recommendations.', 'warning')
            return redirect(url_for('dashboard'))
        
        if not cleaned_text:
            flash('Analysis text not found. Cannot generate recommendations.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Try to load stored recommendations first
        stored_recs = db_operations.get_recommendations_by_analysis(current_user.id, analysis_id)
        if stored_recs:
            recommendation_package = {
                'recommendations': stored_recs,
                'analysis_metadata': {
                    'generated_date': analysis.get('analysis_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    'methodology': 'Previously generated'
                }
            }
        else:
            # Generate new recommendations
            recommendation_package = recommendation_engine.generate_recommendations(
                themes=themes,
                classification=classification,
                text=cleaned_text,
                analysis_id=analysis_id
            )
        
        # Prepare data for template
        recommendation_data = {
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
        
        logger.info(f"Generated {recommendation_data['total_recommendations']} recommendations")
        
        # Store recommendations in database
        try:
            rec_id = db_operations.store_recommendations(
                user_id=current_user.id,
                analysis_id=analysis_id,
                recommendations=recommendation_package.get('recommendations', [])
            )
            logger.info(f"Recommendations stored with ID: {rec_id}")
        except Exception as e:
            logger.warning(f"Could not store recommendations: {e}")
        
        return render_template('recommendations.html', data=recommendation_data)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        
        # Fallback to basic recommendations
        try:
            basic_data = {
                'analysis': {
                    'filename': analysis.get('filename', 'Unknown'),
                    'classification': analysis.get('classification', {}).get('classification', 'Unknown'),
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
            flash('Analysis not found or access denied.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if it's a baseline policy (protect from deletion)
        filename = analysis.get('filename', '')
        if filename.startswith('[BASELINE]'):
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
    db_ops = DatabaseOperations(uri="mongodb://localhost:27017", db_name="policycraft")
    analysis = db_ops.get_analysis_by_id(analysis_id)
    if not analysis or analysis.get('user_id') != current_user.id:
        return jsonify({'error': 'Analysis not found'}), 404

    cleaned_text = analysis.get('text_data', {}).get('cleaned_text', '')
    if not cleaned_text:
        return jsonify({'error': 'No cleaned text available'}), 400

    classifier = PolicyClassifier()
    keywords = classifier.explain_classification(cleaned_text, top_n=15)
    result = [{"term": kw, "category": cat, "score": score} for kw, cat, score in keywords]
    return jsonify({'analysis_id': analysis_id, 'keywords': result})

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
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
    except Exception as e:
        logger.error(f"API error for analysis {analysis_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Public routes

@app.route('/about')
def about():
    """
    Public about page with application information.
    
    Displays information about PolicyCraft, its purpose,
    and academic research context.
    """
    return render_template('public/about.html')

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

# Register template filters
app.jinja_env.filters["clean_university_name"] = clean_university_name
app.jinja_env.filters["clean_filename"] = clean_filename
app.jinja_env.filters["format_british_date"] = format_british_date

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
                # Robust baseline detection check if ANY analysis filename starts with [BASELINE]
                try:
                    user_analyses = db_operations.get_user_analyses(user_id)
                    baseline_exists = any(a.get('filename', '').startswith('[BASELINE]') for a in user_analyses)
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
    print("PolicyCraft starting at: http://localhost:5001")
    
    app.run(debug=True, host='localhost', port=5001)