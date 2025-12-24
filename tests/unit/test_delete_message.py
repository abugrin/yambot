"""Tests for delete_message method"""

import pytest
from unittest.mock import Mock, patch
from yambot import MessengerBot, ValidationError


class TestDeleteMessage:
    """Tests for delete_message method"""
    
    def setup_method(self):
        """Setup test bot"""
        self.bot = MessengerBot('test_token')
    
    def test_delete_message_with_chat_id(self):
        """Test deleting message in group chat with chat_id"""
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True, 'message_id': 999}
        
        with patch.object(self.bot, '_make_request', return_value=mock_response) as mock_request:
            result = self.bot.delete_message(message_id=999, chat_id='0/0/group_123')
            
            # Check that request was made
            assert mock_request.called
            
            # Get the body argument
            call_args = mock_request.call_args
            body = call_args[1]['json']
            
            # Verify body contains chat_id and message_id
            assert 'chat_id' in body
            assert body['chat_id'] == '0/0/group_123'
            assert body['message_id'] == 999
            
            # Verify body does NOT contain login
            assert 'login' not in body
            
            # Verify result
            assert result['ok'] is True
            assert result['message_id'] == 999
    
    def test_delete_message_with_login(self):
        """Test deleting message in private chat with login"""
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True, 'message_id': 777}
        
        with patch.object(self.bot, '_make_request', return_value=mock_response) as mock_request:
            result = self.bot.delete_message(message_id=777, login='user@example.com')
            
            call_args = mock_request.call_args
            body = call_args[1]['json']
            
            # Verify body contains login and message_id
            assert 'login' in body
            assert body['login'] == 'user@example.com'
            assert body['message_id'] == 777
            
            # Verify body does NOT contain chat_id
            assert 'chat_id' not in body
            
            # Verify result
            assert result['ok'] is True
    
    def test_delete_message_with_thread_id(self):
        """Test deleting message in thread with chat_id and thread_id"""
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True, 'message_id': 666}
        
        with patch.object(self.bot, '_make_request', return_value=mock_response) as mock_request:
            result = self.bot.delete_message(
                message_id=666, 
                chat_id='0/0/group_123', 
                thread_id=456
            )
            
            call_args = mock_request.call_args
            body = call_args[1]['json']
            
            # Verify body contains chat_id, thread_id, and message_id
            assert 'chat_id' in body
            assert body['chat_id'] == '0/0/group_123'
            assert 'thread_id' in body
            assert body['thread_id'] == 456
            assert body['message_id'] == 666
            
            # Verify body does NOT contain login
            assert 'login' not in body
    
    def test_delete_message_both_chat_id_and_login_raises_error(self):
        """Test that providing both chat_id and login raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.bot.delete_message(
                message_id=123, 
                chat_id='0/0/group_123', 
                login='user@example.com'
            )
        
        assert 'mutually exclusive' in str(exc_info.value).lower()
    
    def test_delete_message_neither_chat_id_nor_login_raises_error(self):
        """Test that providing neither chat_id nor login raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.bot.delete_message(message_id=123)
        
        assert 'must be provided' in str(exc_info.value).lower()
    
    def test_delete_message_thread_without_chat_id_raises_error(self):
        """Test that thread_id without chat_id raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.bot.delete_message(message_id=123, thread_id=456)
        
        assert 'must be provided' in str(exc_info.value).lower()
    
    def test_delete_message_with_login_ignores_thread_id(self):
        """Test that thread_id is not sent when using login"""
        mock_response = Mock()
        mock_response.json.return_value = {'ok': True, 'message_id': 888}
        
        with patch.object(self.bot, '_make_request', return_value=mock_response) as mock_request:
            # thread_id should be ignored when using login
            result = self.bot.delete_message(
                message_id=888, 
                login='user@example.com',
                thread_id=999  # This should be ignored
            )
            
            call_args = mock_request.call_args
            body = call_args[1]['json']
            
            # Verify body contains only login and message_id
            assert 'login' in body
            assert body['login'] == 'user@example.com'
            assert body['message_id'] == 888
            
            # Verify thread_id is NOT in body (ignored for private chats)
            assert 'thread_id' not in body
            assert 'chat_id' not in body

