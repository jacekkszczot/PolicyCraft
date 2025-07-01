"""
User models for PolicyCraft authentication system.
Defines User model, onboarding support, and database relationships.

Author: Jacek Robert Kszczot
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import json

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
        self.last_login = datetime.now(timezone.utc)
    
    def is_first_login(self):
        """Check if this is user's first login (needs onboarding)."""
        if not hasattr(self, '_onboarding_checked'):
            onboarding = UserOnboarding.query.filter_by(user_id=self.id).first()
            if not onboarding:
                # Create onboarding record for new user
                onboarding = UserOnboarding(user_id=self.id)
                db.session.add(onboarding)
                db.session.commit()
                self._onboarding_checked = True
                return True
            self._onboarding_checked = onboarding.is_completed
        return not self._onboarding_checked
    
    def complete_onboarding(self, selected_universities=None):
        """Mark onboarding as completed."""
        onboarding = UserOnboarding.query.filter_by(user_id=self.id).first()
        if onboarding:
            onboarding.is_completed = True
            onboarding.onboarding_completed_date = datetime.now(timezone.utc)
            if selected_universities:
                onboarding.set_selected_universities(selected_universities)
                onboarding.sample_policies_accepted = True
            db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserOnboarding(db.Model):
    """
    Track user onboarding progress and sample policy preferences.
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
    
    # Relationship
    user = db.relationship('User', backref=db.backref('onboarding', uselist=False))
    
    def __repr__(self):
        return f'<UserOnboarding {self.user_id}: completed={self.is_completed}>'
    
    def get_selected_universities(self):
        """Get list of selected universities from JSON string."""
        if self.selected_universities:
            try:
                return json.loads(self.selected_universities)
            except:
                return []
        return []
    
    def set_selected_universities(self, universities_list):
        """Set selected universities as JSON string."""
        self.selected_universities = json.dumps(universities_list)


# Sample universities with their policies
SAMPLE_UNIVERSITIES = {
    'oxford': {
        'name': 'University of Oxford',
        'country': 'UK',
        'file': 'oxford-ai-policy.pdf',
        'description': 'Comprehensive AI policy focusing on academic integrity and research ethics.',
        'classification': 'Moderate',
        'themes': ['Academic Integrity', 'AI Ethics', 'Research Guidelines']
    },
    'cambridge': {
        'name': 'University of Cambridge', 
        'country': 'UK',
        'file': 'cambridge-ai-policy.pdf',
        'description': 'Balanced approach to AI usage with emphasis on transparency.',
        'classification': 'Moderate',
        'themes': ['Transparency', 'Academic Standards', 'Innovation']
    },
    'mit': {
        'name': 'Massachusetts Institute of Technology',
        'country': 'USA', 
        'file': 'mit-ai-policy.pdf',
        'description': 'Innovation-focused policy encouraging responsible AI experimentation.',
        'classification': 'Permissive',
        'themes': ['Innovation', 'Research Excellence', 'Ethical AI']
    },
    'stanford': {
        'name': 'Stanford University',
        'country': 'USA',
        'file': 'stanford-ai-policy.pdf', 
        'description': 'Progressive policy promoting AI literacy and responsible usage.',
        'classification': 'Permissive',
        'themes': ['AI Literacy', 'Student Empowerment', 'Innovation']
    },
    'harvard': {
        'name': 'Harvard University',
        'country': 'USA',
        'file': 'harvard-ai-policy.pdf',
        'description': 'Rigorous policy emphasizing academic rigor and integrity.',
        'classification': 'Moderate', 
        'themes': ['Academic Rigor', 'Integrity', 'Governance']
    },
    'edinburgh': {
        'name': 'University of Edinburgh',
        'country': 'UK',
        'file': 'edinburgh university-ai-policy.pdf',
        'description': 'Research-focused policy with strong ethical framework.',
        'classification': 'Moderate',
        'themes': ['Research Ethics', 'AI Governance', 'Accountability']
    }
    ,
    'columbia': {
        'name': 'Columbia University',
        'country': 'USA',
        'file': 'columbia-ai-policy.pdf',
        'description': 'Comprehensive policy with strong disclosure requirements.',
        'classification': 'Moderate',
        'themes': ['Disclosure', 'Academic Integrity', 'Governance']
    },
    'chicago': {
        'name': 'University of Chicago',
        'country': 'USA',
        'file': 'chicago-ai-policy.docx',
        'description': 'Research-focused policy emphasizing academic rigor.',
        'classification': 'Restrictive',
        'themes': ['Research Ethics', 'Academic Rigor', 'Compliance']
    },
    'cornell': {
        'name': 'Cornell University',
        'country': 'USA',
        'file': 'cornell-ai-policy.docx',
        'description': 'Balanced approach with emphasis on student support.',
        'classification': 'Moderate',
        'themes': ['Student Support', 'Academic Excellence', 'Innovation']
    },
    'imperial': {
        'name': 'Imperial College London',
        'country': 'UK',
        'file': 'imperial-ai-policy.docx',
        'description': 'STEM-focused policy promoting responsible innovation.',
        'classification': 'Permissive',
        'themes': ['STEM Innovation', 'Research Excellence', 'Technology Ethics']
    },
    'belfast': {
        'name': 'Queens University Belfast',
        'country': 'UK',
        'file': 'belfast university-ai-policy.pdf',
        'description': 'Regional university approach with practical guidelines.',
        'classification': 'Moderate',
        'themes': ['Practical Guidelines', 'Regional Standards', 'Academic Integrity']
    },
    'jagiellonian': {
        'name': 'Jagiellonian University',
        'country': 'Poland',
        'file': 'jagiellonian university-ai-policy.pdf',
        'description': 'European perspective on AI ethics and governance.',
        'classification': 'Moderate',
        'themes': ['European Standards', 'AI Ethics', 'International Compliance']
    },
    'leeds_trinity': {
        'name': 'Leeds Trinity University',
        'country': 'UK',
        'file': 'leeds trinity university-ai-policy.pdf',
        'description': 'Teaching-focused institution policy with student-centered approach.',
        'classification': 'Moderate',
        'themes': ['Student-Centered', 'Teaching Excellence', 'Practical Application']
    },
    'tokyo': {
        'name': 'University of Tokyo',
        'country': 'Japan',
        'file': 'tokyo-ai-policy.docx',
        'description': 'Asian perspective on AI integration in higher education.',
        'classification': 'Moderate',
        'themes': ['Asian Standards', 'Technology Integration', 'Cultural Considerations']
    },
    'unknown_2': {
        'name': 'Research University Sample 2',
        'country': 'International',
        'file': '2-ai-policy.pdf',
        'description': 'Additional sample policy for comparative analysis.',
        'classification': 'Moderate',
        'themes': ['Comparative Analysis', 'Research Standards', 'Policy Framework']
    }
}


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
        print("✅ Created default admin user: admin/admin123")
    
    print("✅ Database initialized with onboarding support")
    print(f"✅ Sample universities available: {len(SAMPLE_UNIVERSITIES)}")
