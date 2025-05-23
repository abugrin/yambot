import base64
import logging
from typing import Any, Dict, List, Optional
from time import sleep
from .router import Router
from .types import Update, UpdatesResponse
from .http_client import HTTPClientBase, create_client

API_URL = 'https://botapi.messenger.yandex.net/bot/v1'

class MessengerBot(Router):
    """MessengerBot Client

    Args:
        token (str): Bot API token
        client_type (str): HTTP client type ('requests', 'httpx', or 'async'), default: 'requests'
        log_level (int): Logging level
        pool_interval (int): Interval between pooling requests in seconds, default: 1
        **client_kwargs: Additional arguments for HTTP client configuration

    """
    def __init__(self, token: str, client_type: str = 'requests', log_level=logging.INFO, 
                 pool_interval: int = 1, **client_kwargs):
        super().__init__()
        self._token = token
        self._pool_interval = pool_interval
        self._logger = logging.getLogger('yambot')
        self._logger.setLevel(log_level)
        
        # Initialize HTTP client
        self._http = create_client(client_type, token=token, **client_kwargs)

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_http'):
            self._http.close()

    def start_pooling(self):
        """Starts pooling for new updates"""
        self._logger.info('Starting pooling...')
        last_update_id = -1

        try:
            while True:
                try:
                    request_body = {'limit': 10, 'offset': last_update_id + 1}
                    response = self._http.post(
                        f'{API_URL}/messages/getUpdates',
                        json=request_body
                    )
                    updates_response = UpdatesResponse(**response)
                    updates = updates_response.updates

                    if len(updates) > 0:
                        last_update_id = updates[len(updates) - 1].update_id
                        for update in updates:
                            self._logger.debug(f'Got update: {update}')
                            self._process_update(update)
                except Exception as e:
                    self._logger.error(f'Error while pooling: {type(e)} {e}')
                finally:
                    sleep(self._pool_interval)

        except KeyboardInterrupt:
            self._logger.info('Stop pooling...')
        finally:
            self._http.close()

    def _send_text(self, body: Dict, update: Update) -> Dict:
        """Send text message"""
        path = f'{API_URL}/messages/sendText'
        self._set_target_chat(body, update)
        self._logger.debug(f'Sending text: {body}')
        
        try:
            return self._http.post(path, json=body)
        except Exception as e:
            self._logger.error(f'Error while sending message: {e}')
            return {}

    def _send_form(self, files: List[tuple], update: Update, path: str = f'{API_URL}/messages/sendImage') -> Dict:
        """Send form data with files"""
        body = {}
        self._set_target_chat(body, update)
        
        try:
            return self._http.post(path, files=files, data=body)
        except Exception as e:
            self._logger.error(f'Error while sending form data: {e}')
            return {}

    def _set_target_chat(self, body: Dict, update: Update) -> Dict:
        """Set target chat in request body"""
        if update.chat and update.chat.chat_type == 'group':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})
        elif update.chat and update.chat.chat_type == 'channel':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})            
        else:
            body.update({'login': update.from_m.login})
        return body

    def send_message(self, text: str, update: Update, disable_web_page_preview: bool = True) -> Dict:
        """Send text message to chat, thread or user (depends on Update object)

        Args:
            text (str): Text to send
            update (Update): Update object
            disable_web_page_preview (bool): Disable web page preview, default: True
        Returns:
            Dict: Response from Bot API
        """
        body = {'text': text, 'disable_web_page_preview': disable_web_page_preview}
        return self._send_text(body, update)

    def delete_message(self, update: Update) -> Dict:
        """Delete message from chat, thread or user (depends on Update object)

        Args:
            update (Update): Update object
        Returns:
            Dict: Response from Bot API
        """
        path = f'{API_URL}/messages/delete'
        body = {'message_id': update.message_id}
        self._set_target_chat(body, update)
        
        self._logger.debug(f'Delete request: {body}')
        try:
            response = self._http.post(path, json=body)
            self._logger.debug(f'Delete response: {response}')
            return response
        except Exception as e:
            self._logger.error(f'Error while deleting message: {e}')
            return {}

    def send_inline_keyboard(self, text: str, buttons: List[Dict], update: Update) -> Dict:
        """Send inline keyboard to chat, thread or user (depends on Update object)

        Args:
            text (str): Text to send
            buttons (List[Dict]): List of buttons to send. Can be any Dict with 'text' and 'callback_data'
            update (Update): Update object
        Returns:
            Dict: Response from Bot API
        """
        if update.chat and update.chat.chat_type == 'channel':
            self._logger.error('Send inline keyboard to channel not supported.')
            return {'error': 'Not supported for channels'}
        
        body = {'text': text, 'inline_keyboard': buttons}
        return self._send_text(body, update)

    def send_image(self, image: Any, update: Update) -> Dict:
        """Send image to chat, thread or user (depends on Update object)

        Args:
            image (Union[str, bytes]): Image to send. Can be base64 string or bytes
            update (Update): Update object
        Returns:
            Dict: Response from Bot API
        """
        try:
            img_data = base64.b64decode(image) if isinstance(image, str) else image
            files = [('image', ('image.jpeg', img_data, 'image/jpeg'))]
            return self._send_form(files, update)
        except Exception as e:
            self._logger.error(f'Error processing image: {e}')
            return {}

    def send_gallery(self, images: List[Any], update: Update) -> Dict:
        """Send image gallery to chat, thread or user (depends on Update object)

        Args:
            images (List[Any]): List of images to send. Can be base64 string or bytes
            update (Update): Update object
        Returns:
            Dict: Response from Bot API
        """
        try:
            files = []
            for idx, image in enumerate(images):
                img_data = base64.b64decode(image) if isinstance(image, str) else image
                files.append(('images', (f'image{idx}.jpeg', img_data, 'image/jpeg')))
            return self._send_form(files, update, path=f'{API_URL}/messages/sendGallery')
        except Exception as e:
            self._logger.error(f'Error processing gallery: {e}')
            return {}

    def send_file(self, file: Any, filename: str, mime_type: str, update: Update) -> Dict:
        """Send file to chat, thread or user (depends on Update object)

        Args:
            file: File to send
            filename (str): Name of the file
            mime_type (str): MIME type of the file
            update (Update): Update object
        Returns:
            Dict: Response from Bot API
        """
        file_data = [('document', (filename, file, mime_type))]
        return self._send_form(file_data, update, path=f'{API_URL}/messages/sendFile')

    def download_file(self, update: Update, dir: str = '') -> None:
        """Download file from chat, thread or user (depends on Update object)

        Args:
            update (Update): Update object
            dir (str): Directory to save file, default: ''

        Raises:
            FileNotFoundError: If file not found in update object
        """
        if not update.file:
            self._logger.error('File not found in update object')
            raise FileNotFoundError('File not found in update object')

        path = f'{API_URL}/messages/getFile'
        body = {'file_id': update.file.file_id}
        
        try:
            response = self._http.post(path, json=body)
            with open(f'{dir}{update.file.name}', 'wb') as f:
                f.write(response['content'] if isinstance(response, dict) else response)
            self._logger.info(f'File downloaded: {update.file.name}')
        except Exception as e:
            self._logger.error(f'Error downloading file: {e}')
            raise


