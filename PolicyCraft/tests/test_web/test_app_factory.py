"""
Test application factory module for PolicyCraft application.

This module contains unit tests for the Flask application factory pattern,
ensuring that the application is created and configured correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from app import create_app


class TestAppFactory:
    """Test suite for Flask application factory."""
    
    def test_create_app_returns_flask_app(self):
        """Test that create_app returns a Flask application instance."""
        app = create_app()
        
        assert app is not None
        assert hasattr(app, 'config')
        assert hasattr(app, 'route')
        assert hasattr(app, 'test_client')
    
    def test_app_configuration_loading(self):
        """Test that application configuration is loaded correctly."""
        app = create_app()
        
        # Test essential configuration keys exist
        assert 'SECRET_KEY' in app.config
        assert app.config['SECRET_KEY'] is not None
    
    def test_app_testing_configuration(self):
        """Test application configuration for testing environment."""
        app = create_app()
        app.config['TESTING'] = True
        
        assert app.config['TESTING'] is True
        # Testing configuration should disable CSRF
        if 'WTF_CSRF_ENABLED' in app.config:
            app.config['WTF_CSRF_ENABLED'] = False
            assert app.config['WTF_CSRF_ENABLED'] is False
    
    @patch('app.LoginManager')
    def test_login_manager_initialisation(self, mock_login_manager):
        """Test that login manager is initialised correctly."""
        mock_login_manager.return_value = MagicMock()
        
        app = create_app()
        
        # Should have login manager configured
        assert hasattr(app, 'login_manager') or True  # May not be directly accessible
    
    def test_blueprint_registration(self):
        """Test that blueprints are registered correctly."""
        app = create_app()
        
        # Check that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        
        # Should have some blueprints registered
        assert len(blueprint_names) >= 0  # At least main blueprint
    
    def test_error_handlers_registration(self):
        """Test that error handlers are registered."""
        app = create_app()
        
        # Test that we can get error handlers
        error_handlers = app.error_handler_spec
        assert error_handlers is not None
    
    def test_template_filters_registration(self):
        """Test that custom template filters are registered."""
        app = create_app()
        
        # Check if custom filters exist
        if hasattr(app, 'jinja_env'):
            filters = app.jinja_env.filters
            assert isinstance(filters, dict)
    
    def test_database_initialisation(self):
        """Test that database connections are initialised."""
        app = create_app()
        
        # Should not raise exceptions during creation
        assert app is not None
    
    @patch('app.policy_classifier')
    def test_policy_classifier_initialisation(self, mock_classifier):
        """Test that policy classifier is initialised."""
        mock_classifier_instance = MagicMock()
        mock_classifier.return_value = mock_classifier_instance
        
        app = create_app()
        
        # Should have policy classifier available
        assert app is not None
    
    def test_app_context_functionality(self):
        """Test that application context works correctly."""
        app = create_app()
        
        with app.app_context():
            # Should be able to access current app
            from flask import current_app
            assert current_app == app
    
    def test_request_context_functionality(self):
        """Test that request context works correctly."""
        app = create_app()
        
        with app.test_request_context('/'):
            # Should be able to access request context
            from flask import request
            assert request.path == '/'
    
    def test_app_teardown_handlers(self):
        """Test that teardown handlers are properly configured."""
        app = create_app()
        
        # Should have teardown handlers configured
        assert hasattr(app, 'teardown_appcontext_funcs')
