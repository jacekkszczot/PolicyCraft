"""
Test configuration module for PolicyCraft application.

This module contains unit tests for the configuration settings,
ensuring that all environment variables and configuration options
are properly loaded and validated.
"""

import os
import pytest
from unittest.mock import patch

from config import Config


class TestConfig:
    """Test suite for application configuration."""
    
    def test_default_configuration(self):
        """Test that default configuration values are set correctly."""
        config = Config()
        
        # Test that essential attributes exist
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'MONGODB_SETTINGS')
        assert config.SECRET_KEY is not None
        assert config.MONGODB_SETTINGS is not None
    
    def test_mongodb_configuration(self):
        """Test MongoDB configuration settings."""
        config = Config()
        mongodb_settings = config.MONGODB_SETTINGS
        
        assert isinstance(mongodb_settings, dict)
        assert 'db' in mongodb_settings
    
    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret_key'})
    def test_environment_variable_override(self):
        """Test that environment variables properly override defaults."""
        config = Config()
        assert config.SECRET_KEY == 'test_secret_key'
    
    def test_security_configuration(self):
        """Test security-related configuration."""
        config = Config()
        
        # Ensure SECRET_KEY meets minimum security requirements
        assert config.SECRET_KEY is not None
        assert len(str(config.SECRET_KEY)) >= 8
