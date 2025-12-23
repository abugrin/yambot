"""Tests for backward compatibility"""

import pytest
import warnings
from yambot import MessengerBot


class TestBackwardCompatibility:
    """Tests for deprecated methods and parameters"""
    
    def test_pool_interval_parameter_deprecated(self):
        """Test that pool_interval parameter shows deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bot = MessengerBot('test_token', pool_interval=2)
            
            # Check deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert 'pool_interval' in str(w[0].message)
            assert 'poll_interval' in str(w[0].message)
            
            # Check that value was set correctly
            assert bot._poll_interval == 2
    
    def test_poll_interval_parameter_no_warning(self):
        """Test that poll_interval parameter doesn't show warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bot = MessengerBot('test_token', poll_interval=3)
            
            # Check no deprecation warning
            assert len(w) == 0
            
            # Check that value was set correctly
            assert bot._poll_interval == 3
    
    def test_start_pooling_deprecated(self):
        """Test that start_pooling() shows deprecation warning"""
        bot = MessengerBot('test_token')
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Mock start_polling to avoid actual polling
            original_start_polling = bot.start_polling
            bot.start_polling = lambda: None
            
            try:
                bot.start_pooling()
                
                # Check deprecation warning was raised
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert 'start_pooling' in str(w[0].message)
                assert 'start_polling' in str(w[0].message)
            finally:
                bot.start_polling = original_start_polling
    
    def test_both_parameters_pool_wins(self):
        """Test that pool_interval takes precedence when both are provided"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bot = MessengerBot('test_token', poll_interval=3, pool_interval=5)
            
            # Check deprecation warning was raised
            assert len(w) == 1
            
            # pool_interval should take precedence
            assert bot._poll_interval == 5

