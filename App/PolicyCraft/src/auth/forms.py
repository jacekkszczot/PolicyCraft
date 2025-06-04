"""
Authentication forms for PolicyCraft using WTForms.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from src.auth.models import User

class LoginForm(FlaskForm):
    """User login form."""
    
    username_or_email = StringField(
        'Username or Email',
        validators=[DataRequired(), Length(min=3, max=120)],
        render_kw={"placeholder": "Enter username or email"}
    )
    
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter password"}
    )
    
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    """User registration form."""
    
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"placeholder": "Choose username"}
    )
    
    email = EmailField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=120)],
        render_kw={"placeholder": "your.email@university.ac.uk"}
    )
    
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Create password"}
    )
    
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={"placeholder": "Confirm password"}
    )
    
    first_name = StringField('First Name', render_kw={"placeholder": "First name (optional)"})
    last_name = StringField('Last Name', render_kw={"placeholder": "Last name (optional)"})
    institution = StringField('Institution', render_kw={"placeholder": "Your institution (optional)"})
    
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
