import base64
import logging
from typing import Any, Dict, List
from time import sleep
from requests import post
from .router import Router
from .types import Update, UpdatesResponse

API_URL = 'https://botapi.messenger.yandex.net/bot/v1'

class MessengerBot(Router):
    """MessengerBot Client

    Args:
        token (str): Bot API token
        log_level (int): Deprecated, use logging module instead
        pool_interval (int): Interval between pooling requests in seconds, default: 1

    """
    def __init__(self, token: str, log_level=logging.INFO, pool_interval: int = 1):
        """MessengerBot Client

        Args:
            token (str): Bot API token
            log_level (int): Deprecated, use logging module instead
            pool_interval (int): Interval between pooling requests in seconds, default: 1

        """

        super().__init__()
        self._token = token
        self._pool_interval = pool_interval
        self._headers = {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}


    def start_pooling(self):
        """Starts pooling for new updates

        """

        self._logger.info('Starting pooling...')
        last_update_id = -1

        try:
            while True:
                try:
                    request_body = {'limit': 10, 'offset': last_update_id + 1}

                    response = post(f'{API_URL}/messages/getUpdates', json=request_body, headers=self._headers)
                    if response.status_code != 200:
                        raise ConnectionError(f'{response.status_code} - {response.text}')
                    updates_response = UpdatesResponse(**response.json())

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


    def _send_text(self, body: Dict, update: Update):
        path = f'{API_URL}/messages/sendText'

        self._set_target_chat(body, update)
        self._logger.debug(f'Sending text: {body}')
        try:
            response = post(path, json=body, headers=self._headers)
            if response.status_code != 200:
                raise ConnectionError(f'{response.status_code} - {response.text}')
            self._logger.debug(f'Send message response: {response.text}')
            return response.json()
        except Exception as e:
            self._logger.error(f'Error while sending message: {e}')
            return {}

    def _send_form(self, files, update: Update, path = f'{API_URL}/messages/sendImage'):

        headers = {'Authorization': f'OAuth {self._token}'}
        body = {}

        self._set_target_chat(body, update)
        try:
            response = post(path, headers=headers, files=files, data=body)
            if response.status_code !=200:
                raise ConnectionError(f'{response.status_code} - {response.text}')
            self._logger.debug(f'Send form response: {response.text}')
            return response.json()
        except Exception as e:
            self._logger.error(f'Error while sending form data: {e}')
            return {}

    def _set_target_chat(self, body: Dict, update: Update) -> Dict:
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

    def send_message(self, text, update: Update, disable_web_page_preview = True) -> Dict:
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
        response = post(path, json=body, headers=self._headers)
        self._logger.debug(f'Delete response: {response.status_code}')
        return response.status_code

    def send_inline_keyboard(self, text, buttons: List[Dict], update: Update):
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
            return 500
        else:
            body = {'text': text, 'inline_keyboard': buttons}
            return self._send_text(body, update)

    def send_image(self, image, update: Update):
        """Send image to chat, thread or user (depends on Update object)

        Args:
            image (str): Image to send. Can be base64 string or bytes
            update (Update): Update object
        Returns:
            Dict: Response from Bot API

        """

        try:
            img_data = base64.b64decode(image)
        except TypeError:
            img_data = image
        files = [('image', ('image.jpeg', img_data, 'image/jpeg'))]
        self._send_form(files, update)

    def send_gallery(self, images: List[Any], update: Update):
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
        self._send_form(files, update, path=f'{API_URL}/messages/sendGallery')

    def send_file(self, file, filename: str, mime_type: str, update: Update):
        file_data = [('document', (filename, file, mime_type))]
        self._send_form(files=file_data, update=update, path=f'{API_URL}/messages/sendFile')



    def download_file(self, update: Update, dir = ''):
        """Download file from chat, thread or user (depends on Update object)

        Args:
            update (Update): Update object
            dir (str): Directory to save file, default: ''

        Raises:
            FileNotFoundError: If file not found in update object
        """
        
        path = f'{API_URL}/messages/getFile'

        if update.file:
            body = {'file_id': update.file.file_id}
            response = post(path, json=body, headers=self._headers)

            with open(f'{dir}{update.file.name}', 'wb') as f:
                f.write(response.content)
                self._logger.info(f'File downloaded: {update.file.name}')

        else:
            self._logger.error('File not found in update object')
            raise FileNotFoundError('File not found in update object')


