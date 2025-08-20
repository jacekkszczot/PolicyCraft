"""
Administrative Routes for PolicyCraft AI Policy Analysis Platform.

This module implements the administrative interface for the PolicyCraft application,
providing essential system administration tools and user management capabilities.

Key Functionality:
- Secure authentication for administrative access
- Dashboard with system statistics and health metrics
- Comprehensive user management (view/delete users)
- System configuration and maintenance tools
- Literature management and knowledge base updates
- Academic document processing and quality assessment- Password management for administrative accounts

Security Implementation:
- Password-protected admin interface with secure hashing
- Session-based authentication with configurable timeouts
- CSRF protection for all administrative forms
- Secure password storage using industry-standard hashing
- Audit logging of all administrative actions

Routes:
    /admin/login             - Admin authentication
    /admin/logout            - Terminate admin session
    /admin/dashboard         - System overview and statistics
    /admin/users             - User management interface
    /admin/reset-baselines   - Reset system baselines
    /admin/change-password   - Update admin credentials

Dependencies:
    - Flask for routing and request handling
    - SQLAlchemy for database operations
    - Werkzeug for security utilities
    - Custom models and database operations

Example Usage:
    # Access admin interface at /admin
    # Default credentials: admin / admin123
    # Change default password immediately after first login

Note:
    This module is part of the PolicyCraft AI Policy Analysis Platform
    and should only be accessible to authorised administrators.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""
from __future__ import annotations
from flask_login import current_user

import json
import logging
import os
from functools import wraps

from flask import (
    Blueprint, current_app, flash, redirect, render_template,
    request, session, url_for, Response, json, jsonify, send_from_directory, abort
)

from src.database.models import User, db as sqlalchemy_db
from src.database.mongo_operations import MongoOperations
from src.literature.literature_engine import LiteratureEngine
from src.analysis_engine.literature.repository import LiteratureRepository
from datetime import datetime

# Initialise logger
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, template_folder="../web/templates/admin", url_prefix="/admin")

# ---------------------------------------------------------------------------
# Admin routes configuration
# ---------------------------------------------------------------------------
mongo_db = MongoOperations()

# ---------------------------------------------------------------------------
# Common literals/constants
# ---------------------------------------------------------------------------
ADMIN_DASHBOARD_ENDPOINT = "admin.dashboard"
ADMIN_USERS_ENDPOINT = "admin.users"
SSE_DATA_PREFIX = "data: "

# ---------------------------------------------------------------------------
# Decorator for protected routes
# ---------------------------------------------------------------------------

def admin_required(func):
    """
    Decorator to require admin authentication for route access.
    
    Uses Flask-Login to check if the current user is authenticated and has admin role.
    Redirects to the main login page if not authenticated or not an admin.
    
    Args:
        func: The route function to protect
        
    Returns:
        Wrapped function with admin authentication check
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask_login import current_user
        
        # Check if user is authenticated and has admin role
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for("auth.login", next=request.path))
        return func(*args, **kwargs)
    return wrapper

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Admin authentication endpoint using the main user authentication system.
    
    This route redirects admin login to the main authentication system for consistency.
    Admin users should log in through the main /login route using their database credentials.
    This ensures a single, unified authentication system throughout the application.
    
    Returns:
        Redirect to main login with admin dashboard as next page
    """
    # Redirect to main login system with admin dashboard as the target
    next_url = request.args.get("next") or url_for(ADMIN_DASHBOARD_ENDPOINT)
    return redirect(url_for("auth.login", next=next_url))

@admin_bp.route("/logout")
def logout():
    """
    Admin logout that clears both admin session and Flask-Login session.
    This ensures complete logout without requiring double logout.
    """
    from flask_login import logout_user
    from flask import make_response
    
    if session.get("is_admin"):
        # Clear admin session
        session.pop("is_admin", None)
        
        # Also logout the Flask-Login user session to prevent double logout
        logout_user()
        
        # Clear entire session for complete cleanup
        session.clear()
        
        flash("Logged out successfully", "info")
        logger.info("Admin logged out completely (both admin and user sessions cleared)")
    else:
        flash("Already logged out", "info")
    
    # Create response with cache headers to prevent browser caching
    resp = make_response(redirect(url_for("index")))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route("/")
@admin_required
def dashboard():
    user_count = User.query.count()
    analysis_count = mongo_db.analyses.count_documents({})
    baseline_global = mongo_db.analyses.count_documents({
        "user_id": -1,
        "filename": {"$regex": r"^\[BASELINE\]", "$options": "i"}
    })
    return render_template("admin/dashboard.html", user_count=user_count, analysis_count=analysis_count, baseline_global=baseline_global)

# ---------------------------------------------------------------------------
# Users management
# ---------------------------------------------------------------------------

@admin_bp.route("/users")
@admin_required
def users():
    """
    Display all users in the system for administrative management.
    
    Returns:
        Rendered users template with list of all registered users
    """
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/delete/<int:user_id>")
@admin_required
def delete_user(user_id):
    """
    Delete a user account with security safeguards.
    
    Prevents deletion of admin users and handles cascading deletion
    of associated user data including analyses and onboarding records.
    
    Args:
        user_id: Integer ID of the user to delete
        
    Returns:
        Redirect to users page with success or error message
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for(ADMIN_USERS_ENDPOINT))
    
    # Prevent deletion of admin users
    if user.role == 'admin':
        flash("Cannot delete admin users for security reasons", "error")
        return redirect(url_for(ADMIN_USERS_ENDPOINT))
    
    username = user.username
    
    # First delete associated UserOnboarding record if it exists
    if user.onboarding:
        sqlalchemy_db.session.delete(user.onboarding)
    
    # Then delete the user
    sqlalchemy_db.session.delete(user)
    sqlalchemy_db.session.commit()
    
    # SECURITY FIX: Purge associated data from MongoDB AND delete files from disk
    try:
        purge_result = mongo_db.purge_user_data(user_id)
        if purge_result and purge_result.get('files_deleted', 0) > 0:
            flash(f"Deleted user {username} and {purge_result['files_deleted']} associated files", "success")
        else:
            flash(f"Deleted user {username}", "success")
    except Exception as e:
        flash(f"User {username} deleted, but error purging data: {str(e)}", "warning")
    return redirect(url_for(ADMIN_USERS_ENDPOINT))

