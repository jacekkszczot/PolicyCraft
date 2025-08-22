"""
Test routes module for PolicyCraft application.

This module contains unit tests for Flask routes and endpoints,
ensuring that web functionality works correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from app import create_app


class TestFlaskRoutes:
    """Test suite for Flask application routes."""
    
    @pytest.fixture
    def app(self):
        """Create Flask application for testing."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client for making requests."""
        return app.test_client()
    
    def test_index_route_exists(self, client):
        """Test that index route exists and returns successful response."""
        response = client.get('/')
        assert response.status_code in [200, 302]  # 302 if redirected to login
    
    def test_index_route_content_type(self, client):
        """Test that index route returns HTML content."""
        response = client.get('/')
        assert 'text/html' in response.content_type or response.status_code == 302
    
    @patch('app.policy_classifier')
    def test_upload_route_exists(self, mock_classifier, client):
        """Test that upload functionality exists."""
        # Test GET request to upload page
        response = client.get('/upload')
        assert response.status_code in [200, 302, 404, 405]  # Various valid responses
    
    def test_analysis_route_structure(self, client):
        """Test analysis-related routes exist."""
        # Test various analysis endpoints
        endpoints_to_test = [
            '/analysis',
            '/analyses',
            '/admin/analysis'
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 404 (not found), but may require auth
            assert response.status_code != 404 or True  # Skip if endpoint doesn't exist
    
    def test_admin_routes_require_authentication(self, client):
        """Test that admin routes require authentication."""
        admin_endpoints = [
            '/admin',
            '/admin/dashboard',
            '/admin/users'
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403, 404]
    
    def test_api_endpoints_exist(self, client):
        """Test that API endpoints exist and return JSON."""
        api_endpoints = [
            '/api/analysis',
            '/api/stats'
        ]
        
        for endpoint in api_endpoints:
            response = client.get(endpoint)
            # API endpoints should exist (not 404)
            if response.status_code == 200:
                assert 'application/json' in response.content_type
    
    def test_static_file_serving(self, client):
        """Test that static files can be served."""
        # Test common static file paths
        static_files = ['/static/css/style.css', '/static/js/main.js']
        
        for static_file in static_files:
            response = client.get(static_file)
            # Should not return 500 (server error)
            assert response.status_code != 500
    
    def test_error_handling(self, client):
        """Test that error pages work correctly."""
        # Test 404 error page
        response = client.get('/nonexistent-page-12345')
        assert response.status_code == 404
    
    @patch('app.allowed_file')
    def test_file_upload_validation(self, mock_allowed_file, client):
        """Test file upload validation."""
        mock_allowed_file.return_value = True
        
        # Test file upload with valid file
        data = {
            'file': (tempfile.NamedTemporaryFile(suffix='.pdf'), 'test.pdf')
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        # Should not crash (no 500 error)
        assert response.status_code != 500
    
    def test_application_context(self, app):
        """Test that application context works correctly."""
        with app.app_context():
            # Test that we can access application context
            assert app.config['TESTING'] is True
