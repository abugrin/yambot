"""Tests for type models"""

import pytest
from yambot.types import (
    Sender, Chat, File, Image, Button, User, Vote, 
    Sticker, ForwardedMessage, Update, UpdatesResponse,
    OpenUriDirective, SendMessageDirective, ServerActionDirective,
    SetElementsStateDirective, InlineSuggestButton, SuggestButtons,
    ServerAction, BotRequestError, BotRequest,
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


class TestDirectives:
    """Tests for Directive types"""

    def test_open_uri_directive(self):
        d = OpenUriDirective(uri='https://example.com')
        assert d.type == 'open_uri'
        assert d.uri == 'https://example.com'

    def test_send_message_directive(self):
        d = SendMessageDirective(text='hello', payload={'key': 'val'})
        assert d.type == 'send_message'
        assert d.text == 'hello'
        assert d.payload == {'key': 'val'}

    def test_send_message_directive_no_payload(self):
        d = SendMessageDirective(text='hello')
        assert d.payload is None

    def test_server_action_directive(self):
        d = ServerActionDirective(name='act1', payload={'id': 1}, text='clicked')
        assert d.type == 'server_action'
        assert d.name == 'act1'
        assert d.payload == {'id': 1}
        assert d.text == 'clicked'

    def test_set_elements_state_directive(self):
        d = SetElementsStateDirective(ids=['btn1', 'btn2'], state='loading', timeout_seconds=5)
        assert d.type == 'set_elements_state'
        assert d.ids == ['btn1', 'btn2']
        assert d.state == 'loading'
        assert d.timeout_seconds == 5

    def test_set_elements_state_disabled(self):
        d = SetElementsStateDirective(ids=['btn1'], state='disabled')
        assert d.state == 'disabled'
        assert d.timeout_seconds is None


class TestInlineSuggestButton:
    """Tests for InlineSuggestButton model"""

    def test_minimal_button(self):
        btn = InlineSuggestButton()
        assert btn.id is None
        assert btn.title is None
        assert btn.directives is None

    def test_button_with_directives(self):
        btn = InlineSuggestButton(
            id='btn1',
            title='Click me',
            directives=[
                ServerActionDirective(name='act', payload={'x': 1}),
                OpenUriDirective(uri='https://example.com'),
            ]
        )
        assert btn.id == 'btn1'
        assert btn.title == 'Click me'
        assert len(btn.directives) == 2
        assert btn.directives[0].type == 'server_action'
        assert btn.directives[1].type == 'open_uri'

    def test_button_from_dict(self):
        """Test discriminated union parsing from raw dict"""
        btn = InlineSuggestButton.model_validate({
            'id': 'btn1',
            'title': 'Test',
            'directives': [
                {'type': 'open_uri', 'uri': 'https://example.com'},
                {'type': 'server_action', 'name': 'act', 'payload': {'k': 'v'}},
                {'type': 'set_elements_state', 'ids': ['btn1'], 'state': 'loading'},
            ]
        })
        assert isinstance(btn.directives[0], OpenUriDirective)
        assert isinstance(btn.directives[1], ServerActionDirective)
        assert isinstance(btn.directives[2], SetElementsStateDirective)


class TestSuggestButtons:
    """Tests for SuggestButtons model"""

    def test_flat_buttons(self):
        sb = SuggestButtons(
            layout='false',
            persist=True,
            buttons=[
                InlineSuggestButton(id='b1', title='One'),
                InlineSuggestButton(id='b2', title='Two'),
            ]
        )
        assert sb.layout == 'false'
        assert sb.persist is True
        assert len(sb.buttons) == 2

    def test_2d_buttons(self):
        sb = SuggestButtons(
            layout='true',
            persist=False,
            buttons=[
                [InlineSuggestButton(id='b1', title='Row1-1')],
                [InlineSuggestButton(id='b2', title='Row2-1'), InlineSuggestButton(id='b3', title='Row2-2')],
            ]
        )
        assert len(sb.buttons) == 2
        assert len(sb.buttons[1]) == 2

    def test_model_dump_exclude_none(self):
        sb = SuggestButtons(layout='true', buttons=[InlineSuggestButton(id='b1', title='A')])
        dumped = sb.model_dump(exclude_none=True)
        assert 'persist' not in dumped
        assert dumped['layout'] == 'true'
        assert len(dumped['buttons']) == 1


class TestServerAction:
    """Tests for ServerAction model"""

    def test_server_action(self):
        sa = ServerAction(name='do_thing', payload={'id': 123})
        assert sa.name == 'do_thing'
        assert sa.payload == {'id': 123}

    def test_server_action_no_payload(self):
        sa = ServerAction(name='simple')
        assert sa.payload is None


class TestBotRequestError:
    """Tests for BotRequestError model"""

    def test_unsupported_directive_error(self):
        err = BotRequestError(type='unsupported_directive', name='custom_dir')
        assert err.type == 'unsupported_directive'
        assert err.name == 'custom_dir'
        assert err.message is None

    def test_client_error(self):
        err = BotRequestError(type='client_error', message='Something went wrong')
        assert err.type == 'client_error'
        assert err.message == 'Something went wrong'


class TestBotRequest:
    """Tests for BotRequest model"""

    def test_bot_request_with_server_action(self):
        br = BotRequest(
            server_action=ServerAction(name='act', payload={'k': 'v'}),
            element_id='btn1'
        )
        assert br.server_action.name == 'act'
        assert br.element_id == 'btn1'
        assert br.errors is None

    def test_bot_request_with_errors(self):
        br = BotRequest(
            errors=[BotRequestError(type='client_error', message='fail')]
        )
        assert len(br.errors) == 1
        assert br.errors[0].type == 'client_error'

    def test_bot_request_from_dict(self):
        br = BotRequest.model_validate({
            'server_action': {'name': 'act1', 'payload': {'x': 1}},
            'element_id': 'btn2',
            'errors': [{'type': 'unsupported_directive', 'name': 'bad_dir'}]
        })
        assert br.server_action.name == 'act1'
        assert br.element_id == 'btn2'
        assert len(br.errors) == 1


class TestUpdateWithBotRequest:
    """Tests for Update model with bot_request field"""

    def test_update_with_bot_request(self):
        update_data = {
            'from': {'id': '123', 'login': 'user@example.com'},
            'chat': {'type': 'private'},
            'timestamp': 1234567890,
            'message_id': 1,
            'update_id': 1,
            'bot_request': {
                'server_action': {'name': 'do_thing', 'payload': {'id': 42}},
                'element_id': 'btn1'
            }
        }
        update = Update(**update_data)
        assert update.bot_request is not None
        assert update.bot_request.server_action.name == 'do_thing'
        assert update.bot_request.server_action.payload == {'id': 42}
        assert update.bot_request.element_id == 'btn1'

    def test_update_without_bot_request(self):
        update_data = {
            'from': {'id': '123', 'login': 'user@example.com'},
            'chat': {'type': 'private'},
            'text': 'hello',
            'timestamp': 1234567890,
            'message_id': 1,
            'update_id': 1,
        }
        update = Update(**update_data)
        assert update.bot_request is None


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

