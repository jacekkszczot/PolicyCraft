"""
Authentication forms for PolicyCraft using WTForms.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from src.auth.models import User

class LoginForm(FlaskForm):
    """User login form."""
    
    username_or_email = StringField(
        'Email',
        validators=[DataRequired(), Length(min=3, max=120)],
        render_kw={"placeholder": "Enter email address"}
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
    
    gender = SelectField(
        'Gender',
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        validators=[DataRequired()]
    )

    # Email will serve as both login and unique identifier

    
    email = EmailField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=120)],
        render_kw={"placeholder": "your.email@university.ac.uk"}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters.'),
            Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$',
                message='Password must contain lowercase, uppercase, number and special character.'
            )
        ],
        render_kw={"placeholder": "Create password"}
    )
    
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={"placeholder": "Confirm password"}
    )
    
    first_name = StringField('First Name', validators=[DataRequired()], render_kw={"placeholder": "First name"})
    last_name = StringField('Last Name', validators=[DataRequired()], render_kw={"placeholder": "Last name"})
    institution = StringField('Institution', validators=[DataRequired()], render_kw={"placeholder": "University / Institution"})
    
    submit = SubmitField('Create Account')
    


    
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')