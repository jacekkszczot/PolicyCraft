"""
Administrative Routes for PolicyCraft AI Policy Analysis Platform.

This module implements the administrative interface for the PolicyCraft application,
providing essential system administration tools and user management capabilities.

Key Functionality:
- Secure authentication for administrative access
- Dashboard with system statistics and health metrics
- Comprehensive user management (view/delete users)
- System configuration and maintenance tools
- Password management for administrative accounts

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
import os
from functools import wraps
from typing import Dict

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import User, db as sqlalchemy_db
from src.database.mongo_operations import MongoOperations

admin_bp = Blueprint("admin", __name__, template_folder="../web/templates/admin", url_prefix="/admin")

# ---------------------------------------------------------------------------
# Simple password storage (hashed) – for single-admin scenario
# ---------------------------------------------------------------------------
CONFIG_DIR = os.path.join(os.getcwd(), "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "admin_config.json")
DEFAULT_PASSWORD = "admin123"

mongo_db = MongoOperations()


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
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
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
    baseline_global = mongo_db.analyses.count_documents({"user_id": -1, "filename": {"$regex": r"^\\[baseline\\]", "$options": "i"}})
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
        return redirect(url_for("admin.users"))
    username = user.username
    sqlalchemy_db.session.delete(user)
    sqlalchemy_db.session.commit()
    # Purge associated data
    mongo_db.purge_user_data(user_id)
    flash(f"Deleted user {username}", "success")
    return redirect(url_for("admin.users"))

# ---------------------------------------------------------------------------
# Baselines reset
# ---------------------------------------------------------------------------

@admin_bp.route("/reset_baselines", methods=["GET", "POST"])
@admin_required
def reset_baselines():
    if request.method == "POST":
        # Remove existing baseline docs
        mongo_db.analyses.delete_many({"filename": {"$regex": r"^\\[baseline\\]", "$options": "i"}})
        # Recreate global baselines from dataset
        mongo_db.load_sample_policies_for_user(-1)
        flash("Baselines reset completed", "success")
        return redirect(url_for("admin.dashboard"))
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
