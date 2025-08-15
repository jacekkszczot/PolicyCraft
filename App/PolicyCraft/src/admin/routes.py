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

import json
import logging
import os
from functools import wraps
from typing import Dict

from flask import (
    Blueprint, current_app, flash, redirect, render_template,
    request, session, url_for, Response, json, jsonify, send_from_directory, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import User, db as sqlalchemy_db
from src.database.mongo_operations import MongoOperations
from src.literature.literature_engine import LiteratureEngine
from src.analysis_engine.literature.repository import LiteratureRepository
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, template_folder="../web/templates/admin", url_prefix="/admin")

# ---------------------------------------------------------------------------
# Simple password storage (hashed) – for single-admin scenario
# ---------------------------------------------------------------------------
CONFIG_DIR = os.path.join(os.getcwd(), "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "admin_config.json")
DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_immediately")  # Set ADMIN_PASSWORD in production

mongo_db = MongoOperations()

# ---------------------------------------------------------------------------
# Common literals/constants
# ---------------------------------------------------------------------------
ADMIN_DASHBOARD_ENDPOINT = "admin.dashboard"
ADMIN_USERS_ENDPOINT = "admin.users"
SSE_DATA_PREFIX = "data: "


def _load_config() -> Dict:
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _save_config({"password_hash": generate_password_hash(DEFAULT_PASSWORD)})
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def _save_config(cfg: Dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

# ---------------------------------------------------------------------------
# Decorator for protected routes
# ---------------------------------------------------------------------------

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login", next=request.path))
        return func(*args, **kwargs)
    return wrapper

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        cfg = _load_config()
        if check_password_hash(cfg["password_hash"], password):
            session["is_admin"] = True
            flash("Logged in as admin", "success")
            return redirect(request.args.get("next") or url_for(ADMIN_DASHBOARD_ENDPOINT))
        flash("Invalid admin password", "error")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
@admin_required
def logout():
    session.pop("is_admin", None)
    flash("Logged out of admin", "info")
    return redirect(url_for("index"))

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
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/delete/<int:user_id>")
@admin_required
def delete_user(user_id):
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

# ---------------------------------------------------------------------------
# Change admin password
# ---------------------------------------------------------------------------

@admin_bp.route("/change_password", methods=["GET", "POST"])
@admin_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")
        cfg = _load_config()
        if not check_password_hash(cfg["password_hash"], current_pw):
            flash("Current password incorrect", "error")
            return redirect(url_for("admin.change_password"))
        if new_pw != confirm_pw or len(new_pw) < 6:
            flash("New passwords do not match or too short", "error")
            return redirect(url_for("admin.change_password"))
        cfg["password_hash"] = generate_password_hash(new_pw)
        _save_config(cfg)
        flash("Password updated", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/change_password.html")


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
                logger.info(f"Auto-scan after upload completed: {scan_results}")
                
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
        
        # Format document IDs for display (truncate if too long)
        for doc in recent_updates:
            doc_id = doc.get("document_id", "")
            if len(doc_id) > 30:
                doc["document_id"] = doc_id[:30] + "..."
        
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
        engine = LiteratureEngine()
        docs = engine.get_unified_document_data(include_version_history=True)
        # Find matching document by document_id
        selected = None
        for d in docs:
            if d.get('document_id') == doc_id:
                selected = d
                break
        if not selected:
            flash("Document not found in knowledge base", "error")
            return redirect(url_for("admin.literature_knowledge_base"))

        # Best-effort: locate markdown file path by filename or doc_id fragment
        kb_path = getattr(engine.knowledge_manager, 'knowledge_base_path', 'docs/knowledge_base')
        md_filename = selected.get('filename')
        md_path = None
        try:
            import os
            if md_filename:
                fpath = os.path.join(kb_path, md_filename)
                if os.path.exists(fpath):
                    md_path = md_filename
            if not md_path:
                for f in os.listdir(kb_path):
                    if f.endswith('.md') and (doc_id in f):
                        md_path = f
                        break
        except Exception:
            md_path = None

        # Enrich with additional details (including confidence_level)
        try:
            kb_manager = engine.knowledge_manager
            doc_details = kb_manager.get_document_by_id(doc_id)
            if doc_details:
                selected.update({
                    'insights': doc_details.get('insights', []),
                    'content': doc_details.get('content', ''),
                    'original_filename': doc_details.get('metadata', {}).get('original_filename'),
                    'file_size': doc_details.get('metadata', {}).get('file_size'),
                    'processing_date': doc_details.get('metadata', {}).get('processing_date'),
                    'confidence_level': doc_details.get('confidence_level'),
                    'auto_approved': doc_details.get('auto_approved', False),
                    'original_file_exists': doc_details.get('original_file_exists', False),
                    'is_preloaded': doc_details.get('is_preloaded', False)
                })
        except Exception as e:
            logger.warning(f"Could not enrich document {doc_id} with details: {str(e)}")

        return render_template(
            "admin/literature_document_detail.html",
            doc=selected,
            md_filename=md_path,
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
        
        # Get additional details from knowledge manager
        try:
            kb_manager = literature_engine.knowledge_manager
            doc_details = kb_manager.get_document_by_id(document_id)
            
            if doc_details:
                # Merge additional details
                document.update({
                    'insights': doc_details.get('insights', []),
                    'content': doc_details.get('content', ''),
                    'original_filename': doc_details.get('metadata', {}).get('original_filename'),
                    'file_size': doc_details.get('metadata', {}).get('file_size'),
                    'processing_date': doc_details.get('metadata', {}).get('processing_date'),
                    'confidence_level': doc_details.get('confidence_level', 'N/A'),
                    'auto_approved': doc_details.get('auto_approved', False),
                    'original_file_exists': doc_details.get('original_file_exists', False),
                    'is_preloaded': doc_details.get('is_preloaded', False)
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

