import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from time import sleep
from requests import post, Response
from .router import Router
from .types import Update, UpdatesResponse, User
from .exceptions import APIError, ValidationError, RateLimitError
from .rate_limiter import RateLimiter

API_URL = 'https://botapi.messenger.yandex.net/bot/v1'
DEFAULT_UPDATES_LIMIT = 10
MAX_TEXT_LENGTH = 6000
MAX_BUTTONS = 100
MAX_RPS = 20
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0

class MessengerBot(Router):
    """MessengerBot Client

    Args:
        token (str): Bot API token
        log_level (int): Deprecated, use logging module instead
        poll_interval (int): Interval between polling requests in seconds, default: 1
        pool_interval (int): Deprecated, use poll_interval instead

    """
    def __init__(self, token: str, log_level=logging.INFO, poll_interval: int = 1, pool_interval: Optional[int] = None):
        """MessengerBot Client

        Args:
            token (str): Bot API token
            log_level (int): Deprecated, use logging module instead
            poll_interval (int): Interval between polling requests in seconds, default: 1
            pool_interval (int): Deprecated, use poll_interval instead

        """

        super().__init__()
        self._token = token
        
        # Handle deprecated pool_interval parameter
        if pool_interval is not None:
            import warnings
            warnings.warn(
                "pool_interval parameter is deprecated and will be removed in future versions. "
                "Use poll_interval instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self._poll_interval = pool_interval
        else:
            self._poll_interval = poll_interval
            
        self._headers = {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}
        self._rate_limiter = RateLimiter(max_rps=MAX_RPS)

    def _make_request(self, method: Callable, url: str, max_retries: int = MAX_RETRIES, 
                     timeout: int = DEFAULT_TIMEOUT, **kwargs) -> Response:
        """Make HTTP request with rate limiting and retry logic
        
        Args:
            method: HTTP method function (post, get, etc.)
            url: Request URL
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for request
            
        Returns:
            Response: HTTP response
            
        Raises:
            APIError: If request fails after all retries
            RateLimitError: If rate limit is exceeded
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting
                if not self._rate_limiter.acquire(timeout=timeout):
                    raise RateLimitError('Rate limit timeout exceeded')
                
                # Make request
                response = method(url, timeout=timeout, **kwargs)
                
                # Handle different status codes
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limit exceeded
                    self._logger.warning(f'Rate limit exceeded, attempt {attempt + 1}/{max_retries + 1}')
                    if attempt < max_retries:
                        sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                        continue
                    raise RateLimitError('Rate limit exceeded after all retries')
                elif response.status_code in (500, 502, 503):
                    # Server errors - retry
                    self._logger.warning(f'Server error {response.status_code}, attempt {attempt + 1}/{max_retries + 1}')
                    if attempt < max_retries:
                        sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                        continue
                    raise APIError(response.status_code, f'Server error after all retries: {response.text}')
                elif response.status_code == 401:
                    # Authentication error - don't retry
                    raise APIError(401, 'Authentication failed - check your token')
                elif response.status_code >= 400:
                    # Client errors - don't retry
                    raise APIError(response.status_code, response.text)
                else:
                    # Unexpected status code
                    raise APIError(response.status_code, f'Unexpected status code: {response.text}')
                    
            except (APIError, RateLimitError):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Network errors, timeouts, etc.
                last_exception = e
                self._logger.warning(f'Request failed: {e}, attempt {attempt + 1}/{max_retries + 1}')
                if attempt < max_retries:
                    sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                raise APIError(0, f'Request failed after all retries: {e}') from last_exception
        
        # Should never reach here, but just in case
        if last_exception:
            raise APIError(0, f'Request failed: {last_exception}') from last_exception
        raise APIError(0, 'Request failed for unknown reason')

    def start_pooling(self):
        """Starts pooling for new updates
        
        .. deprecated:: 0.0.9
            Use :func:`start_polling` instead. This method is kept for backward compatibility.
        
        """
        import warnings
        warnings.warn(
            "start_pooling() is deprecated and will be removed in future versions. "
            "Use start_polling() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.start_polling()

    def start_polling(self):
        """Starts polling for new updates

        """

        self._logger.info('Starting polling...')
        last_update_id = -1

        try:
            while True:
                try:
                    request_body = {'limit': DEFAULT_UPDATES_LIMIT, 'offset': last_update_id + 1}

                    response = self._make_request(
                        post, 
                        f'{API_URL}/messages/getUpdates', 
                        json=request_body, 
                        headers=self._headers
                    )
                    updates_response = UpdatesResponse(**response.json())

                    updates = updates_response.updates

                    if len(updates) > 0:
                        last_update_id = updates[len(updates) - 1].update_id

                        for update in updates:
                            self._logger.debug(f'Got update: {update}')
                            self._process_update(update)
                except Exception as e:
                    self._logger.error(f'Error while polling: {type(e)} {e}')
                finally:
                    sleep(self._poll_interval)

        except KeyboardInterrupt:
            self._logger.info('Stop polling...')


    def _send_text(self, body: Dict, update: Update) -> Dict:
        """Send text message via API
        
        Args:
            body (Dict): Request body
            update (Update): Update object
            
        Returns:
            Dict: API response
        """
        path = f'{API_URL}/messages/sendText'

        self._set_target_chat(body, update)
        self._logger.debug(f'Sending text: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        self._logger.debug(f'Send message response: {response.text}')
        return response.json()

    def _send_form(self, files: List, update: Update, path: str = f'{API_URL}/messages/sendImage') -> Dict:
        """Send form data (files) via API
        
        Args:
            files (List): List of files to send
            update (Update): Update object
            path (str): API endpoint path
            
        Returns:
            Dict: API response
        """
        headers = {'Authorization': f'OAuth {self._token}'}
        body = {}

        self._set_target_chat(body, update)
        self._logger.debug(f'Sending form data to: {path}')
        
        response = self._make_request(post, path, headers=headers, files=files, data=body)
        self._logger.debug(f'Send form response: {response.text}')
        return response.json()

    def _set_target_chat(self, body: Dict, update: Update) -> Dict:
        """Set target chat/user in request body based on update

        Args:
            body (Dict): Request body to update
            update (Update): Update object with chat info

        Returns:
            Dict: Updated body
        """
        if update.chat.chat_type in ('group', 'channel'):
            body['chat_id'] = update.chat.chat_id
            if update.chat.thread_id and update.chat.thread_id != 0:
                body['thread_id'] = update.chat.thread_id
        else:
            body['login'] = update.from_m.login
        return body

    def send_message(self, text: str, update: Update, disable_web_page_preview: bool = True, 
                     payload_id: Optional[str] = None, reply_message_id: Optional[int] = None,
                     disable_notification: bool = False, important: bool = False,
                     thread_id: Optional[int] = None) -> Dict:
        """Send text message to chat, thread or user (depends on Update object)

        Args:
            text (str): Text to send (max 6000 characters)
            update (Update): Update object
            disable_web_page_preview (bool): Disable web page preview, default: True
            payload_id (str): Request ID for idempotency
            reply_message_id (int): ID of message to reply to
            disable_notification (bool): Disable notification, default: False
            important (bool): Mark message as important, default: False
            thread_id (int): Thread ID to send message to

        Returns:
            Dict: Response from Bot API

        Raises:
            ValueError: If text is too long

        """
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f'Text length exceeds maximum of {MAX_TEXT_LENGTH} characters')

        body = {'text': text, 'disable_web_page_preview': disable_web_page_preview}
        
        if payload_id:
            body['payload_id'] = payload_id
        if reply_message_id:
            body['reply_message_id'] = reply_message_id
        if disable_notification:
            body['disable_notification'] = disable_notification
        if important:
            body['important'] = important
        if thread_id:
            body['thread_id'] = thread_id
            
        return self._send_text(body, update)
    

    def delete_message(self, update: Update) -> int:
        """Delete message from chat, thread or user (depends on Update object)

        Args:
            update (Update): Update object
        Returns:
            int: Response status code

        """

        path = f'{API_URL}/messages/delete/'
        body = {'message_id': update.message_id}

        self._set_target_chat(body, update)
        self._logger.debug(f'Delete request: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        self._logger.debug(f'Delete response: {response.status_code}')
        return response.status_code

    def send_inline_keyboard(self, text: str, buttons: List[Dict], update: Update) -> Dict:
        """Send inline keyboard to chat, thread or user (depends on Update object)

        Args:
            text (str): Text to send
            buttons (List[Dict]): List of buttons to send. Can be any Dict with 'text' and 'callback_data'
            update (Update): Update object

        Returns:
            Dict: Response from Bot API

        Raises:
            ValueError: If too many buttons or channel type

        """
        if update.chat.chat_type == 'channel':
            raise ValueError('Inline keyboard not supported for channels')
        
        if len(buttons) > MAX_BUTTONS:
            raise ValueError(f'Number of buttons exceeds maximum of {MAX_BUTTONS}')
            
        body = {'text': text, 'inline_keyboard': buttons}
        return self._send_text(body, update)

    def send_image(self, image: Any, update: Update) -> Dict:
        """Send image to chat, thread or user (depends on Update object)

        Args:
            image (str|bytes): Image to send. Can be base64 string or bytes
            update (Update): Update object

        Returns:
            Dict: Response from Bot API

        """
        try:
            img_data = base64.b64decode(image)
        except TypeError:
            img_data = image
        files = [('image', ('image.jpeg', img_data, 'image/jpeg'))]
        return self._send_form(files, update)

    def send_gallery(self, images: List[Any], update: Update) -> Dict:
        """Send image gallery to chat, thread or user (depends on Update object)

        Args:
            images (List[Any]): List of images to send. Can be base64 string or bytes
            update (Update): Update object

        Returns:
            Dict: Response from Bot API

        """
        files = []
        index = 0
        for image in images:
            try:
                img_data = base64.b64decode(image)
            except TypeError:
                img_data = image
            files.append(('images', (f'image{index}.jpeg', img_data, 'image/jpeg')))
            index += 1
        return self._send_form(files, update, path=f'{API_URL}/messages/sendGallery')

    def send_file(self, file: Any, filename: str, mime_type: str, update: Update) -> Dict:
        """Send file to chat, thread or user (depends on Update object)

        Args:
            file: File to send (file object or bytes)
            filename (str): Name of the file
            mime_type (str): MIME type of the file
            update (Update): Update object

        Returns:
            Dict: Response from Bot API

        """
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(filename)
        file_data = [('document', (safe_filename, file, mime_type))]
        return self._send_form(files=file_data, update=update, path=f'{API_URL}/messages/sendFile')



    def download_file(self, update: Update, directory: str = '') -> str:
        """Download file from chat, thread or user (depends on Update object)

        Args:
            update (Update): Update object
            directory (str): Directory to save file, default: current directory

        Returns:
            str: Path to downloaded file

        Raises:
            FileNotFoundError: If file not found in update object
            ValueError: If filename contains path traversal attempt

        """
        if not update.file:
            self._logger.error('File not found in update object')
            raise FileNotFoundError('File not found in update object')
        
        # Sanitize filename to prevent path traversal attacks
        safe_filename = os.path.basename(update.file.name)
        if safe_filename != update.file.name:
            self._logger.warning(f'Suspicious filename detected: {update.file.name}, using: {safe_filename}')
        
        # Build safe file path
        if directory:
            save_path = Path(directory) / safe_filename
        else:
            save_path = Path(safe_filename)
        
        # Download file
        api_path = f'{API_URL}/messages/getFile'
        body = {'file_id': update.file.file_id}
        response = self._make_request(post, api_path, json=body, headers=self._headers)
        
        # Save file
        with open(save_path, 'wb') as f:
            f.write(response.content)
            self._logger.info(f'File downloaded: {save_path}')
        
        return str(save_path)

    # Poll methods
    
    def create_poll(self, title: str, answers: List[str], update: Update,
                    max_choices: int = 1, is_anonymous: bool = False,
                    payload_id: Optional[str] = None, reply_message_id: Optional[int] = None,
                    disable_notification: bool = False, important: bool = False,
                    thread_id: Optional[int] = None) -> Dict:
        """Create a poll in chat or send to user

        Args:
            title (str): Poll title
            answers (List[str]): List of answer options (2-100 items)
            update (Update): Update object
            max_choices (int): Maximum number of choices, default: 1
            is_anonymous (bool): Whether poll is anonymous, default: False
            payload_id (str): Request ID for idempotency
            reply_message_id (int): ID of message to reply to
            disable_notification (bool): Disable notification, default: False
            important (bool): Mark message as important, default: False
            thread_id (int): Thread ID to send poll to

        Returns:
            Dict: Response from Bot API with message_id

        Raises:
            ValidationError: If answers list is invalid

        """
        if len(answers) < 2 or len(answers) > 100:
            raise ValidationError('Poll must have between 2 and 100 answer options')
        
        if max_choices < 1:
            raise ValidationError('max_choices must be at least 1')

        body = {
            'title': title,
            'answers': answers,
            'max_choices': max_choices,
            'is_anonymous': is_anonymous
        }
        
        if payload_id:
            body['payload_id'] = payload_id
        if reply_message_id:
            body['reply_message_id'] = reply_message_id
        if disable_notification:
            body['disable_notification'] = disable_notification
        if important:
            body['important'] = important
        if thread_id:
            body['thread_id'] = thread_id
        
        self._set_target_chat(body, update)
        
        path = f'{API_URL}/messages/createPoll'
        self._logger.debug(f'Creating poll: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    def get_poll_results(self, message_id: int, update: Update,
                        invite_hash: Optional[str] = None,
                        thread_id: Optional[int] = None) -> Dict:
        """Get poll results

        Args:
            message_id (int): Message ID with poll
            update (Update): Update object
            invite_hash (str): Invite hash if bot is not in chat yet
            thread_id (int): Thread ID if poll is in thread

        Returns:
            Dict: Poll results with 'voted_count' and 'answers' (map of answer_id to vote count)

        """
        body = {'message_id': message_id}
        
        self._set_target_chat(body, update)
        
        if invite_hash:
            body['invite_hash'] = invite_hash
        if thread_id:
            body['thread_id'] = thread_id
        
        path = f'{API_URL}/polls/getResults'
        self._logger.debug(f'Getting poll results: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    def get_poll_voters(self, message_id: int, answer_id: int, update: Update,
                       limit: int = 100, cursor: int = 0,
                       invite_hash: Optional[str] = None,
                       thread_id: Optional[int] = None) -> Dict:
        """Get list of users who voted for specific answer

        Args:
            message_id (int): Message ID with poll
            answer_id (int): Answer option number
            update (Update): Update object
            limit (int): Maximum number of voters to return (max 1000), default: 100
            cursor (int): Vote ID to start from, default: 0
            invite_hash (str): Invite hash if bot is not in chat yet
            thread_id (int): Thread ID if poll is in thread

        Returns:
            Dict: Voters list with 'voted_count', 'cursor', and 'votes' array

        Raises:
            ValidationError: If limit is invalid

        """
        if limit < 1 or limit > 1000:
            raise ValidationError('Limit must be between 1 and 1000')

        body = {
            'message_id': message_id,
            'answer_id': answer_id,
            'limit': limit,
            'cursor': cursor
        }
        
        self._set_target_chat(body, update)
        
        if invite_hash:
            body['invite_hash'] = invite_hash
        if thread_id:
            body['thread_id'] = thread_id
        
        path = f'{API_URL}/polls/getVoters'
        self._logger.debug(f'Getting poll voters: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    # Chat management methods
    
    def create_chat(self, name: str, description: str = '',
                   members: Optional[List[User]] = None,
                   admins: Optional[List[User]] = None,
                   avatar_url: Optional[str] = None) -> Dict:
        """Create a new chat

        Args:
            name (str): Chat name (max 200 characters)
            description (str): Chat description (max 500 characters), default: ''
            members (List[User]): List of chat members (max 500)
            admins (List[User]): List of chat admins (max 100)
            avatar_url (str): URL of chat avatar image

        Returns:
            Dict: Response with 'chat_id'

        Raises:
            ValidationError: If parameters are invalid

        """
        if len(name) > 200:
            raise ValidationError('Chat name must not exceed 200 characters')
        if len(description) > 500:
            raise ValidationError('Chat description must not exceed 500 characters')
        
        if members and len(members) > 500:
            raise ValidationError('Cannot add more than 500 members at once')
        if admins and len(admins) > 100:
            raise ValidationError('Cannot add more than 100 admins at once')

        body = {
            'name': name,
            'description': description,
            'channel': False
        }
        
        if members:
            body['members'] = [{'login': m.login} for m in members]
        if admins:
            body['admins'] = [{'login': a.login} for a in admins]
        if avatar_url:
            body['avatar_url'] = avatar_url
        
        path = f'{API_URL}/chats/create'
        self._logger.debug(f'Creating chat: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    def create_channel(self, name: str, description: str = '',
                      subscribers: Optional[List[User]] = None,
                      admins: Optional[List[User]] = None,
                      avatar_url: Optional[str] = None) -> Dict:
        """Create a new channel

        Args:
            name (str): Channel name (max 200 characters)
            description (str): Channel description (max 500 characters), default: ''
            subscribers (List[User]): List of channel subscribers (max 500)
            admins (List[User]): List of channel admins (max 100)
            avatar_url (str): URL of channel avatar image

        Returns:
            Dict: Response with 'chat_id'

        Raises:
            ValidationError: If parameters are invalid

        """
        if len(name) > 200:
            raise ValidationError('Channel name must not exceed 200 characters')
        if len(description) > 500:
            raise ValidationError('Channel description must not exceed 500 characters')
        
        if subscribers and len(subscribers) > 500:
            raise ValidationError('Cannot add more than 500 subscribers at once')
        if admins and len(admins) > 100:
            raise ValidationError('Cannot add more than 100 admins at once')

        body = {
            'name': name,
            'description': description,
            'channel': True
        }
        
        if subscribers:
            body['subscribers'] = [{'login': s.login} for s in subscribers]
        if admins:
            body['admins'] = [{'login': a.login} for a in admins]
        if avatar_url:
            body['avatar_url'] = avatar_url
        
        path = f'{API_URL}/chats/create'
        self._logger.debug(f'Creating channel: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    def update_members(self, chat_id: str,
                      members: Optional[List[User]] = None,
                      admins: Optional[List[User]] = None,
                      subscribers: Optional[List[User]] = None,
                      remove: Optional[List[User]] = None) -> Dict:
        """Update chat or channel members

        Args:
            chat_id (str): Chat or channel ID
            members (List[User]): Users to add as members (max 500)
            admins (List[User]): Users to make admins (max 100)
            subscribers (List[User]): Users to add as subscribers (max 500)
            remove (List[User]): Users to remove (max 500)

        Returns:
            Dict: Response with 'ok' status

        Raises:
            ValidationError: If parameters are invalid

        """
        if not any([members, admins, subscribers, remove]):
            raise ValidationError('At least one user list must be provided')
        
        if members and len(members) > 500:
            raise ValidationError('Cannot add more than 500 members at once')
        if admins and len(admins) > 100:
            raise ValidationError('Cannot add more than 100 admins at once')
        if subscribers and len(subscribers) > 500:
            raise ValidationError('Cannot add more than 500 subscribers at once')
        if remove and len(remove) > 500:
            raise ValidationError('Cannot remove more than 500 users at once')

        body = {'chat_id': chat_id}
        
        if members:
            body['members'] = [{'login': m.login} for m in members]
        if admins:
            body['admins'] = [{'login': a.login} for a in admins]
        if subscribers:
            body['subscribers'] = [{'login': s.login} for s in subscribers]
        if remove:
            body['remove'] = [{'login': r.login} for r in remove]
        
        path = f'{API_URL}/chats/updateMembers'
        self._logger.debug(f'Updating members: {body}')
        
        response = self._make_request(post, path, json=body, headers=self._headers)
        return response.json()

    def get_user_link(self, login: str) -> Dict:
        """Get links to user's chat and call

        Args:
            login (str): User login

        Returns:
            Dict: Response with 'id', 'chat_link', and 'call_link'

        """
        from requests import get
        
        path = f'{API_URL}/users/getUserLink'
        params = {'login': login}
        
        self._logger.debug(f'Getting user link for: {login}')
        
        response = self._make_request(get, path, params=params, headers=self._headers)
        return response.json()


