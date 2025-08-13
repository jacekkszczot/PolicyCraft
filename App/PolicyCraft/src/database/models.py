"""
Database models for PolicyCraft AI Policy Analysis Platform.

This module defines all database models and provides database initialization.
It uses SQLAlchemy ORM for database operations.

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import json

# Sample universities data used for onboarding and baseline policies
SAMPLE_UNIVERSITIES = {
    "oxford": {
        "name": "University of Oxford",
        "file": "oxford-ai-policy.pdf",
        "country": "UK",
        "themes": ["Ethics", "Governance", "Transparency"],
        "classification": "Moderate"
    },
    "cambridge": {
        "name": "University of Cambridge",
        "file": "cambridge-ai-policy.pdf",
        "country": "UK",
        "themes": ["Ethics", "Research", "Education"],
        "classification": "Moderate"
    },
    "cambridge_docx": {
        "name": "University of Cambridge",
        "file": "cambridge-ai-policy.docx",
        "country": "UK",
        "themes": ["Ethics", "Research", "Education"],
        "classification": "Moderate"
    },
    "imperial": {
        "name": "Imperial College London",
        "file": "imperial-ai-policy.docx",
        "country": "UK",
        "themes": ["Research", "Innovation", "Governance"],
        "classification": "Permissive"
    },
    "edinburgh": {
        "name": "University of Edinburgh",
        "file": "edinburgh university-ai-policy.pdf",
        "country": "UK",
        "themes": ["Ethics", "Governance", "Research"],
        "classification": "Moderate"
    },
    "leeds": {
        "name": "Leeds Trinity University",
        "file": "leeds trinity university-ai-policy.pdf",
        "country": "UK",
        "themes": ["Education", "Ethics", "Student Support"],
        "classification": "Restrictive"
    },
    "harvard": {
        "name": "Harvard University",
        "file": "harvard-ai-policy.pdf",
        "country": "USA",
        "themes": ["Research", "Ethics", "Innovation"],
        "classification": "Permissive"
    },
    "mit": {
        "name": "MIT",
        "file": "mit-ai-policy.pdf",
        "country": "USA",
        "themes": ["Innovation", "Research", "Ethics"],
        "classification": "Permissive"
    },
    "stanford": {
        "name": "Stanford University",
        "file": "stanford-ai-policy.pdf",
        "country": "USA",
        "themes": ["Research", "Education", "Ethics"],
        "classification": "Moderate"
    },
    "tokyo": {
        "name": "University of Tokyo",
        "file": "tokyo-ai-policy.docx",
        "country": "Japan",
        "themes": ["Research", "Innovation", "Cultural Context"],
        "classification": "Permissive"
    },
    "jagiellonian": {
        "name": "Jagiellonian University",
        "file": "jagiellonian university-ai-policy.pdf",
        "country": "Poland",
        "themes": ["Education", "Ethics", "European Context"],
        "classification": "Restrictive"
    },
    "belfast": {
        "name": "Belfast University",
        "file": "belfast university-ai-policy.pdf",
        "country": "UK",
        "themes": ["Education", "Ethics", "Student Support"],
        "classification": "Restrictive"
    },
    "chicago": {
        "name": "University of Chicago",
        "file": "chicago-ai-policy.docx",
        "country": "USA",
        "themes": ["Research", "Ethics", "Innovation"],
        "classification": "Moderate"
    },
    "columbia": {
        "name": "Columbia University",
        "file": "columbia-ai-policy.pdf",
        "country": "USA",
        "themes": ["Research", "Ethics", "Innovation"],
        "classification": "Moderate"
    },
    "cornell": {
        "name": "Cornell University",
        "file": "cornell-ai-policy.docx",
        "country": "USA",
        "themes": ["Research", "Education", "Ethics"],
        "classification": "Moderate"
    },
    "liverpool": {
        "name": "University of Liverpool",
        "file": "liverpool policy-ai-policy.pdf",
        "country": "UK",
        "themes": ["Education", "Ethics", "Student Support"],
        "classification": "Moderate"
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Comprehensive user model for authentication, authorization, and profile management.
    
    This class serves as the foundation for user accounts within the PolicyCraft application,
    providing secure authentication through password hashing and session management via
    Flask-Login's UserMixin. It stores essential user information, authentication details,
    and account status.
    
    The model is designed to be extensible while maintaining data integrity through
    appropriate constraints and relationships with other system components.
    """
    __tablename__ = 'users'
    
    # Primary key and identification
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # Authentication fields
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    institution = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(50), default='user')
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    onboarding = db.relationship('UserOnboarding', backref='user', uselist=False)
    
    def __init__(self, username, email, password, **kwargs):
        """Initialize a new user and persist the password hash securely."""
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.institution = kwargs.get('institution')
        self.role = kwargs.get('role', 'user')
    
    def set_password(self, password):
        """Hash and store user password securely."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify user password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name or username."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def update_last_login(self):
        """Update user's last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
    
    def is_first_login(self):
        """Check if this is the user's first login (requires onboarding)."""
        if not self.onboarding:
            # Create onboarding record for new user
            self.onboarding = UserOnboarding(user_id=self.id)
            db.session.add(self.onboarding)
            db.session.commit()
            return True
        # Return True only if onboarding is NOT completed
        return not self.onboarding.is_completed
    
    def complete_onboarding(self, selected_universities=None):
        """Mark onboarding as completed."""
        if self.onboarding:
            self.onboarding.is_completed = True
            self.onboarding.onboarding_completed_date = datetime.now(timezone.utc)
            if selected_universities:
                self.onboarding.set_selected_universities(selected_universities)
                self.onboarding.sample_policies_accepted = True
            db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserOnboarding(db.Model):
    """
    Tracks and manages user progress through the PolicyCraft onboarding process.
    
    This model records a user's journey through the initial setup and familiarisation
    with the PolicyCraft platform. It stores information about which sample policies
    have been presented to the user, their selections, and completion status of
    various onboarding steps.
    
    The model supports a multi-step onboarding process where users can be introduced
    to the platform's features gradually, with their progress being saved between
    sessions.
    """
    __tablename__ = 'user_onboarding'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Onboarding status
    is_completed = db.Column(db.Boolean, default=False)
    sample_policies_offered = db.Column(db.Boolean, default=False)
    sample_policies_accepted = db.Column(db.Boolean, default=False)
    selected_universities = db.Column(db.Text)  # JSON string of selected universities
    
    # Timestamps
    first_login_date = db.Column(db.DateTime, default=datetime.utcnow)
    onboarding_completed_date = db.Column(db.DateTime)
    
    def get_selected_universities(self):
        """Get list of selected universities from JSON string."""
        if self.selected_universities:
            try:
                return json.loads(self.selected_universities)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_selected_universities(self, universities_list):
        """Store list of selected universities as JSON string."""
        self.selected_universities = json.dumps(universities_list)
    
    def __repr__(self):
        return f'<UserOnboarding {self.user_id}: completed={self.is_completed}>'


def init_db(app):
    """Initialize the database connection and create tables.
    
    This function creates all required tables and sets up the initial admin user.
    It should be called during application startup after db.init_app(app).
    
    Args:
        app: The Flask application instance
    """
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Create default admin user if none exists
        admin = User.query.filter_by(email='admin@policycraft.ai').first()
        if not admin and app.config.get('DEFAULT_ADMIN_PASSWORD'):
            admin = User(
                username='admin',
                email='admin@policycraft.ai',
                password=app.config['DEFAULT_ADMIN_PASSWORD'],
                first_name='Admin',
                last_name='User',
                role='admin',
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
    
    return db