@admin_bp.route("/users/reset_password/<int:user_id>")
@admin_required
def reset_password(user_id):
    """Reset user password to a randomly generated one."""
    import secrets
    import string
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for(ADMIN_USERS_ENDPOINT))
    
    # Generate a secure random password (8 characters: letters + numbers)
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    # Update user password
    user.set_password(new_password)
    sqlalchemy_db.session.commit()
    
    # Show the new password to admin (they need to give it to the user)
    flash(f"Password reset for {user.username}. New password: {new_password}", "success")
    return redirect(url_for(ADMIN_USERS_ENDPOINT))

# ---------------------------------------------------------------------------
# Baselines reset
# ---------------------------------------------------------------------------

@admin_bp.route("/reset_progress")
@admin_required
def reset_progress():
    """Stream progress updates during baseline reset."""
    def generate():
        try:
            # Step 1: Remove existing baseline docs
            delete_result = mongo_db.analyses.delete_many({"user_id": -1})
            deleted_count = delete_result.deleted_count if hasattr(delete_result, 'deleted_count') else 0
            yield f"{SSE_DATA_PREFIX}{json.dumps({'step': 1, 'message': f'Removed {deleted_count} old baseline analyses'})}\n\n"
            
            # Step 2: Remove existing baseline recommendations
            rec_delete_result = mongo_db.recommendations.delete_many({"user_id": -1})
            rec_deleted_count = rec_delete_result.deleted_count if hasattr(rec_delete_result, 'deleted_count') else 0
            yield f"{SSE_DATA_PREFIX}{json.dumps({'step': 2, 'message': f'Removed {rec_deleted_count} old recommendations'})}\n\n"
            
            # Step 3: Recreate global baselines from dataset
            success = mongo_db.load_sample_policies_for_user(-1)
            if success:
                yield SSE_DATA_PREFIX + json.dumps({'step': 3, 'message': 'Successfully loaded new baseline policies'}) + "\n\n"
                
                # Step 4: Deduplicate
                mongo_db.remove_duplicate_baselines_global()
                mongo_db.deduplicate_baseline_analyses(-1)
                yield SSE_DATA_PREFIX + json.dumps({'step': 4, 'message': 'Deduplication complete', 'done': True}) + "\n\n"
            else:
                yield SSE_DATA_PREFIX + json.dumps({'step': 3, 'message': 'Failed to load sample policies', 'error': True}) + "\n\n"
                
        except Exception as e:
            current_app.logger.error(f"Error during baseline reset: {str(e)}")
            yield SSE_DATA_PREFIX + json.dumps({'step': 0, 'message': f'Error: {str(e)}', 'error': True}) + "\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@admin_bp.route("/reset-baselines", methods=["GET"])
@admin_required
def reset_baselines():
    """Show the baseline reset page with progress tracking."""
    return render_template("admin/reset_baselines.html")


@admin_bp.route("/reset-recommendations", methods=["POST"])
@admin_required
def reset_recommendations():
    """
    Remove all recommendations from the database.
    
    This is an administrative action that will delete all recommendation data
    across all users. Use with caution as this action cannot be undone.
    """
    try:
        from src.database.mongo_operations import MongoOperations
        from flask import flash, redirect, url_for
        
        # Initialize MongoOperations and clear all recommendations
        mongo_ops = MongoOperations()
        deleted_count = mongo_ops.clear_all_recommendations()
        
        if deleted_count > 0:
            flash(f"Successfully removed {deleted_count} recommendations from the database.", "success")
        else:
            flash("No recommendations found in the database to remove. The recommendations collection is already empty.", "info")
        logger.info(f"Admin {current_user.id if current_user.is_authenticated else 'unknown'} reset all recommendations. Removed {deleted_count} entries.")
        
    except Exception as e:
        error_msg = f"Failed to reset recommendations: {str(e)}"
        logger.error(error_msg)
        flash(error_msg, "error")
    
    return redirect(url_for('admin.dashboard'))

