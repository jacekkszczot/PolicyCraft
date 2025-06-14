"""
Main Flask application for PolicyCraft - AI Policy Analysis Framework.
FULLY INTEGRATED VERSION with all modules working together.

Author: Jacek Robert Kszczot
Project: MSc AI & Data Science - COM7016
University: Leeds Trinity University
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

# Import configuration
from config import get_config, create_secure_directories

# Import authentication components
from src.auth.models import User, db, init_db
from src.auth.routes import auth_bp

# Import ALL analysis modules - INTEGRATED!
from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.database.operations import DatabaseOperations
from src.visualisation.charts import ChartGenerator
from src.recommendation.engine import RecommendationEngine
from clean_dataset import process_new_upload

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
    Application factory function to create and configure Flask app.
    """
    print("=== CREATING FULLY INTEGRATED POLICYCRAFT APP ===")
    
    # Create secure directories first
    create_secure_directories()
    
    # Initialize Flask application
    app = Flask(__name__, 
               template_folder='src/web/templates',
               static_folder='src/web/static')
    
    # Load configuration from secure config
    config_obj = get_config()
    app.config.from_object(config_obj)
    print(f"DEBUG: App config loaded - SECRET_KEY exists: {'SECRET_KEY' in app.config}")
    
    # Initialize extensions
    db.init_app(app)
    print("DEBUG: Database initialized")
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    print("DEBUG: Flask-Login initialized")
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login session management."""
        print(f"DEBUG: Loading user with ID: {user_id}")
        user = User.query.get(int(user_id))
        print(f"DEBUG: User loaded: {user is not None}")
        return user
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print("DEBUG: Auth blueprint registered")

    # Debug - show all routes
    print("=== ALL ROUTES ===")
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule.rule} -> {rule.endpoint}")
    print("=== END ROUTES ===")
    
    # Make current_user available in all templates
    @app.context_processor
    def inject_current_user():
        """Make current_user available in all templates."""
        return dict(current_user=current_user)
    
    # Initialize database and create tables
    with app.app_context():
        print("DEBUG: Initializing database")
        init_db(app)
        print("DEBUG: Database initialized successfully")
    
    print("=== FLASK APP CREATED SUCCESSFULLY ===")
    return app

# Create Flask app
app = create_app()

# Initialize ALL core components - INTEGRATED SYSTEM!
print("=== INITIALIZING INTEGRATED AI MODULES ===")
text_processor = TextProcessor()
theme_extractor = ThemeExtractor()
policy_classifier = PolicyClassifier()
db_operations = DatabaseOperations()
chart_generator = ChartGenerator()
recommendation_engine = RecommendationEngine()
print("=== ALL AI MODULES INITIALIZED SUCCESSFULLY ===")

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_upload_folder():
    """Create upload folder if it doesn't exist."""
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"Created upload folder: {upload_folder}")

