import base64
import logging

from yambot.router import Router
from time import sleep
from requests import post

from yambot.types import Update

API_URL = 'https://botapi.messenger.yandex.net/bot/v1/messages'

class MessengerBot(Router):
    def __init__(self, token, log_level=logging.INFO):
        super().__init__(log_level=log_level)
        self._token = token
        self._headers = {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}


    def start_pooling(self):
        self._logger.info('Starting pooling...')
        last_update_id = -1

        while True:
            try:
                request_body = {'limit': 10, 'offset': last_update_id + 1}

                response = post(f'{API_URL}/getUpdates', json=request_body, headers=self._headers)
                if response.status_code != 200:
                    raise ConnectionError(f'{response.status_code} - {response.text}')
                response_json = response.json()

                if 'updates' in response_json:
                    updates = response_json['updates']

                    if len(updates) > 0:
                        last_update_id = int(updates[len(updates) - 1]['update_id'])

                        for update in updates:
                            self._logger.debug(f'Got update: {update}')
                            update_obj = Update.from_dict(update)
                            self._process_update(update_obj)
            except Exception as e:
                self._logger.error(f'Error while pooling: {e}')
            finally:
                sleep(1)

    def _send_text(self, body, update: Update):
        path = f'{API_URL}/sendText'

        if update.chat.chat_type == 'group':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})
        else:
            body.update({'login': update.from_m.login})
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

    def _send_image_form(self, files, update: Update, path = f'{API_URL}/sendImage'):

        headers = {'Authorization': f'OAuth {self._token}'}
        body = {}

        if update.chat.chat_type == 'group':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})
        else:
            body.update({'login': update.from_m.login})
        try:
            response = post(path, headers=headers, files=files, data=body)
            if response.status_code !=200:
                raise ConnectionError(f'{response.status_code} - {response.text}')
            self._logger.debug(f'Send image response: {response.text}')
            return response.json()
        except Exception as e:
            self._logger.error(f'Error while sending image: {e}')
            return {}


    def send_message(self, text, update: Update, disable_web_page_preview = True):
        body = {'text': text, 'disable_web_page_preview': disable_web_page_preview}
        return self._send_text(body, update)

    def delete_message(self, update: Update):
        path = f'{API_URL}/delete/'
        body = {'message_id': update.message_id}

        if update.chat.chat_type == 'group':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})
        else:
            body.update({'login': update.from_m.login})
        self._logger.debug(f'Delete request: {body}')
        response = post(path, json=body, headers=self._headers)
        self._logger.debug(f'Delete response: {response.status_code}')
        return response.status_code

    def send_inline_keyboard(self, text, buttons: [], update: Update):
        body = {'text': text, 'inline_keyboard': buttons}
        return self._send_text(body, update)

    def send_image(self, image, update: Update):
        try:
            img_data = base64.b64decode(image)
        except TypeError:
            img_data = image
        files = [('image', ('image.jpeg', img_data, 'image/jpeg'))]
        self._send_image_form(files, update)

    def send_gallery(self, images: [], update: Update):
        files = []
        index = 0
        for image in images:
            try:
                img_data = base64.b64decode(image)
            except TypeError:
                img_data = image
            files.append(('images', (f'image{index}.jpeg', img_data, 'image/jpeg')))
            index += 1
        self._send_image_form(files, update, path=f'{API_URL}/sendGallery')