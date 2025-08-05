"""
Authentication and User Management Forms for PolicyCraft.

This module defines the web forms used for user authentication and account management
in the PolicyCraft application. It utilises WTForms for form handling and validation,
ensuring data integrity and security throughout the user authentication process.

Forms include:
- LoginForm: Handles user authentication with email and password
- RegistrationForm: Manages new user account creation with comprehensive validation

All forms implement server-side validation and include client-side validation hints
for an enhanced user experience.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from src.database.models import User

class LoginForm(FlaskForm):
    """
    Form for user authentication in the PolicyCraft application.
    
    This form handles the collection and validation of user credentials during the
    login process. It implements server-side validation and includes client-side
    validation hints for an optimal user experience.
    
    Attributes:
        username_or_email (StringField): Field for user's email address. Must be
            between 3 and 120 characters in length. Required field.
            
        password (PasswordField): Field for the user's password. Required field.
            
        remember_me (BooleanField): Optional checkbox to enable persistent login
            sessions. When selected, the user remains logged in across browser
            sessions until explicitly logging out.
            
        submit (SubmitField): Button to submit the login form.
            
    Example:
        form = LoginForm()
        if form.validate_on_submit():
            # Process login logic here
            user = authenticate_user(form.username_or_email.data, form.password.data)
    """
    
    username_or_email = StringField(
        'Email',
        validators=[DataRequired(), Length(min=3, max=120)],
        render_kw={"placeholder": "Enter email address"}
    )
    
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Enter password",
            "autocomplete": "current-password"
        }
    )
    
    remember_me = BooleanField(
        'Remember me',
        default=False,
        description="Keep me logged in on this device"
    )
    
    submit = SubmitField(
        'Log In',
        render_kw={"class": "btn btn-primary btn-block"}
    )

class RegistrationForm(FlaskForm):
    """
    Form for new user registration in the PolicyCraft application.
    
    This form collects and validates all necessary information for creating a new user account.
    It includes comprehensive validation for each field to ensure data integrity and security.
    
    Attributes:
        gender (SelectField): User's gender selection. Required field with predefined options.
        
        email (EmailField): User's email address. Must be unique and follow email format.
            Serves as the primary identifier for the user account.
            
        password (PasswordField): User's chosen password. Must meet complexity requirements:
            - Minimum 8 characters
            - At least one lowercase letter
            - At least one uppercase letter
            - At least one digit
            - At least one special character
            
        password_confirm (PasswordField): Confirmation field for the password.
            Must match the password field exactly.
            
        first_name (StringField): User's first name. Required field.
        
        last_name (StringField): User's last name. Required field.
        
        institution (StringField): User's educational or professional institution.
            Required field to ensure proper affiliation tracking.
            
        submit (SubmitField): Button to submit the registration form.
    
    Methods:
        validate_email: Ensures the provided email is not already registered in the system.
    
    Example:
        form = RegistrationForm()
        if form.validate_on_submit():
            # Process registration logic here
            user = create_user(
                email=form.email.data,
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                institution=form.institution.data,
                gender=form.gender.data
            )
    """
    
    email = EmailField(
        'Email',
        validators=[
            DataRequired(message='Email address is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email cannot exceed 120 characters')
        ],
        render_kw={
            "placeholder": "your.email@university.ac.uk",
            "autocomplete": "email"
        }
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(
                min=8,
                message='Password must be at least 8 characters long.'
            ),
            Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$',
                message=(
                    'Password must contain at least one lowercase letter, '
                    'one uppercase letter, one digit, and one special character.'
                )
            )
        ],
        render_kw={
            "placeholder": "Create a strong password",
            "autocomplete": "new-password"
        },
        description=(
            'Password must be at least 8 characters long and include uppercase, '
            'lowercase, numbers, and special characters.'
        )
    )
    
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={
            "placeholder": "Re-enter your password",
            "autocomplete": "new-password"
        }
    )
    
    first_name = StringField(
        'First Name',
        validators=[
            DataRequired(message='First name is required'),
            Length(max=50, message='First name cannot exceed 50 characters')
        ],
        render_kw={
            "placeholder": "First name",
            "autocomplete": "given-name"
        }
    )
    
    last_name = StringField(
        'Last Name',
        validators=[
            DataRequired(message='Last name is required'),
            Length(max=50, message='Last name cannot exceed 50 characters')
        ],
        render_kw={
            "placeholder": "Last name",
            "autocomplete": "family-name"
        }
    )
    
    institution = StringField(
        'Institution',
        validators=[
            DataRequired(message='Institution is required'),
            Length(max=200, message='Institution name is too long')
        ],
        render_kw={
            "placeholder": "University / Institution",
            "autocomplete": "organization"
        }
    )
    
    submit = SubmitField(
        'Create Account',
        render_kw={"class": "btn btn-primary btn-block"}
    )
    
    def validate_email(self, email):
        """
        Validate that the provided email is not already registered.
        
        Args:
            email (str): The email address to validate.
            
        Raises:
            ValidationError: If the email is already associated with an existing account.
            
        Note:
            This validation is case-insensitive to prevent duplicate accounts with
            the same email address in different cases.
        """
        if User.query.filter_by(email=email.data.lower()).first() is not None:
            raise ValidationError('This email address is already registered. Please use a different email or log in.')