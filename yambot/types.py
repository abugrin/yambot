import json


class _BaseObject(object):
    def to_json(self):
        return json.dumps(self)


class Chat:
    def __init__(self, chat_type, chat_id, thread_id):
        self._chat_id = chat_id
        self._chat_type = chat_type
        self._thread_id = thread_id

    @classmethod
    def from_dict(cls, obj: dict):
        return cls(
            chat_id=obj.get('chat_id', None),
            chat_type=obj['type'],
            thread_id=obj.get('thread_id', None)
        )

    @property
    def chat_id(self):
        return self._chat_id

    @property
    def chat_type(self):
        return self._chat_type

    @property
    def thread_id(self):
        return self._thread_id


class From:
    def __init__(self, display_name, from_id, login, robot):
        self._display_name = display_name
        self._from_id = from_id
        self._login = login
        self._robot = robot

    @classmethod
    def from_dict(cls, obj: dict):
        return cls(
            display_name=obj['display_name'],
            from_id=obj['id'],
            login=obj['login'],
            robot=obj['robot']
        )

    @property
    def display_name(self):
        return self._display_name

    @property
    def from_id(self):
        return self._from_id

    @property
    def login(self):
        return self._login

    @property
    def robot(self):
        return self._robot

class Update:
    def __init__(self, chat: Chat, from_m: From, message_id, text, timestamp,
                 update_id, reply_to_message, callback_data):
        self._chat = chat
        self._from_m = from_m
        self._message_id = message_id
        self._text = text
        self._timestamp = timestamp
        self._update_id = update_id
        self._reply_to_message = reply_to_message
        self._callback_data = callback_data

    @classmethod
    def from_dict(cls, obj: dict):
        reply_to_message = None
        if 'reply_to_message' in obj:
            reply_to_message = Update.from_dict(obj['reply_to_message'])

        return cls(
            chat=Chat.from_dict(obj['chat']),
            from_m=From.from_dict(obj['from']),
            message_id=obj['message_id'],
            text=obj['text'],
            timestamp=obj['timestamp'],
            update_id=obj['update_id'],
            reply_to_message=reply_to_message,
            callback_data=obj.get('callback_data', None)

        )

    @property
    def chat(self):
        return self._chat

    @property
    def from_m(self):
        return self._from_m

    @property
    def message_id(self):
        return self._message_id

    @property
    def text(self):
        return self._text

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def update_id(self):
        return self._update_id

    @property
    def reply_to_message(self):
        return self._reply_to_message

    @property
    def callback_data(self):
        return self._callback_data

