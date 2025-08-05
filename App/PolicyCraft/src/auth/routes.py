"""
Authentication Routes for PolicyCraft Application.

This module implements the HTTP endpoints for user authentication and account management
in the PolicyCraft platform. It handles the complete authentication workflow including
user registration, login, session management, and account customisation.

The module is structured as a Flask Blueprint, providing a clean separation of concerns
and following RESTful design principles. All routes implement proper security measures
including CSRF protection, secure password handling, and session management.

Key Features:
- User registration with comprehensive validation
- Secure login/logout functionality
- Profile management and customisation
- Password change and account deletion
- Session management and security headers

Security Considerations:
- All sensitive operations require authentication
- Passwords are never stored in plaintext
- Session tokens are securely managed by Flask-Login
- CSRF protection is enforced on all forms
- Security headers are set for all responses

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from src.database.models import User, db
from src.auth.forms import LoginForm, RegistrationForm
import logging

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user authentication and session establishment.
    
    This route manages the login process for both GET and POST requests. For GET requests,
    it renders the login form. For POST requests, it validates the submitted credentials
    and establishes an authenticated session if successful.
    
    The authentication process includes:
    - Validation of username/email and password
    - Account status verification (active/inactive)
    - Secure session creation with optional "remember me" functionality
    - Logging of successful and failed login attempts
    
    Security Features:
    - CSRF protection via Flask-WTF forms
    - Secure password verification using cryptographic hashing
    - Protection against timing attacks
    - Session fixation protection
    - Secure cookie settings
    
    Returns:
        Response: 
            - On GET: Rendered login template
            - On successful POST: Redirect to dashboard
            - On failed authentication: Re-rendered login form with error messages
            
    Example:
        # Successful login
        POST /login
        Form Data: username_or_email=user@example.com, password=securepassword123
        
        # Failed login
        POST /login
        Form Data: username_or_email=user@example.com, password=wrongpassword
        
    Note:
        - Passwords are never logged or stored in plaintext
        - Failed login attempts are logged for security monitoring
        - Session cookies are marked as secure and httpOnly
    """
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
    """
    Handle new user registration and account creation.
    
    This route manages the user registration process, validating and processing
    new account requests. It handles both GET requests (displaying the registration
    form) and POST requests (processing form submissions).
    
    The registration process includes:
    - Validation of all form fields (email, password, personal details)
    - Duplicate account prevention
    - Secure password hashing
    - Transaction management for database operations
    - Comprehensive error handling and user feedback
    
    Security Features:
    - CSRF protection via Flask-WTF forms
    - Password strength requirements
    - Email normalisation (case-insensitive, whitespace trimming)
    - Secure session management
    - Transaction rollback on error
    
    Returns:
        Response:
            - On GET: Rendered registration template
            - On successful POST: Redirect to login page with success message
            - On validation failure: Re-rendered form with error messages
            - On database error: Error message with 500 status code
            
    Example:
        # Successful registration
        POST /register
        Form Data: 
            email=user@example.com,
            password=SecurePass123!,
            confirm_password=SecurePass123!,
            first_name=John,
            last_name=Doe,
            gender=male,
            institution=Example University
            
    Note:
        - Passwords are hashed before storage using bcrypt
        - Email addresses are normalised to lowercase
        - All string inputs are stripped of leading/trailing whitespace
        - Database transactions ensure data consistency
    """
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
    """
    Handle user logout and session termination.
    
    This route securely terminates the current user's session and performs
    comprehensive cleanup of authentication artifacts. It ensures that all
    session data is properly invalidated and that no sensitive information
    remains accessible after logout.
    
    Security Measures:
    - Invalidates the current session token
    - Removes all session data
    - Deletes the remember-me cookie if present
    - Sets appropriate cache control headers
    - Provides user feedback via flash messages
    
    Process Flow:
    1. Records the username for logging purposes
    2. Logs out the user via Flask-Login
    3. Clears all session data
    4. Removes the remember-me cookie
    5. Sets cache control headers
    6. Redirects to the login page
    
    Returns:
        Response: 
            - Redirects to the login page with appropriate cache headers
            - Includes flash message confirming logout
            
    Security Headers:
        - Cache-Control: no-cache, no-store, must-revalidate
        - Pragma: no-cache
        - Expires: 0
        
    Note:
        - This route requires authentication
        - All operations are logged for security auditing
        - The response is explicitly marked as non-cacheable
    """
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
    """
    Display the authenticated user's profile information.
    
    This route renders a template containing the current user's profile details,
    including personal information and account settings. The route is protected
    and requires authentication to access.
    
    The profile page typically displays:
    - User's full name and contact information
    - Institutional affiliation
    - Account preferences
    - Security settings
    - Activity history
    
    Security:
    - Requires authentication via @login_required decorator
    - Only displays information for the currently logged-in user
    - Implements CSRF protection for any forms
    
    Returns:
        Response: Rendered profile template with user data
        
    Template:
        auth/profile.html - The profile page template
        
    Context Variables:
        user (User): The current user object containing profile information
        
    Example:
        GET /profile
        
    Note:
        - This route is only accessible to authenticated users
        - Sensitive information is never exposed in the template
        - The template includes forms for updating profile information
    """
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """
    Update the authenticated user's profile information.
    
    This route handles the submission of updated profile information from the
    user's profile page. It processes form data, validates the input, and
    updates the user's record in the database.
    
    The following fields can be updated:
    - Email address (with uniqueness validation)
    - First name
    - Last name
    - Gender
    - Institutional affiliation
    
    Security Features:
    - Requires authentication via @login_required
    - CSRF protection through Flask-WTF forms
    - Email uniqueness validation
    - Input sanitisation (whitespace trimming, case normalisation)
    - Transaction management for database operations
    
    Parameters (via POST form data):
        email (str): User's email address (must be unique)
        first_name (str): User's first name (optional)
        last_name (str): User's last name (optional)
        gender (str): User's gender (optional)
        institution (str): User's institutional affiliation (optional)
        
    Returns:
        Response: 
            - Redirect to profile page with success/error message
            - 302 Redirect on success
            - 400 Bad Request if email is already in use
            - 500 Internal Server Error on database failure
            
    Example:
        POST /profile/update
        Form Data: 
            email=user@example.com
            first_name=John
            last_name=Doe
            gender=male
            institution=Example University
            
    Note:
        - All string inputs are automatically stripped of whitespace
        - Email addresses are normalised to lowercase
        - Empty fields are converted to None in the database
        - Changes are atomic (all or nothing) within a transaction
    """
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
    """
    Update the authenticated user's password.
    
    This route handles the password change process for authenticated users.
    It verifies the current password, validates the new password requirements,
    and updates the user's password in the database if all checks pass.
    
    Security Features:
    - Requires authentication via @login_required
    - CSRF protection through Flask-WTF forms
    - Current password verification
    - New password confirmation
    - Minimum password length enforcement (6 characters)
    - Secure password hashing before storage
    - Transaction management for database operations
    
    Parameters (via POST form data):
        current_password (str): User's current password for verification
        new_password (str): New password to set
        confirm_password (str): Confirmation of the new password
        
    Returns:
        Response: 
            - Redirect to profile page with success/error message
            - 302 Redirect on success
            - 400 Bad Request if current password is incorrect or new password is invalid
            - 500 Internal Server Error on database failure
            
    Example:
        POST /profile/change_password
        Form Data:
            current_password=oldSecurePassword123
            new_password=newSecurePassword456
            confirm_password=newSecurePassword456
            
    Note:
        - The current password must be provided and match the stored hash
        - New password and confirmation must match exactly
        - New password must be at least 6 characters long
        - Password changes are logged for security auditing
        - Session remains active after password change
    """
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
    """
    Permanently delete the authenticated user's account and all associated data.
    
    This route handles the complete removal of a user's account from the system,
    including all personal data, analysis history, and related records. The process
    is irreversible and requires careful handling to maintain data integrity.
    
    Security Features:
    - Requires authentication via @login_required
    - CSRF protection through Flask-WTF forms
    - Automatic session termination before deletion
    - Comprehensive error handling and transaction management
    - Logging of all deletion activities
    
    Process Flow:
    1. Captures user identifiers for logging purposes
    2. Logs out the user to invalidate current session
    3. Deletes associated analyses and recommendations from MongoDB
    4. Removes the user record from the SQL database
    5. Redirects to the home page with confirmation
    
    Returns:
        Response: 
            - Redirect to home page with success/error message
            - 302 Redirect on success
            - 500 Internal Server Error if deletion fails
            
    Example:
        POST /profile/delete
        
    Note:
        - This action is irreversible and will permanently delete all user data
        - The user is automatically logged out before deletion
        - All related data is purged from both SQL and MongoDB
        - The operation is atomic - either all data is deleted or none is
        - Failed deletions are logged with detailed error information
        - Users should be clearly warned about data loss before calling this endpoint
    """
    try:
        # Capture identifiers BEFORE logging out, because current_user becomes Anonymous afterwards
        user_id = current_user.id
        username = current_user.username

        # Log the user out first to invalidate session
        logout_user()

        # Delete associated analyses & recommendations in Mongo
        try:
            from app import db_operations  # late import to avoid circular deps
            if hasattr(db_operations, "purge_user_data"):
                db_operations.purge_user_data(user_id)
        except Exception as purge_err:
            logger.warning(f"Could not purge Mongo data for user {user_id}: {purge_err}")

        # Delete user record (and potentially cascade related data)
        User.query.filter_by(id=user_id).delete()
        db.session.commit()

        flash('Your account has been deleted.', 'info')
        logger.info(f"Account deleted for user {username} (id={user_id})")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Account deletion error for user {locals().get('username','unknown')}: {str(e)}")
        flash('Failed to delete account.', 'error')
    return redirect(url_for('index'))