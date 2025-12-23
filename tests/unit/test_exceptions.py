"""Tests for custom exceptions"""

import pytest
from yambot.exceptions import (
    YambotError, APIError, RateLimitError, 
    ValidationError, AuthenticationError
)


class TestExceptions:
    """Tests for custom exception classes"""
    
    def test_yambot_error(self):
        """Test base YambotError"""
        error = YambotError('Test error')
        assert str(error) == 'Test error'
        assert isinstance(error, Exception)
    
    def test_api_error(self):
        """Test APIError"""
        error = APIError(404, 'Not found')
        assert error.status_code == 404
        assert error.message == 'Not found'
        assert 'API Error 404' in str(error)
        assert isinstance(error, YambotError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError()
        assert error.status_code == 429
        assert 'Rate limit exceeded' in error.message
        assert isinstance(error, APIError)
    
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError('Invalid input')
        assert str(error) == 'Invalid input'
        assert isinstance(error, YambotError)
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError()
        assert error.status_code == 401
        assert 'Authentication failed' in error.message
        assert isinstance(error, APIError)

