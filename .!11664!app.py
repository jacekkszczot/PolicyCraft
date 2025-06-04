"""
Main Flask application for PolicyCraft - AI Policy Analysis Framework.

This application provides a secure web interface for analysing university AI policies,
extracting themes, and generating policy recommendations with user authentication.

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

# Import authentication components
from src.auth.models import User, db, init_db
from src.auth.routes import auth_bp

# Import analysis modules
from src.nlp.text_processor import TextProcessor
from src.nlp.theme_extractor import ThemeExtractor
from src.nlp.policy_classifier import PolicyClassifier
from src.database.operations import DatabaseOperations
from src.recommendation.engine import RecommendationEngine
from src.visualisation.charts import ChartGenerator

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
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Initialize Flask application
    app = Flask(__name__, 
               template_folder='src/web/templates',
               static_folder='src/web/static')
    
    # Application configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['UPLOAD_FOLDER'] = 'data/policies/pdf_originals'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt', 'docx'}
    
    # Database configuration
    from config import get_config
    config_obj = get_config()
    app.config.from_object(config_obj)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
    app.register_blueprint(auth_bp)
    
    # Make current_user available in all templates
    @app.context_processor
    def inject_current_user():
        """Make current_user available in all templates."""
        return dict(current_user=current_user)
    
    # Initialize database and create tables
    with app.app_context():
        init_db(app)
    
    return app

# Create Flask app
app = create_app()

# Initialize core components
text_processor = TextProcessor()
theme_extractor = ThemeExtractor()
policy_classifier = PolicyClassifier()
db_operations = DatabaseOperations()
recommendation_engine = RecommendationEngine()
chart_generator = ChartGenerator()

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_upload_folder():
    """
    Create upload folder if it doesn't exist.
    Ensures the application can save uploaded files.
    """
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"Created upload folder: {upload_folder}")

@app.route('/')
def index():
    """Landing page route - shows content for all users."""
    logger.info("Landing page accessed")
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard - main page after login.
    Shows user's analyses and comparative insights.
    
    Returns:
        str: Rendered HTML template for dashboard
    """
    try:
        logger.info(f"Dashboard accessed by user: {current_user.username}")
        
        # Get user's analyses from database
        user_analyses = db_operations.get_user_analyses(current_user.id)
        
        # Generate dashboard charts for user's data
        dashboard_charts = chart_generator.generate_user_dashboard_charts(user_analyses)
        
        # Calculate user statistics
        total_policies = len(user_analyses)
        classification_counts = {}
        theme_frequencies = {}
        
        for analysis in user_analyses:
            # Count classifications
            classification = analysis.get('classification', 'Unknown')
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
            
            # Count theme frequencies
            themes = analysis.get('themes', [])
            for theme in themes:
                theme_frequencies[theme] = theme_frequencies.get(theme, 0) + 1
        
        dashboard_data = {
            'user': current_user,
            'total_policies': total_policies,
            'classification_counts': classification_counts,
            'theme_frequencies': theme_frequencies,
            'charts': dashboard_charts,
            'recent_analyses': user_analyses[-5:] if user_analyses else []  # Last 5 analyses
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error loading dashboard for user {current_user.username}: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """
    Handle file upload functionality - requires authentication.
    GET: Display upload form
    POST: Process uploaded policy document
    
    Returns:
        str: Rendered HTML template or redirect to results page
    """
    if request.method == 'GET':
        logger.info(f"Upload page accessed by user: {current_user.username}")
        return render_template('upload.html')
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            logger.warning(f"Upload attempted without file by user: {current_user.username}")
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            flash('No file selected', 'error')
            logger.warning(f"Upload attempted with empty filename by user: {current_user.username}")
            return redirect(request.url)
        
        # Process valid file upload
        if file and allowed_file(file.filename):
            try:
                # Secure the filename and save file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                unique_filename = f"{current_user.id}_{timestamp}{filename}"
                
                create_upload_folder()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                logger.info(f"File uploaded successfully by user {current_user.username}: {unique_filename}")
                flash('File uploaded successfully!', 'success')
                
                # Redirect to analysis with the filename
                return redirect(url_for('analyse_document', filename=unique_filename))
                
            except Exception as e:
                logger.error(f"Error uploading file for user {current_user.username}: {str(e)}")
                flash('Error uploading file. Please try again.', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload PDF, TXT, or DOCX files.', 'error')
            logger.warning(f"Invalid file type uploaded by user {current_user.username}: {file.filename}")
            return redirect(request.url)

@app.route('/analyse/<filename>')
@login_required
def analyse_document(filename):
    """
    Analyse uploaded policy document and display results.
    Processes the document through NLP pipeline and stores results.
    
    Args:
        filename (str): Name of the uploaded file to analyse
        
    Returns:
        str: Rendered HTML template with analysis results
    """
    try:
        # Verify file belongs to current user (security check)
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
        
        logger.info(f"Starting analysis of file: {filename} by user: {current_user.username}")
        
        # Step 1: Extract text from document
        extracted_text = text_processor.extract_text_from_file(file_path)
        if not extracted_text:
            flash('Could not extract text from file', 'error')
            logger.error(f"Text extraction failed for: {filename}")
            return redirect(url_for('upload_file'))
        
        # Step 2: Clean and preprocess text
        cleaned_text = text_processor.clean_text(extracted_text)
        
        # Step 3: Extract themes from policy
        themes = theme_extractor.extract_themes(cleaned_text)
        
        # Step 4: Classify policy approach
        classification = policy_classifier.classify_policy(cleaned_text)
        
        # Step 5: Store results in database with user association
        analysis_id = db_operations.store_user_analysis_results(
            user_id=current_user.id,
            filename=filename,
            original_text=extracted_text,
            cleaned_text=cleaned_text,
            themes=themes,
            classification=classification
        )
        
        # Step 6: Generate visualisations
        charts = chart_generator.generate_analysis_charts(themes, classification)
        
        logger.info(f"Analysis completed successfully for: {filename} by user: {current_user.username}")
        
        # Prepare results for template
        results = {
            'filename': filename,
            'analysis_id': analysis_id,
            'themes': themes,
            'classification': classification,
            'charts': charts,
            'text_length': len(cleaned_text),
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user': current_user
        }
        
        return render_template('results.html', results=results)
        
    except Exception as e:
        logger.error(f"Error during analysis of {filename} by user {current_user.username}: {str(e)}")
        flash('Error analysing document. Please try again.', 'error')
        return redirect(url_for('upload_file'))

@app.route('/recommendations/<analysis_id>')
@login_required
def get_recommendations(analysis_id):
    """
    Generate policy recommendations based on analysis results.
    
    Args:
        analysis_id (str): ID of the analysis to generate recommendations for
        
    Returns:
        str: Rendered HTML template with recommendations
    """
    try:
        logger.info(f"Generating recommendations for analysis: {analysis_id} by user: {current_user.username}")
        
        # Get analysis results from database
        analysis = db_operations.get_user_analysis_by_id(current_user.id, analysis_id)
        if not analysis:
            flash('Analysis not found or access denied', 'error')
            logger.error(f"Analysis not found or access denied: {analysis_id} for user: {current_user.username}")
            return redirect(url_for('dashboard'))
        
        # Generate recommendations based on analysis
        recommendations = recommendation_engine.generate_recommendations(
            themes=analysis['themes'],
            classification=analysis['classification'],
            context=analysis.get('context', {}),
            user_profile={
                'institution': current_user.institution,
                'role': current_user.role
            }
        )
        
        recommendation_data = {
            'analysis': analysis,
            'recommendations': recommendations,
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user': current_user
        }
        
        return render_template('recommendations.html', data=recommendation_data)
        
    except Exception as e:
        logger.error(f"Error generating recommendations for user {current_user.username}: {str(e)}")
        flash('Error generating recommendations. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/analysis/<analysis_id>')
@login_required
def api_get_analysis(analysis_id):
    """
    API endpoint to get analysis results in JSON format.
    
    Args:
        analysis_id (str): ID of the analysis to retrieve
        
    Returns:
        JSON: Analysis results or error message
    """
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
    """
    Handle 404 errors with custom page.
    
    Args:
        error: The 404 error object
        
    Returns:
        str: Rendered 404 error page
    """
    logger.warning(f"404 error: {request.url}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors with custom page.
    
    Args:
        error: The 500 error object
        
    Returns:
        str: Rendered 500 error page
    """
    logger.error(f"500 error: {str(error)}")
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    """
    Run the Flask application in debug mode for development.
    """
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/database', exist_ok=True)
    create_upload_folder()
    
    logger.info("Starting PolicyCraft Application with Authentication")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)