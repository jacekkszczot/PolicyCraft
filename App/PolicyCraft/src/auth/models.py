"""
User models for PolicyCraft authentication system.
Defines User model and database relationships.

Author: Jacek Robert Kszczot
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model for authentication and session management.
    Implements Flask-Login UserMixin for session handling.
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
    
    def __init__(self, username, email, password, **kwargs):
        """Initialise new user with hashed password."""
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
        self.last_login = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.username}>'

def init_db(app):
    """
    Initialise database tables and create default admin user.
    Note: db.init_app(app) should be called before this function.
    
    Args:
        app: Flask application instance
    """
    # Create all tables
    db.create_all()
    
    # Create default admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@policycraft.com',
            password='admin123',  # Change this in production!
            first_name='Admin',
            last_name='User',
            role='admin',
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin/admin123")
