"""
Database Abstraction Layer for PolicyCraft AI Policy Analysis Platform.

This package provides a unified interface for database operations, abstracting away
the underlying database implementations and providing consistent access patterns
for both SQL and NoSQL data storage.

Key Components:
- models.py: SQLAlchemy ORM models for structured data storage
- mongo_operations.py: MongoDB operations for document storage and retrieval
- Database connection management
- Data validation and transformation utilities

Features:
- Seamless integration with both SQL and NoSQL databases
- Connection pooling and session management
- Transaction support with proper error handling
- Data validation and sanitisation
- Query building and optimisation

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University

Dependencies:
- SQLAlchemy for SQL database operations
- PyMongo for MongoDB interactions
- Flask-SQLAlchemy for Flask integration
- Marshmallow for data serialisation/deserialisation

Example Usage:
    from database import db, init_db
    from database.models import User, Analysis
    from database.mongo_operations import MongoOperations
    
    # Initialise database connections
    app = Flask(__name__)
    init_db(app)
    
    # Example SQL query
    users = User.query.filter_by(active=True).all()
    
    # Example MongoDB operation
    mongo = MongoOperations()
    results = mongo.find_documents('analysis', {'status': 'completed'})

Note:
    This module is a critical component of the PolicyCraft AI Policy Analysis Platform
    and handles all data persistence requirements for the application.
"""

# Import key components for easier access
from .models import db, init_db
from .mongo_operations import MongoOperations

__all__ = ['db', 'init_db', 'MongoOperations']
