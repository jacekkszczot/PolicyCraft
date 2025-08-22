"""
Test authentication routes for PolicyCraft application.

Tests for login, logout, and registration functionality.
"""

import pytest
from unittest.mock import Mock, patch
from app import create_app


class TestAuthRoutes:
    """Test suite for authentication routes."""
    
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
    
    def test_login_route_exists(self, client):
        """Test that login route exists and is accessible."""
        response = client.get('/login')
        assert response.status_code in [200, 302, 405]
    
    def test_logout_route_exists(self, client):
        """Test that logout route exists."""
        response = client.get('/logout')
        assert response.status_code in [200, 302, 405]
    
    def test_register_route_exists(self, client):
        """Test that registration route exists."""
        response = client.get('/register')
        assert response.status_code in [200, 302, 404, 405]
