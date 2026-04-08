from collections.abc import Callable
import logging
import multiprocessing
import os
import sys
from time import sleep
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from yambot import MessengerBot, Update, SuggestButtons, InlineSuggestButton, ServerActionDirective, OpenUriDirective

load_dotenv()
bot_api_key = os.getenv('BOT_KEY')
if not bot_api_key:
    raise ValueError('BOT_KEY not found in .env file')

yb = MessengerBot(bot_api_key)

main_menu_buttons = {}

bot_logger = logging.getLogger('yambot')
bot_logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
bot_logger.addHandler(log_handler)


@yb.add_handler(command='/debug')
def show_handlers(update):
    handlers: List[Tuple[Dict, Callable]] = yb.list_handlers()
    message = 'Handlers:\n'
    for handler in handlers:
        message += f'{handler[0]}, {handler[1].__name__}\n'
    yb.send_message(f'{message}', update)


@yb.add_handler(server_action='do_something')
def handle_action(update):
    payload = update.bot_request.server_action.payload
    yb.send_message(f"Received: {payload}", update)
    yb.send_suggest_buttons("Choose an option:", main_menu_buttons, update)

@yb.add_handler(any=True)
def process_any(update: Update):
    yb.send_suggest_buttons("Choose an option:", main_menu_buttons, update)


def build_menu():
    buttons = SuggestButtons(
        layout="true",
        persist=False,
        buttons=[
            [
                InlineSuggestButton(
                    id="btn1",
                    title="Action Button",
                    directives=[
                        ServerActionDirective(name="do_something", payload={"key": "value"})
                    ]
                ),
                InlineSuggestButton(
                    id="btn2",
                    title="Open Link",
                    directives=[
                        OpenUriDirective(uri="https://ya.ru")
                    ]
                )
            ]
        ]
    )
    return buttons


def send_menu(update, menu):
    yb.send_inline_keyboard(text='Доступные команды:', buttons=menu, update=update)


if __name__ == "__main__":
    main_menu_buttons = build_menu()
    yb.start_pooling()
