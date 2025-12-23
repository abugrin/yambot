"""Tests for type models"""

import pytest
from yambot.types import (
    Sender, Chat, File, Image, Button, User, Vote, 
    Sticker, ForwardedMessage, Update, UpdatesResponse
)


class TestSender:
    """Tests for Sender model"""
    
    def test_sender_with_login(self):
        """Test Sender with login"""
        sender = Sender(id='123', login='user@example.com', display_name='User')
        assert sender.login == 'user@example.com'
        assert sender.from_id == '123'
        assert sender.display_name == 'User'
    
    def test_sender_without_login(self):
        """Test Sender without login (channel)"""
        sender = Sender(id='channel_123', display_name='Channel')
        assert sender.from_id == 'channel_123'
        assert sender.login is None


class TestChat:
    """Tests for Chat model"""
    
    def test_private_chat(self):
        """Test private chat"""
        chat = Chat(type='private')
        assert chat.chat_type == 'private'
        assert chat.chat_id is None
    
    def test_group_chat(self):
        """Test group chat"""
        chat = Chat(type='group', id='group_123', thread_id=456)
        assert chat.chat_type == 'group'
        assert chat.chat_id == 'group_123'
        assert chat.thread_id == 456


class TestButton:
    """Tests for Button model"""
    
    def test_button_creation(self):
        """Test button creation"""
        button = Button(text='Click me', callback_data={'cmd': '/test'})
        assert button.text == 'Click me'
        assert button.callback_data == {'cmd': '/test'}


class TestUser:
    """Tests for User model"""
    
    def test_user_creation(self):
        """Test user creation"""
        user = User(login='user@example.com')
        assert user.login == 'user@example.com'


class TestUpdate:
    """Tests for Update model"""
    
    def test_text_update(self):
        """Test text message update"""
        update_data = {
            'from': {'id': '123', 'login': 'user@example.com'},
            'chat': {'type': 'private'},
            'text': 'Hello',
            'timestamp': 1234567890,
            'message_id': 1,
            'update_id': 1
        }
        update = Update(**update_data)
        assert update.text == 'Hello'
        assert update.from_m.login == 'user@example.com'
        assert update.chat.chat_type == 'private'
    
    def test_update_with_images(self):
        """Test update with images"""
        update_data = {
            'from': {'id': '123', 'login': 'user@example.com'},
            'chat': {'type': 'private'},
            'timestamp': 1234567890,
            'message_id': 1,
            'update_id': 1,
            'images': [[
                {'file_id': 'img1', 'width': 100, 'height': 100},
                {'file_id': 'img2', 'width': 200, 'height': 200}
            ]]
        }
        update = Update(**update_data)
        assert len(update.images) == 1
        assert len(update.images[0]) == 2


class TestUpdatesResponse:
    """Tests for UpdatesResponse model"""
    
    def test_updates_response(self):
        """Test updates response"""
        response_data = {
            'ok': True,
            'updates': [
                {
                    'from': {'id': '123', 'login': 'user@example.com'},
                    'chat': {'type': 'private'},
                    'text': 'Hello',
                    'timestamp': 1234567890,
                    'message_id': 1,
                    'update_id': 1
                }
            ]
        }
        response = UpdatesResponse(**response_data)
        assert response.ok is True
        assert len(response.updates) == 1
        assert response.updates[0].text == 'Hello'

