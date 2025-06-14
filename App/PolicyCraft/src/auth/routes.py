"""
Enhanced logout debugging for PolicyCraft.
This adds comprehensive logging to track the logout process.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from src.auth.models import User, db
from src.auth.forms import LoginForm, RegistrationForm
import logging

print("=== ENHANCED AUTH ROUTES MODULE LOADED ===")

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with enhanced debugging."""
    print(f"DEBUG LOGIN: current_user.is_authenticated = {current_user.is_authenticated}")
    
    # Redirect if user already logged in
    if current_user.is_authenticated:
        print("DEBUG: User already authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    print(f"DEBUG: Form validation: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        # Get form data
        username_or_email = form.username_or_email.data.strip()
        password = form.password.data
        remember = form.remember_me.data
        
        print(f"DEBUG: Login attempt - username/email: {username_or_email}")
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        print(f"DEBUG: User found: {user is not None}")
        
        # Verify user and password
        if user and user.check_password(password):
            print(f"DEBUG: Password check passed for user: {user.username}")
            if user.is_active:
                # Log user in
                login_success = login_user(user, remember=remember)
                print(f"DEBUG: login_user() result: {login_success}")
                
                # Debug session state after login
                print(f"DEBUG: Session after login: {dict(session)}")
                print(f"DEBUG: current_user after login: {current_user}")
                print(f"DEBUG: current_user.is_authenticated: {current_user.is_authenticated}")
                
                user.update_last_login()
                db.session.commit()
                
                logger.info(f"User {user.username} logged in successfully")
                flash(f'Welcome back, {user.get_full_name()}!', 'success')
                
                # Redirect to intended page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    print(f"DEBUG: Redirecting to next page: {next_page}")
                    return redirect(next_page)
                print("DEBUG: Redirecting to dashboard")
                return redirect(url_for('dashboard'))
            else:
                flash('Your account has been deactivated. Please contact support.', 'error')
                logger.warning(f"Deactivated user {user.username} attempted login")
        else:
            flash('Invalid username/email or password. Please try again.', 'error')
            logger.warning(f"Failed login attempt for: {username_or_email}")
    
    print("DEBUG: Rendering login template")
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    print(f"DEBUG REGISTER: current_user.is_authenticated = {current_user.is_authenticated}")
    
    # Redirect if user already logged in
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
                institution=form.institution.data.strip() if form.institution.data else None
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
    """Handle user logout with COMPREHENSIVE debugging."""
    print("\n" + "="*60)
    print("COMPREHENSIVE LOGOUT DEBUG SESSION")
    print("="*60)
    
    # STEP 1: Pre-logout state
    print("STEP 1: PRE-LOGOUT STATE")
    print(f"  current_user.is_authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        print(f"  current_user.username: {current_user.username}")
        print(f"  current_user.id: {current_user.id}")
    print(f"  Session contents: {dict(session)}")
    print(f"  Session keys: {list(session.keys())}")
    
    # Store username for logging
    username = current_user.username if current_user.is_authenticated else 'Unknown'
    user_id = current_user.id if current_user.is_authenticated else None
    
    # STEP 2: Flask-Login logout
    print("\nSTEP 2: CALLING FLASK-LOGIN LOGOUT")
    logout_user()
    print(f"  After logout_user() - current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"  After logout_user() - current_user: {current_user}")
    
    # STEP 3: Manual session cleanup
    print("\nSTEP 3: MANUAL SESSION CLEANUP")
    session_keys_before = list(session.keys())
    print(f"  Session keys before cleanup: {session_keys_before}")
    
    # Remove Flask-Login specific keys
    removed_keys = []
    for key in ['_user_id', '_fresh', '_id', 'user_id']:
        if key in session:
            session.pop(key, None)
            removed_keys.append(key)
            print(f"  Removed session key: {key}")
    
    print(f"  Total keys removed: {removed_keys}")
    
    # STEP 4: Complete session clear
    print("\nSTEP 4: COMPLETE SESSION CLEAR")
    session.clear()
    print(f"  After session.clear() - Session contents: {dict(session)}")
    print(f"  After session.clear() - Session keys: {list(session.keys())}")
    
    # STEP 5: Final state verification
    print("\nSTEP 5: FINAL STATE VERIFICATION")
    print(f"  Final current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"  Final current_user: {current_user}")
    print(f"  Final session: {dict(session)}")
    
    # STEP 6: Database session check
    print("\nSTEP 6: DATABASE SESSION CHECK")
    try:
        if user_id:
            db_user = User.query.get(user_id)
            if db_user:
                print(f"  Database user still exists: {db_user.username}")
                print(f"  Database user last_login: {db_user.last_login}")
            else:
                print(f"  Database user not found for ID: {user_id}")
    except Exception as e:
        print(f"  Database check error: {e}")
    
    print("="*60)
    print("END LOGOUT DEBUG SESSION")
    print("="*60 + "\n")
    
    # Log the logout
    logger.info(f"User {username} logged out successfully")
    flash('You have been logged out successfully.', 'info')
    
    # Create response with comprehensive cache headers
    response = redirect(url_for('index'))
    
    # Anti-cache headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'  
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
    
    # Additional security headers
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    print(f"DEBUG: Response headers set - redirecting to index")
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile page."""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/session-check')
def session_check():
    """Debug endpoint to check session state."""
    print("\n" + "="*40)
    print("SESSION CHECK DEBUG")
    print("="*40)
    print(f"current_user.is_authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        print(f"current_user.username: {current_user.username}")
    print(f"Session contents: {dict(session)}")
    print(f"Session keys: {list(session.keys())}")
    print("="*40 + "\n")
    
    return {
        'authenticated': current_user.is_authenticated,
        'user': current_user.username if current_user.is_authenticated else None,
        'session': dict(session),
        'session_keys': list(session.keys())
    }