@app.route('/')
def index():
    """Landing page route - shows content for all users."""
    print(f"DEBUG INDEX: current_user.is_authenticated = {current_user.is_authenticated}")
    logger.info("Landing page accessed")
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():
    """Fixed dashboard with proper data serialization."""
    print("=== DASHBOARD FIXED VERSION ===")
    
    try:
        logger.info(f"Dashboard accessed by user: {current_user.username}")
        
        # Get user's analyses with error handling
        try:
            user_analyses = db_operations.get_user_analyses(current_user.id)
            print(f"DEBUG: Retrieved {len(user_analyses)} analyses")
        except Exception as e:
            print(f"ERROR getting analyses: {e}")
            user_analyses = []
        
        # Generate dashboard charts with error handling
        try:
            dashboard_charts = chart_generator.generate_user_dashboard_charts(user_analyses)
            print(f"DEBUG: Generated charts: {list(dashboard_charts.keys()) if dashboard_charts else 'None'}")
        except Exception as e:
            print(f"ERROR generating charts: {e}")
            dashboard_charts = {}
        
        # Calculate user statistics with error handling
        total_policies = len(user_analyses)
        classification_counts = {}
        theme_frequencies = {}
        
        try:
            for analysis in user_analyses:
                # Count classifications
                classification = analysis.get('classification', {})
                if isinstance(classification, dict):
                    cls = classification.get('classification', 'Unknown')
                else:
                    cls = 'Unknown'
                classification_counts[cls] = classification_counts.get(cls, 0) + 1
                
                # Count theme frequencies
                themes = analysis.get('themes', [])
                for theme in themes:
                    if isinstance(theme, dict):
                        theme_name = theme.get('name', 'Unknown')
                    else:
                        theme_name = str(theme)
                    theme_frequencies[theme_name] = theme_frequencies.get(theme_name, 0) + 1
            
            print(f"DEBUG: Classification counts: {classification_counts}")
            print(f"DEBUG: Theme frequencies: {dict(list(theme_frequencies.items())[:5])}")
        except Exception as e:
            print(f"ERROR calculating statistics: {e}")
        
        # Get database statistics with error handling
        try:
            db_stats = db_operations.get_analysis_statistics(current_user.id)
            print(f"DEBUG: DB stats: {db_stats}")
        except Exception as e:
            print(f"ERROR getting DB stats: {e}")
            db_stats = {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}
        
        # FIXED: Prepare serializable user data (no LocalProxy!)
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.get_full_name(),
            'institution': getattr(current_user, 'institution', None),
            'role': getattr(current_user, 'role', 'user')
        }
        
        # FIXED: Convert dates to strings for JSON serialization
        processed_analyses = []
        for analysis in user_analyses:  # Recent analyses
            processed_analysis = analysis.copy()
            
            # Convert datetime objects to strings
            if 'analysis_date' in processed_analysis:
                if hasattr(processed_analysis['analysis_date'], 'strftime'):
                    processed_analysis['analysis_date'] = processed_analysis['analysis_date'].strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(processed_analysis['analysis_date'], str):
                    # Already a string, try to format it nicely
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(processed_analysis['analysis_date'].replace('Z', '+00:00'))
                        processed_analysis['analysis_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass  # Keep original string
            
            processed_analyses.append(processed_analysis)
        
        # Prepare FULLY serializable dashboard data
        dashboard_data = {
            'user': user_data,  # FIXED: Serializable user data
            'total_policies': total_policies,
            'classification_counts': classification_counts,
            'theme_frequencies': theme_frequencies,
            'charts': dashboard_charts,
            'recent_analyses': processed_analyses,  # FIXED: Dates converted to strings
            'statistics': db_stats
        }
        
        print("DEBUG: Dashboard data prepared successfully")
        print(f"DEBUG: Data keys: {list(dashboard_data.keys())}")
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        print(f"CRITICAL ERROR in dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return minimal serializable dashboard data
        minimal_data = {
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.get_full_name()
            },
            'total_policies': 0,
            'classification_counts': {},
            'theme_frequencies': {},
            'charts': {},
            'recent_analyses': [],
            'statistics': {'total_analyses': 0, 'avg_confidence': 0, 'avg_themes_per_analysis': 0}
        }
        
        flash('Dashboard loaded with limited data due to an error.', 'warning')
        return render_template('dashboard.html', data=minimal_data)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """ENHANCED file upload with drag-drop and multi-file support."""
    if request.method == 'GET':
        logger.info(f"Upload page accessed by user: {current_user.username}")
        return render_template('upload.html')
    
    if request.method == 'POST':
        # Handle both single and multiple file uploads
        uploaded_files = request.files.getlist('files[]')  # Multi-file support
        
        # Fallback for single file upload
        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            single_file = request.files.get('file')
            if single_file and single_file.filename != '':
                uploaded_files = [single_file]
        
        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            flash('No files selected', 'error')
            logger.warning(f"Upload attempted without files by user: {current_user.username}")
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
                    processing_result = process_new_upload(file_path, file.filename)
                    if processing_result['success']:  # ← Dodaj 4 spacje wcięcia
                        print(f"✅ Auto-processed: {processing_result['standardized_name']}")
                    else:
                        print(f"⚠️ Processing failed: {processing_result['error']}")

                    successful_uploads.append({
                        'original': file.filename,
                        'unique': unique_filename,
                        'size': os.path.getsize(file_path)
                    })
                    
                    logger.info(f"File uploaded successfully by user {current_user.username}: {unique_filename}")
                    
                except Exception as e:
                    failed_uploads.append({
                        'filename': file.filename,
                        'error': str(e)
                    })
                    logger.error(f"Error uploading file {file.filename} for user {current_user.username}: {str(e)}")
            else:
                failed_uploads.append({
                    'filename': file.filename,
                    'error': 'Invalid file type'
                })
        
        # Provide feedback
        if successful_uploads:
            if len(successful_uploads) == 1:
                flash(f'File uploaded successfully! Starting analysis...', 'success')
                # Redirect to single file analysis
                return redirect(url_for('analyse_document', filename=successful_uploads[0]['unique']))
            else:
                flash(f'{len(successful_uploads)} files uploaded successfully! Starting batch analysis...', 'success')
                # Redirect to batch analysis
                file_list = [f['unique'] for f in successful_uploads]
                return redirect(url_for('batch_analyse', files=','.join(file_list)))
        
        if failed_uploads:
            error_msg = f"{len(failed_uploads)} files failed to upload: " + ", ".join([f['filename'] for f in failed_uploads])
            flash(error_msg, 'error')
        
        if not successful_uploads:
            return redirect(request.url)

@app.route('/batch-analyse/<path:files>')
@login_required
def batch_analyse(files):
    """
    Batch analysis for multiple uploaded files.
    """
    try:
        file_list = files.split(',')
        
        # Security check - ensure all files belong to current user
        for filename in file_list:
            if not filename.startswith(f"{current_user.id}_"):
                flash('Access denied. You can only analyse your own documents.', 'error')
                return redirect(url_for('upload_file'))
        
        logger.info(f"Starting batch analysis of {len(file_list)} files by user: {current_user.username}")
        print(f"=== STARTING BATCH AI PIPELINE FOR {len(file_list)} FILES ===")
        
        batch_results = []
        successful_analyses = 0
        failed_analyses = 0
        
        for i, filename in enumerate(file_list, 1):
            print(f"\n--- Processing file {i}/{len(file_list)}: {filename} ---")
            
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                if not os.path.exists(file_path):
                    print(f"❌ File not found: {filename}")
                    failed_analyses += 1
                    continue
                
                # Run full AI pipeline for each file
                print(f"🔄 Running AI pipeline...")
                
                # Text extraction
                extracted_text = text_processor.extract_text_from_file(file_path)
                if not extracted_text:
                    print(f"❌ Text extraction failed for: {filename}")
                    failed_analyses += 1
                    continue
                
                # Text cleaning
                cleaned_text = text_processor.clean_text(extracted_text)
                
                # Theme extraction
                themes = theme_extractor.extract_themes(cleaned_text)
                
                # Policy classification
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
                charts = chart_generator.generate_analysis_charts(themes, classification)
                
                # Store results
                batch_results.append({
                    'filename': filename,
                    'original_filename': filename.split('_', 2)[-1],  # Remove user_id and timestamp
                    'analysis_id': analysis_id,
                    'themes': themes[:5],  # Top 5 themes for summary
                    'classification': classification,
                    'charts': charts,
                    'text_length': len(cleaned_text),
                    'theme_count': len(themes),
                    'status': 'success'
                })
                
                successful_analyses += 1
                print(f"✅ Analysis completed: {classification['classification']} ({classification['confidence']}%)")
                
            except Exception as e:
                print(f"❌ Error analyzing {filename}: {str(e)}")
                batch_results.append({
                    'filename': filename,
                    'original_filename': filename.split('_', 2)[-1],
                    'status': 'failed',
                    'error': str(e)
                })
                failed_analyses += 1
        
        print(f"\n=== BATCH ANALYSIS COMPLETED ===")
        print(f"✅ Successful: {successful_analyses}")
        print(f"❌ Failed: {failed_analyses}")
        
        # Generate batch summary
        if successful_analyses > 0:
            # Aggregate statistics
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
        
        logger.info(f"Batch analysis completed for user {current_user.username}: {successful_analyses}/{len(file_list)} successful")
        
        return render_template('batch_results.html', {
            'results': batch_results,
            'summary': batch_summary,
            'user': current_user,
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis for user {current_user.username}: {str(e)}")
        flash('Error during batch analysis. Please try again.', 'error')
        return redirect(url_for('upload_file'))

@app.route('/api/upload-progress')
@login_required
def upload_progress():
    """API endpoint for upload progress tracking."""
    # This would require more complex implementation with background tasks
    # For now, return a simple response
    return jsonify({
        'status': 'processing',
        'message': 'Files are being processed...'
    })

@app.route('/analyse/<filename>')
@login_required
def analyse_document(filename):
    """
    FULLY INTEGRATED document analysis pipeline.
    Uses ALL modules: TextProcessor → ThemeExtractor → PolicyClassifier → Database → Charts
    """
    try:
        # Security check
        if not filename.startswith(f"{current_user.id}_"):
            flash('Access denied. You can only analyse your own documents.', 'error')
            logger.warning(f"User {current_user.username} attempted to access file: {filename}")
            return redirect(url_for('upload_file'))
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            logger.error(f"File not found for analysis: {filename}")
            return redirect(url_for('upload_file'))
        
        logger.info(f"Starting INTEGRATED analysis of file: {filename} by user: {current_user.username}")
        print(f"=== STARTING FULL AI PIPELINE FOR {filename} ===")
        
        # STEP 1: Extract text using TextProcessor
        print("STEP 1: Text extraction...")
        extracted_text = text_processor.extract_text_from_file(file_path)
        if not extracted_text:
            flash('Could not extract text from file', 'error')
            logger.error(f"Text extraction failed for: {filename}")
            return redirect(url_for('upload_file'))
        print(f"✅ Text extracted: {len(extracted_text)} characters")
        
        # STEP 2: Clean and preprocess text
        print("STEP 2: Text cleaning...")
        cleaned_text = text_processor.clean_text(extracted_text)
        print(f"✅ Text cleaned: {len(cleaned_text)} characters")
        
        # STEP 3: Extract themes using ThemeExtractor
        print("STEP 3: Theme extraction...")
        themes = theme_extractor.extract_themes(cleaned_text)
        print(f"✅ Themes extracted: {len(themes)} themes found")
        for theme in themes[:3]:
            print(f"   - {theme['name']}: {theme['score']} ({theme['confidence']}%)")
        
        # STEP 4: Classify policy using PolicyClassifier
        print("STEP 4: Policy classification...")
        classification = policy_classifier.classify_policy(cleaned_text)
        print(f"✅ Policy classified: {classification['classification']} ({classification['confidence']}%)")
        
        # STEP 5: Store results in database
        print("STEP 5: Database storage...")
        analysis_id = db_operations.store_user_analysis_results(
            user_id=current_user.id,
            filename=filename,
            original_text=extracted_text,
            cleaned_text=cleaned_text,
            themes=themes,
            classification=classification
        )
        print(f"✅ Analysis stored with ID: {analysis_id}")
        
        # STEP 6: Generate visualizations
        print("STEP 6: Chart generation...")
        charts = chart_generator.generate_analysis_charts(themes, classification)
        print(f"✅ Charts generated: {list(charts.keys())}")
        
        # STEP 7: Prepare comprehensive results
        print("STEP 7: Results preparation...")
        text_stats = text_processor.get_text_statistics(cleaned_text)
        theme_summary = theme_extractor.get_theme_summary(themes)
        classification_details = policy_classifier.get_classification_details(cleaned_text)
        
        logger.info(f"INTEGRATED analysis completed successfully for: {filename} by user: {current_user.username}")
        print(f"=== FULL AI PIPELINE COMPLETED SUCCESSFULLY ===")
        
        # Prepare COMPREHENSIVE results for template
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
                'classification_confidence': classification['confidence'],
                'processing_method': classification['method']
            }
        }
        
        return render_template('results.html', results=results)
        
    except Exception as e:
        logger.error(f"Error during INTEGRATED analysis of {filename} by user {current_user.username}: {str(e)}")
        print(f"ERROR in analysis pipeline: {str(e)}")
        flash('Error analysing document. Please try again.', 'error')
        return redirect(url_for('upload_file'))

@app.route('/recommendations/<analysis_id>')
@login_required
def get_recommendations(analysis_id):
    """
    Generate evidence-based recommendations using advanced recommendation engine.
    Integrates UNESCO (2023), JISC (2023), and BERA (2018) guidelines.
    """
    try:
        # Get the analysis data
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        if not analysis:
            flash('Analysis not found or access denied.', 'error')
            return redirect(url_for('dashboard'))
        
        logger.info(f"Generating advanced recommendations for analysis {analysis_id} by user: {current_user.username}")
        print(f"\n🚀 Starting advanced recommendation generation for {analysis_id}")
        
        # Extract analysis components
        themes = analysis.get('themes', [])
        classification = analysis.get('classification', {})
        
        # Get original text for framework analysis
        text_data = analysis.get('text_data', {})
        cleaned_text = text_data.get('cleaned_text', text_data.get('original_text', ''))
        
        if not cleaned_text:
            flash('Analysis text not found. Cannot generate recommendations.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Generate advanced recommendations using research-grade engine
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
        
        logger.info(f"Generated {recommendation_data['total_recommendations']} advanced recommendations for user {current_user.username}")
        print(f"✅ Advanced recommendation generation completed: {recommendation_data['total_recommendations']} recommendations")
        
        # Store recommendations in database for future reference
        try:
            rec_id = db_operations.store_recommendations(
                user_id=current_user.id,
                analysis_id=analysis_id,
                recommendations=recommendation_package.get('recommendations', [])
            )
            print(f"📝 Recommendations stored with ID: {rec_id}")
        except Exception as e:
            print(f"⚠️ Could not store recommendations: {e}")
            # Continue anyway - recommendations are still generated
        
        return render_template('recommendations.html', data=recommendation_data)
        
    except Exception as e:
        logger.error(f"Error generating advanced recommendations for analysis {analysis_id} by user {current_user.username}: {str(e)}")
        print(f"❌ Error in advanced recommendation generation: {str(e)}")
        
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
                        'description': 'Conduct comprehensive review of AI policy to ensure alignment with current best practices and institutional needs.',
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
            
            flash('Using basic recommendations due to processing error. Please try again later.', 'warning')
            return render_template('recommendations.html', data=basic_data)
            
        except Exception as fallback_error:
            logger.error(f"Fallback recommendation generation also failed: {str(fallback_error)}")
            flash('Error generating recommendations. Please try again.', 'error')
            return redirect(url_for('dashboard'))

@app.route('/api/analysis/<analysis_id>')
@login_required
def api_get_analysis(analysis_id):
    """API endpoint to get analysis results in JSON format."""
    try:
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        if analysis:
            return jsonify({
                'success': True,
                'data': analysis
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Analysis not found or access denied'
            }), 404
            
    except Exception as e:
        logger.error(f"API error for analysis {analysis_id} by user {current_user.username}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/about')
def about():
    """Public about page - accessible without authentication."""
    return render_template('public/about.html')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with custom page."""
    logger.warning(f"404 error: {request.url}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with custom page."""
    logger.error(f"500 error: {str(error)}")
    return render_template('errors/500.html'), 500

@app.before_request
def log_request_info():
    """Log all requests for debugging."""
    print(f"=== REQUEST: {request.method} {request.url} -> endpoint: {request.endpoint} ===")
    if current_user.is_authenticated:
        print(f"=== AUTHENTICATED USER: {current_user.username} ===")
    else:
        print("=== ANONYMOUS USER ===")

if __name__ == '__main__':
    """Run the FULLY INTEGRATED PolicyCraft application."""
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    create_upload_folder()
    
    logger.info("Starting FULLY INTEGRATED PolicyCraft Application")
    print("🚀 PolicyCraft starting with FULL AI INTEGRATION on: http://localhost:5001")
    print("🤖 All modules loaded: TextProcessor, ThemeExtractor, PolicyClassifier, Database, Charts, RecommendationEngine")
    print("🔧 Use ONLY this address to avoid session issues!")
    print("="*80)
    
    # Run the application
    app.run(debug=True, host='localhost', port=5001)