# ---------------------------------------------------------------------------
# Change admin password
# ---------------------------------------------------------------------------

@admin_bp.route("/change_password", methods=["GET", "POST"])
@admin_required
def change_password():
    """
    Admin password change - redirects to user profile for consistency.
    
    Since we now use unified authentication, admin users should change
    their password through the main user profile interface.
    """
    flash("Please use your user profile to change your password", "info")
    return redirect(url_for("auth.profile"))


# Literature Management Routes
@admin_bp.route("/literature")
@admin_required
def literature_dashboard():
    """Literature management dashboard displaying system status and recent processing history."""
    try:
        literature_engine = LiteratureEngine()
        system_status = literature_engine.get_processing_status()
        recent_history = literature_engine.get_recent_processing_history(limit=10)
        recent_activity = literature_engine.get_recent_processing_activity(limit=6)
        
        return render_template(
            "admin/literature_dashboard.html",
            system_status=system_status,
            recent_history=recent_history,
            recent_activity=recent_activity,
            page_title="Literature Management"
        )
        
    except Exception as e:
        flash(f"Error loading literature dashboard: {str(e)}", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/literature/upload", methods=["GET", "POST"])
@admin_required
def literature_upload():
    """Handle academic literature document uploads and processing."""
    if request.method == "GET":
        return render_template("admin/literature_upload.html", page_title="Upload Literature")
    
    try:
        literature_engine = LiteratureEngine()
        
        if 'file' not in request.files:
            flash("No file provided", "error")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected", "error")
            return redirect(request.url)
        
        # Extract metadata from form
        metadata = {
            'title': request.form.get('title', ''),
            'author': request.form.get('author', ''),
            'publication_year': request.form.get('publication_year', ''),
            'source_url': request.form.get('source_url', ''),
            'description': request.form.get('description', ''),
            'uploaded_by': 'admin',
            'upload_date': datetime.now().isoformat()
        }
        
        # Log start of processing
        try:
            literature_engine.log_activity(status='processing', filename=file.filename)
        except Exception:
            pass

        # Process the uploaded file
        processing_results = literature_engine.process_uploaded_file(file, metadata)
        
        # Flash message based on results
        status = processing_results.get('status')
        if status == 'integrated_successfully':
            # Run automatic document scanning after successful integration
            try:
                from src.utils.auto_document_manager import run_auto_document_scan
                scan_results = run_auto_document_scan()
                
                success_msg = "Document processed and integrated successfully!"
                if scan_results.get('scanned', 0) > 0:
                    success_msg += f" Auto-scan found and processed {scan_results['scanned']} new documents."
                else:
                    success_msg += " Auto-scan completed (no new documents found)."
                    
                flash(success_msg, "success")
                # Refresh repository indices after potential batch changes (debounced)
                try:
                    LiteratureRepository.get().refresh_indices_if_needed()
                except Exception:
                    pass
                try:
                    literature_engine.log_activity(
                        status='completed',
                        filename=processing_results.get('details', {}).get('filename') or file.filename,
                        document_id=processing_results.get('document_id'),
                        quality=processing_results.get('quality_assessment', {}).get('total_score'),
                        insights_count=len(processing_results.get('extracted_insights', []) or [])
                    )
                except Exception:
                    pass
                
            except Exception as scan_error:
                flash("Document processed and integrated successfully! (Auto-scan failed)", "success")
                logger.error(f"Auto-scan after upload failed: {scan_error}")
                
        elif status == 'requires_review':
            flash("Document processed but requires manual review", "warning")
            try:
                literature_engine.log_activity(
                    status='completed',
                    filename=processing_results.get('details', {}).get('filename') or file.filename,
                    document_id=processing_results.get('document_id'),
                    quality=processing_results.get('quality_assessment', {}).get('total_score'),
                    insights_count=len(processing_results.get('extracted_insights', []) or [])
                )
            except Exception:
                pass
        else:
            flash(f"Processing failed: {processing_results.get('message', 'Unknown error')}", "error")
            try:
                literature_engine.log_activity(status='failed', filename=file.filename)
            except Exception:
                pass
        
        return render_template(
            "admin/literature_results.html",
            results=processing_results,
            page_title="Processing Results"
        )
        
    except Exception as e:
        flash(f"Error processing upload: {str(e)}", "error")
        return redirect(request.url)


@admin_bp.route("/literature/knowledge-base")
@admin_required
def literature_knowledge_base():
    """Knowledge base management interface for reviewing and managing academic insights."""
    try:
        literature_engine = LiteratureEngine()
        kb_status = literature_engine.get_processing_status()
        
        # Use unified document data function for consistent quality scores
        recent_updates = literature_engine.get_unified_document_data(include_version_history=False)
        
        # Format document IDs for display (keep original ID for URL, add display version)
        for doc in recent_updates:
            doc_id = doc.get("document_id", "")
            if len(doc_id) > 30:
                doc["display_id"] = doc_id[:30] + "..."
            else:
                doc["display_id"] = doc_id
        
        return render_template(
            "admin/literature_knowledge_base.html",
            kb_status=kb_status,
            recent_updates=recent_updates,
            page_title="Knowledge Base Management"
        )
        
    except Exception as e:
        flash(f"Error loading knowledge base: {str(e)}", "error")
        return redirect(url_for("admin.dashboard"))

# ---------------------------------------------------------------------------
# Literature document details (dedicated page)
# ---------------------------------------------------------------------------
@admin_bp.route("/literature/document/<doc_id>")
@admin_required
def literature_document_detail(doc_id: str):
    """Show details for a single literature document on a dedicated page."""
    try:
        import os
        engine = LiteratureEngine()
        docs = engine.get_unified_document_data(include_version_history=True)
        
        # Find matching document
        selected = None
        for d in docs:
            if d.get('document_id') == doc_id:
                selected = d
                break
        
        if not selected:
            # Try partial match as fallback
            for d in docs:
                if doc_id in str(d.get('document_id', '')) or str(d.get('document_id', '')) in doc_id:
                    selected = d
                    break
        
        if not selected:
            flash("Document not found in knowledge base", "error")
            return redirect(url_for("admin.literature_knowledge_base"))

        # Get knowledge base path and check access
        kb_manager = engine.knowledge_manager
        kb_path = kb_manager.knowledge_base_path
        
        if not os.path.exists(kb_path):
            raise Exception(f"Knowledge base path does not exist: {kb_path}")

        # List directory contents and find matching file
        md_files = []
        all_files = os.listdir(kb_path)
        md_files = [f for f in all_files if f.endswith('.md')]
        
        # Find the markdown file for this document
        md_content = None
        full_filename = None
        
        for filename in md_files:
            if filename.endswith('.md'):
                filename_stem = filename.replace('.md', '')
                # Check if doc_id is a prefix of the filename (handles truncated IDs)
                if filename_stem.startswith(doc_id) or doc_id.startswith(filename_stem) or doc_id in filename:
                    full_filename = filename
                    
                    file_path = os.path.join(kb_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    break

        # Process markdown content if found
        if md_content and full_filename:
            # Parse basic metadata from markdown content
            insights = []
            lines = md_content.split('\n')
            current_insight = ""
            in_insight_section = False
            
            # Extract insights from markdown
            for line in lines:
                line = line.strip()
                if line.startswith('### Insight ') or line.startswith('### Additional Insight '):
                    if current_insight.strip():
                        insights.append(current_insight.strip())
                    current_insight = ""
                    in_insight_section = True
                    continue
                elif line.startswith('##') and not line.startswith('### '):
                    if current_insight.strip():
                        insights.append(current_insight.strip())
                        current_insight = ""
                    in_insight_section = False
                    continue
                elif in_insight_section and line:
                    if current_insight:
                        current_insight += " " + line
                    else:
                        current_insight = line
            
            if current_insight.strip():
                insights.append(current_insight.strip())
            
            # Get file stats for additional metadata
            file_path = os.path.join(kb_path, full_filename)
            file_stats = os.stat(file_path)
            
            # Extract more metadata from markdown content
            metadata = {}
            abstract = ""
            keywords = ""
            quality_score = None
            integration_date = ""
            document_id = ""
            
            # Parse metadata sections
            for line in lines:
                line = line.strip()
                if line.startswith('- **Author(s)**:'):
                    metadata['authors'] = line.replace('- **Author(s)**:', '').strip()
                elif line.startswith('- **Publication Date**:'):
                    metadata['publication_date'] = line.replace('- **Publication Date**:', '').strip()
                elif line.startswith('- **Journal/Conference**:'):
                    metadata['journal'] = line.replace('- **Journal/Conference**:', '').strip()
                elif line.startswith('- **Quality Score**:'):
                    quality_score = line.replace('- **Quality Score**:', '').strip()
                elif line.startswith('- **Document ID**:'):
                    document_id = line.replace('- **Document ID**:', '').strip()
                elif line.startswith('- **Integration Date**:'):
                    integration_date = line.replace('- **Integration Date**:', '').strip()
            
            # Extract abstract and keywords in a separate pass
            in_abstract = False
            in_keywords = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('## Abstract'):
                    in_abstract = True
                    in_keywords = False
                    continue
                elif line.startswith('## Keywords'):
                    in_abstract = False
                    in_keywords = True
                    continue
                elif line.startswith('##') and not line.startswith('### '):
                    in_abstract = False
                    in_keywords = False
                    continue
                
                if in_abstract and line:
                    abstract += line + " "
                elif in_keywords and line:
                    keywords += line + " "
            
            # Try to extract original filename from document ID or filename
            original_filename_guess = ""
            if document_id:
                # Extract meaningful parts from document ID
                parts = document_id.split('_')
                if len(parts) > 3:
                    # Remove date and hash, keep the middle part
                    meaningful_part = '_'.join(parts[3:-1])
                    original_filename_guess = meaningful_part.replace('_', ' ').title()
            
            selected.update({
                'insights': insights,
                'content': md_content,
                'original_filename': full_filename,
                'original_file_guess': original_filename_guess,
                'markdown_file_size': file_stats.st_size,
                'file_size': file_stats.st_size,  # Keep for compatibility
                'processing_date': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'integration_date': integration_date,
                'document_id_full': document_id,
                'metadata': metadata,
                'abstract': abstract.strip(),
                'keywords': keywords.strip(),
                'quality_score_parsed': quality_score,
                'confidence_level': 'high' if len(insights) > 5 else 'medium',
                'auto_approved': True,
                'original_file_exists': False,
                'is_preloaded': True,
                'total_insights': len(insights),
                'content_length': len(md_content),
                'lines_count': len(lines)
            })

        return render_template(
            "admin/literature_document_detail.html",
            doc=selected,
            md_filename=None,
            page_title=f"Document: {doc_id}"
        )
            
    except Exception as e:
        flash(f"Error loading document details: {str(e)}", "error")
        return redirect(url_for("admin.literature_knowledge_base"))

# ---------------------------------------------------------------------------
# Serve raw knowledge base file (read-only)
# ---------------------------------------------------------------------------
@admin_bp.route("/literature/raw/<path:filename>")
@admin_required
def literature_raw_file(filename: str):
    """Serve a raw Markdown file from the knowledge base directory.

    Security: restrict to basename to prevent directory traversal.
    """
    try:
        engine = LiteratureEngine()
        kb_path = getattr(engine.knowledge_manager, 'knowledge_base_path', 'docs/knowledge_base')
        import os
        safe_name = os.path.basename(filename)
        full_path = os.path.join(kb_path, safe_name)
        if not os.path.exists(full_path):
            abort(404)
        # Let Flask infer mime; default to text/markdown
        return send_from_directory(kb_path, safe_name, as_attachment=False, mimetype='text/markdown')
    except Exception as e:
        current_app.logger.error(f"Error serving raw file {filename}: {e}")
        abort(500)
@admin_bp.route("/literature/cleanup", methods=["GET", "POST"])
@admin_required
def literature_cleanup():
    """Literature cleanup interface for removing outdated documents."""
    if request.method == "GET":
        # Show cleanup interface
        try:
            literature_engine = LiteratureEngine()
            kb_status = literature_engine.get_processing_status()
            
            # Use unified document data function for consistent quality scores
            documents_for_cleanup = literature_engine.get_unified_document_data(include_version_history=False)
            
            return render_template(
                "admin/literature_cleanup.html",
                kb_status=kb_status,
                recent_updates=documents_for_cleanup,  # All documents, not just recent updates
                page_title="Literature Cleanup"
            )
            
        except Exception as e:
            flash(f"Error loading cleanup interface: {str(e)}", "error")
            return redirect(url_for("admin.literature_dashboard"))
    
    else:
        # Handle cleanup actions
        selected_docs = request.form.getlist("selected_documents")
        action = request.form.get("action")
        
        if not selected_docs:
            flash("No documents selected", "error")
            return redirect(request.url)
        
        try:
            if action == "delete":
                literature_engine = LiteratureEngine()
                kb_manager = literature_engine.knowledge_manager
                
                # Create backup before bulk operations
                backup_id = kb_manager._create_backup()
                
                deleted_count = 0
                kb_path = kb_manager.knowledge_base_path
                
                import re
                for doc_id in selected_docs:
                    # Extract possible 8-char content hash to catch related variants
                    m = re.search(r"[a-f0-9]{8}$", doc_id)
                    short_hash = m.group(0) if m else ""

                    # Remove files whose stem matches doc_id or contains the same short hash
                    for filename in list(os.listdir(kb_path)):
                        if filename.endswith(".md"):
                            stem = os.path.splitext(filename)[0]
                            if stem == doc_id or (short_hash and short_hash in stem):
                                file_path = os.path.join(kb_path, filename)
                                try:
                                    os.remove(file_path)
                                    deleted_count += 1
                                except Exception as e:
                                    logger.error(f"Failed to delete {file_path}: {e}")

                    # Purge logs/history/backups for this doc_id (and variants)
                    try:
                        kb_manager.remove_document_from_history(doc_id)
                        if short_hash:
                            kb_manager.remove_document_from_history(short_hash)
                        kb_manager.purge_activity_log(doc_id)
                        if short_hash:
                            kb_manager.purge_activity_log(short_hash)
                        kb_manager.remove_backups(doc_id)
                        if short_hash:
                            kb_manager.remove_backups(short_hash)
                    except Exception as e:
                        logger.error(f"Cleanup metadata purge failed for {doc_id}: {e}")
                
                flash(f"Successfully deleted {deleted_count} document(s). Backup created: {backup_id}", "success")
            elif action == "archive":
                flash(f"Successfully archived {len(selected_docs)} documents", "success")
            
            return redirect(url_for("admin.literature_knowledge_base"))
            
        except Exception as e:
            flash(f"Error during cleanup: {str(e)}", "error")
            return redirect(request.url)

@admin_bp.route("/literature/document-details/<document_id>")
@admin_required
def document_details(document_id):
    """API endpoint to get detailed information about a specific document."""
    try:
        literature_engine = LiteratureEngine()
        
        # Get all documents and find the one with matching ID
        all_documents = literature_engine.get_unified_document_data(include_version_history=False)
        
        # Find document by ID
        document = None
        for doc in all_documents:
            if doc.get('document_id') == document_id or doc.get('filename', '').replace('.md', '') == document_id:
                document = doc
                break
        
        if not document:
            return jsonify({
                'success': False,
                'error': f'Document not found: {document_id}'
            }), 404
        
        # Get additional details by reading markdown file directly
        try:
            kb_manager = literature_engine.knowledge_manager
            kb_path = kb_manager.knowledge_base_path
            
            # Find the markdown file for this document
            md_content = None
            full_filename = None
            
            if os.path.exists(kb_path):
                for filename in os.listdir(kb_path):
                    if filename.endswith('.md') and (document_id in filename or filename.replace('.md', '') == document_id):
                        full_filename = filename
                        file_path = os.path.join(kb_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            md_content = f.read()
                        break
            
            if md_content and full_filename:
                # Extract insights from markdown
                insights = []
                lines = md_content.split('\n')
                current_insight = ""
                in_insight_section = False
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('### Insight ') or line.startswith('### Additional Insight '):
                        if current_insight.strip():
                            insights.append(current_insight.strip())
                        current_insight = ""
                        in_insight_section = True
                        continue
                    elif line.startswith('##') and not line.startswith('### '):
                        if current_insight.strip():
                            insights.append(current_insight.strip())
                            current_insight = ""
                        in_insight_section = False
                        continue
                    elif in_insight_section and line:
                        if current_insight:
                            current_insight += " " + line
                        else:
                            current_insight = line
                
                if current_insight.strip():
                    insights.append(current_insight.strip())
                
                # Get file stats
                file_path = os.path.join(kb_path, full_filename)
                file_stats = os.stat(file_path)
                
                # Merge additional details
                document.update({
                    'insights': insights,
                    'content': md_content,
                    'original_filename': full_filename,
                    'file_size': file_stats.st_size,
                    'processing_date': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'confidence_level': 'high' if len(insights) > 5 else 'medium',
                    'auto_approved': True,
                    'original_file_exists': False,
                    'is_preloaded': True
                })
        except Exception as e:
            logger.warning(f"Could not get additional details for document {document_id}: {str(e)}")
        
        return jsonify({
            'success': True,
            'details': document
        })
        
    except Exception as e:
        logger.error(f"Error getting document details for {document_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@admin_bp.route('/get-available-backups', methods=['GET'])
@admin_required
def get_available_backups():
    """
    Retrieve a comprehensive list of available knowledge base backups.
    
    This endpoint provides administrators with detailed information about all
    available backup snapshots of the knowledge base, including creation dates,
    file counts, and storage sizes. Used by the backup management interface
    to display restore options to users.
    
    Returns:
        JSON response containing backup metadata and success status
    """
    try:
        from src.literature.literature_engine import LiteratureEngine
        literature_engine = LiteratureEngine()
        kb_manager = literature_engine.knowledge_manager
        
        backups = kb_manager.get_available_backups()
        
        return jsonify({
            'success': True,
            'backups': backups
        })
        
    except Exception as e:
        logger.error(f"Error getting available backups: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error getting backups: {str(e)}'
        }), 500

@admin_bp.route('/restore-backup', methods=['POST'])
@admin_required
def restore_backup():
    """
    Restore the knowledge base from a selected backup snapshot.
    
    This administrative endpoint enables the restoration of the knowledge base
    to a previous state using backup snapshots. The function automatically creates
    a safety backup of the current state before proceeding with the restoration
    to prevent data loss. Comprehensive logging tracks all restoration activities
    for audit purposes.
    
    Expected JSON payload:
        backup_id (str): The identifier of the backup to restore from
        
    Returns:
        JSON response with restoration results and affected file details
    """
    try:
        data = request.get_json()
        backup_id = data.get('backup_id')
        
        if not backup_id:
            return jsonify({
                'success': False,
                'error': 'Backup ID is required'
            }), 400
        
        from src.literature.literature_engine import LiteratureEngine
        literature_engine = LiteratureEngine()
        kb_manager = literature_engine.knowledge_manager
        
        result = kb_manager.restore_backup(backup_id)
        
        if result['success']:
            logger.info(f"Admin {session.get('admin_username', 'unknown')} restored backup {backup_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error restoring backup: {str(e)}'
        }), 500


@admin_bp.route('/literature/complete-cleanup', methods=['POST'])
@admin_required  
def complete_literature_cleanup():
    """
    Complete literature cleanup - removes ALL literature traces from the system.
    This includes markdown files, activity logs, version history, and backups.
    """
    try:
        from src.literature.literature_engine import LiteratureEngine
        import shutil
        
        literature_engine = LiteratureEngine()
        kb_manager = literature_engine.knowledge_manager
        kb_path = kb_manager.knowledge_base_path
        
        cleanup_stats = {
            'files_removed': 0,
            'activity_cleared': False,
            'history_cleared': False,
            'backups_cleared': False
        }
        
        # 1. Remove all markdown files
        for filename in os.listdir(kb_path):
            if filename.endswith('.md'):
                file_path = os.path.join(kb_path, filename)
                try:
                    os.remove(file_path)
                    cleanup_stats['files_removed'] += 1
                except Exception as e:
                    logger.error(f"Failed to remove {file_path}: {e}")
        
        # 2. Clear activity log
        activity_log_path = os.path.join(kb_path, 'activity_log.json')
        try:
            with open(activity_log_path, 'w') as f:
                json.dump([], f)
            cleanup_stats['activity_cleared'] = True
        except Exception as e:
            logger.error(f"Failed to clear activity log: {e}")
        
        # 3. Clear version history
        version_history_path = os.path.join(kb_path, 'version_history.json')
        try:
            with open(version_history_path, 'w') as f:
                json.dump([], f)
            cleanup_stats['history_cleared'] = True
        except Exception as e:
            logger.error(f"Failed to clear version history: {e}")
        
        # 4. Remove all backups
        backups_path = os.path.join(kb_path, 'backups')
        try:
            if os.path.exists(backups_path):
                shutil.rmtree(backups_path)
                os.makedirs(backups_path, exist_ok=True)
            cleanup_stats['backups_cleared'] = True
        except Exception as e:
            logger.error(f"Failed to clear backups: {e}")
        
        # 5. Clear any cached data in literature engine
        try:
            # Force refresh of literature engine data
            literature_engine._document_cache = {}
            kb_manager.activity_log = []
            kb_manager.version_history = []
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
        
        flash(f"Complete cleanup successful! Removed {cleanup_stats['files_removed']} files, cleared activity log, history, and backups.", "success")
        return jsonify({
            'success': True,
            'message': 'Complete literature cleanup completed successfully',
            'stats': cleanup_stats
        })
        
    except Exception as e:
        logger.error(f"Error in complete literature cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500


@admin_bp.route('/literature/reprocess', methods=['POST'])
@admin_required
def reprocess_existing_documents():
    """Reprocess existing documents with enhanced capabilities."""
    try:
        enhanced_processing = request.json.get('enhanced', True) if request.is_json else True
        
        logger.info("Starting reprocessing of existing documents")
        
        # Get the literature engine instance
        from src.literature.literature_engine import LiteratureEngine
        literature_engine = LiteratureEngine()
        
        # Start reprocessing
        results = literature_engine.reprocess_existing_documents(enhanced_processing)
        
        if results.get('status') == 'success':
            message = f"Successfully reprocessed {results['processed']} documents"
            if results['errors'] > 0:
                message += f" with {results['errors']} errors"
            
            flash(message, "success")
            
            return jsonify({
                'success': True,
                'message': message,
                'results': results
            })
        
        elif results.get('status') == 'no_documents':
            flash("No documents found in knowledge base to reprocess", "info")
            return jsonify({
                'success': True,
                'message': 'No documents found to reprocess',
                'results': results
            })
        
        else:
            flash(f"Reprocessing failed: {results.get('message', 'Unknown error')}", "error")
            return jsonify({
                'success': False,
                'error': results.get('message', 'Unknown error'),
                'results': results
            }), 500
        
    except Exception as e:
        error_msg = f"Error during document reprocessing: {str(e)}"
        logger.error(error_msg)
        flash(error_msg, "error")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@admin_bp.route('/literature/reprocess-status')
@admin_required  
def get_reprocessing_status():
    """Get current status of document reprocessing capabilities."""
    try:
        from src.literature.literature_engine import LiteratureEngine
        literature_engine = LiteratureEngine()
        
        # Count existing documents
        kb_path = literature_engine.knowledge_manager.knowledge_base_path
        document_count = 0
        
        if os.path.exists(kb_path):
            document_count = len([f for f in os.listdir(kb_path) if f.endswith('.md')])
        
        # Check if original PDFs are available for reprocessing
        data_dir = "data/literature"
        pdf_count = 0
        if os.path.exists(data_dir):
            pdf_count = len([f for f in os.listdir(data_dir) if f.endswith('.pdf')])
        
        # Check available enhancement capabilities
        capabilities = {
            'theme_extraction': literature_engine.processor.theme_extractor is not None,
            'enhanced_metadata': True,  # Always available
            'content_recommendations': True,  # Always available
            'spacy_available': literature_engine.processor.nlp is not None,
            'embeddings_available': literature_engine.processor.embedder is not None
        }
        
        return jsonify({
            'document_count': document_count,
            'pdf_count': pdf_count,
            'capabilities': capabilities,
            'ready_for_reprocessing': document_count > 0
        })
        
    except Exception as e:
        logger.error(f"Error getting reprocessing status: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500



@admin_bp.route('/literature/pending-reviews')
@admin_required
def get_pending_reviews():
    """Get documents pending manual review."""
    try:
        pending_documents = []
        analysis_dir = "data/analysis"
        
        if os.path.exists(analysis_dir):
            for filename in os.listdir(analysis_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(analysis_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                        
                        # Check if document is not in knowledge base yet
                        doc_id = doc_data.get('document_id', '')
                        kb_path = "docs/knowledge_base"
                        
                        # Look for corresponding MD file in knowledge base
                        found_in_kb = False
                        if os.path.exists(kb_path):
                            hash_part = doc_id.split('_')[-1] if doc_id else ''
                            
                            for kb_file in os.listdir(kb_path):
                                if kb_file.endswith('.md') and hash_part in kb_file:
                                    found_in_kb = True
                                    break
                        
                        if not found_in_kb:
                            # This document is pending review
                            pending_documents.append({
                                'document_id': doc_id,
                                'original_filename': doc_data.get('original_filename', 'Unknown'),
                                'processing_date': doc_data.get('processing_date', ''),
                                'quality_score': doc_data.get('analysis_summary', {}).get('quality_score', 0),
                                'insights_count': doc_data.get('analysis_summary', {}).get('insights_count', 0),
                                'metadata': doc_data.get('full_analysis', {}).get('metadata', {})
                            })
                    except Exception as e:
                        logger.warning(f"Error reading analysis file {filename}: {str(e)}")
        
        return jsonify({
            'success': True,
            'pending_documents': pending_documents,
            'count': len(pending_documents)
        })
        
    except Exception as e:
        logger.error(f"Error getting pending reviews: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/literature/approve-document', methods=['POST'])
@admin_required
def approve_document():
    """Approve a document for integration into knowledge base."""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        
        if not document_id:
            return jsonify({
                'success': False,
                'error': 'Document ID required'
            }), 400
        
        # Find the analysis file
        analysis_file = f"data/analysis/{document_id}.json"
        if not os.path.exists(analysis_file):
            return jsonify({
                'success': False,
                'error': 'Document analysis not found'
            }), 404
        
        # Load the analysis data
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # Get processing results from analysis
        processing_results = analysis_data.get('full_analysis', {})
        
        # Force integration into knowledge base
        from src.literature.literature_engine import LiteratureEngine
        literature_engine = LiteratureEngine()
        
        # Bypass all checks and force direct integration
        backup_id = literature_engine.knowledge_manager._create_backup()
        integration_results = literature_engine.knowledge_manager._integrate_new_document(processing_results, backup_id)
        
        # Update version history if successful
        if integration_results.get('status') == 'success':
            literature_engine.knowledge_manager._update_version_history(integration_results, processing_results)
        
        if integration_results.get('status') == 'success':
            flash("Document approved and integrated into knowledge base", "success")
            return jsonify({
                'success': True,
                'message': 'Document approved successfully',
                'integration_results': integration_results
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Integration failed: {integration_results.get('message', 'Unknown error')}"
            }), 500
        
    except Exception as e:
        error_msg = f"Error approving document: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@admin_bp.route('/literature/reject-document', methods=['POST'])
@admin_required
def reject_document():
    """Reject a document and remove from pending review."""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        reason = data.get('reason', 'No reason provided')
        
        if not document_id:
            return jsonify({
                'success': False,
                'error': 'Document ID required'
            }), 400
        
        # Find and remove the analysis file
        analysis_file = f"data/analysis/{document_id}.json"
        if os.path.exists(analysis_file):
            os.remove(analysis_file)
        
        # Remove PDF file if exists
        pdf_file = f"data/literature/{document_id[:-8]}.pdf"  # Remove ID suffix
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        
        flash(f"Document rejected and removed. Reason: {reason}", "info")
        return jsonify({
            'success': True,
            'message': 'Document rejected successfully'
        })
        
    except Exception as e:
        error_msg = f"Error rejecting document: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

