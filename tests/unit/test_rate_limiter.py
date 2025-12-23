"""Tests for rate limiter"""

import pytest
import time
from yambot.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter class"""
    
    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter(max_rps=10)
        
        # Should allow 10 requests immediately
        for _ in range(10):
            assert limiter.acquire(timeout=1.0) is True
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test that rate limiter blocks requests exceeding limit"""
        limiter = RateLimiter(max_rps=5)
        
        # Use up all tokens
        for _ in range(5):
            assert limiter.acquire(timeout=0.1) is True
        
        # Next request should timeout
        assert limiter.acquire(timeout=0.1) is False
    
    def test_rate_limiter_resets_after_time(self):
        """Test that rate limiter allows requests after time passes"""
        limiter = RateLimiter(max_rps=5)
        
        # Use up all tokens
        for _ in range(5):
            limiter.acquire()
        
        # Wait for tokens to refresh
        time.sleep(1.1)
        
        # Should allow requests again
        assert limiter.acquire(timeout=0.1) is True
    
    def test_rate_limiter_reset(self):
        """Test manual reset of rate limiter"""
        limiter = RateLimiter(max_rps=5)
        
        # Use up all tokens
        for _ in range(5):
            limiter.acquire()
        
        # Reset
        limiter.reset()
        
        # Should allow requests again
        assert limiter.acquire(timeout=0.1) is True

