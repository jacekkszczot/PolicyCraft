"""
Authentication routes for PolicyCraft.
Clean version without duplicates.

Author: Jacek Robert Kszczot
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from src.auth.models import User, db
from src.auth.forms import LoginForm, RegistrationForm
import logging

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Get form data
        username_or_email = form.username_or_email.data.strip()
        password = form.password.data
        remember = form.remember_me.data
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        # Verify user and password
        if user and user.check_password(password):
            if user.is_active:
                # Log user in
                login_user(user, remember=remember)
                user.update_last_login()
                db.session.commit()
                
                logger.info(f"User {user.username} logged in successfully")
                
                # Check if this is user's first login and handle onboarding
                if user.is_first_login():
                    from app import handle_first_login_onboarding
                    handle_first_login_onboarding(user.id)
                
                flash(f'Welcome back, {user.get_full_name()}!', 'success')
                
                # Redirect to intended page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Your account has been deactivated. Please contact support.', 'error')
        else:
            flash('Invalid username/email or password. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                username=form.email.data.strip().lower(),
                email=form.email.data.strip().lower(),
                password=form.password.data,
                first_name=form.first_name.data.strip() if form.first_name.data else None,
                last_name=form.last_name.data.strip() if form.last_name.data else None,
                gender=form.gender.data,
                institution=form.institution.data.strip()
            )
            
            # Save to database
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {user.username}")
            flash('Registration successful! You can now log in.', 'success')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    # Store username for logging
    username = current_user.username if current_user.is_authenticated else 'Unknown'
    
    # Logout user
    logout_user()
    
    # Clear session
    session.clear()

    # Manually clear remember-me cookie (extra safety)
    resp = make_response(redirect(url_for('auth.login')))
    resp.set_cookie('remember_token', '', expires=0, httponly=True)
    
    # Log the logout
    logger.info(f"User {username} logged out successfully")
    flash('You have been logged out successfully.', 'info')
    
    # Create response with cache headers
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile page."""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user details (name, institution, email)."""
    gender = request.form.get('gender', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    institution = request.form.get('institution', '').strip()
    email = request.form.get('email', '').strip().lower()

    # If email changed, ensure uniqueness
    if email and email != current_user.email:
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email address already in use.', 'error')
            return redirect(url_for('auth.profile'))
        current_user.email = email
    
    current_user.first_name = first_name or None
    current_user.last_name = last_name or None
    current_user.gender = gender or None
    current_user.institution = institution or None
    try:
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error for {current_user.username}: {str(e)}")
        flash('Failed to update profile.', 'error')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('confirm_password')

    if not current_user.check_password(current_pwd):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    if new_pwd != confirm_pwd or len(new_pwd) < 6:
        flash('New passwords do not match or are too short.', 'error')
        return redirect(url_for('auth.profile'))
    
    current_user.set_password(new_pwd)
    try:
        db.session.commit()
        flash('Password changed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password change error for {current_user.username}: {str(e)}")
        flash('Failed to change password.', 'error')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and associated data."""
    try:
        username = current_user.username
        logout_user()
        User.query.filter_by(id=current_user.id).delete()
        db.session.commit()
        flash('Your account has been deleted.', 'info')
        logger.info(f"Account deleted for user {username}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Account deletion error for {current_user.username}: {str(e)}")
        flash('Failed to delete account.', 'error')
    return redirect(url_for('index'))