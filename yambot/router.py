import logging
import sys

from yambot.types import Update
import re


class Router:
    def __init__(self, log_level = logging.INFO):
        self._handlers = []
        # If using button must provide 'cmd' object in callback-data
        self._allowed_commands = ['button', 'command', 'text', 'regex', 'any']
        self._logger = logging.getLogger('yambot')
        self._logger.setLevel(log_level)
        log_handler = logging.StreamHandler(sys.stdout)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
        self._logger.addHandler(log_handler)

    def add_handler(self, **kwargs):
        def decorator(func):
            if not [cmd for cmd in self._allowed_commands if cmd in kwargs]:
                raise ValueError(
                    f'Handler type not supported: {kwargs.keys()}, supported types: {self._allowed_commands}')
            self._handlers.append((kwargs, func))
            return func

        return decorator

    def get_updates(self):
        raise NotImplementedError

    def _process_update(self, update: Update):
        match = False
        for cmd, func in self._handlers:
            if self._check_handler(cmd, update):
                func(update)
                match = True
                break

        if not match:
            for cmd, func in self._handlers:
                if self._match_any_handler(cmd):
                    func(update)
                    match = True
                    break
        if not match:
            print('No handler found')

    @staticmethod
    def _check_handler(cmd: dict, update: Update):
        text = update.text
        if update.callback_data:
            if 'cmd' in update.callback_data and 'button' in cmd:
                if cmd['button'] == update.callback_data['cmd']:
                    return True
        if cmd.get('text', False):
            if text == cmd['text']:
                return True
        if cmd.get('regex', False):
            pattern = re.compile(cmd['regex'])
            if pattern.match(text):
                return True
        if cmd.get('command', False):
            if text == cmd['command']:
                return True
        return False

    @staticmethod
    def _match_any_handler(cmd: dict):
        if cmd.get('any', False):
            if cmd['any']:
                return True
        return False

    def list_handlers(self):
        for handler in self._handlers:
            print(f'Handler: {handler}')
