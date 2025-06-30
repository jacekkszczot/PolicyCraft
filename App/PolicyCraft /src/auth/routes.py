"""
Authentication routes for PolicyCraft.
Clean version without duplicates.

Author: Jacek Robert Kszczot
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                password=form.password.data,
                first_name=form.first_name.data.strip() if form.first_name.data else None,
                last_name=form.last_name.data.strip() if form.last_name.data else None,
                institution=form.institution.data.strip() if hasattr(form, 'institution') and form.institution.data else None
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
    
    # Log the logout
    logger.info(f"User {username} logged out successfully")
    flash('You have been logged out successfully.', 'info')
    
    # Create response with cache headers
    response = redirect(url_for('index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile page."""
    return render_template('auth/profile.html', user=current_user)