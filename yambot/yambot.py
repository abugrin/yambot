import base64

from yambot.router import Router
from time import sleep
from requests import post

from yambot.types import Update

API_URL = 'https://botapi.messenger.yandex.net/bot/v1/messages'


class MessengerBot(Router):
    def __init__(self, token):
        super().__init__()
        self._token = token
        self._headers = {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}

    def start_pooling(self):
        print('Starting pooling...')
        last_update_id = -1

        while True:

            request_body = {'limit': 10, 'offset': last_update_id + 1}

            response = post(f'{API_URL}/getUpdates', json=request_body, headers=self._headers)
            response_json = response.json()

            if 'updates' in response_json:
                updates = response_json['updates']

                if len(updates) > 0:
                    last_update_id = int(updates[len(updates) - 1]['update_id'])

                    for update in updates:
                        print(f'Got update: {update}')
                        update_obj = Update.from_dict(update)
                        self._process_update(update_obj)
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
        response = post(path, json=body, headers=self._headers)
        return response.status_code
    def _send_image_form(self, files, update: Update):
        path = f'{API_URL}/sendImage'
        headers = {'Authorization': f'OAuth {self._token}'}
        body = {}

        if update.chat.chat_type == 'group':
            if update.chat.thread_id and update.chat.thread_id != '0':
                body.update({'chat_id': update.chat.chat_id, 'thread_id': update.chat.thread_id})
            else:
                body.update({'chat_id': update.chat.chat_id})
        else:
            body.update({'login': update.from_m.login})

        response = post(path, headers=headers, files=files, data=body)
        return response.status_code


    def send_message(self, text, update: Update):
        body = {'text': text, 'disable_web_page_preview': True}
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
        print(f'Delete request: {body}')
        response = post(path, json=body, headers=self._headers)
        print(f'Delete response: {response.status_code}')
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

