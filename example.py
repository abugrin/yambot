from collections.abc import Callable
import logging
import multiprocessing
import os
import sys
from time import sleep
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from api.gpt_api import send_translate_request, send_art_request, get_art_response
from api.tracker_api import create_ticket
from yambot import MessengerBot, Update

load_dotenv()
bot_api_key = os.getenv('BOT_KEY')
if not bot_api_key:
    raise ValueError('BOT_KEY not found in .env file')

yb = MessengerBot(bot_api_key, client_type='httpx')

main_menu = []
translate_requests = {}
pass_requests = {}
art_requests = {}
art_queue = {}

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

@yb.add_handler(command='/file')
def send_file(update: Update):
    with open('test.pdf', 'rb') as f:
        yb.send_file(f, 'test.pdf', 'application/pdf', update)
    send_menu(update, main_menu)


@yb.add_handler(button='/translate')
def translate_button(update: Update):
    yb.send_message('Введите текст для перевода:', update)
    translate_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/pass')
def pass_button(update: Update):
    yb.send_message('Введите имя и фамилию для заказа пропуска:', update)
    pass_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/pass_yes')
def pass_yes(update: Update):
    if update.callback_data:
        res = create_ticket(update.callback_data['name'])
        yb.send_message(f"Заявка на пропуск оформлена: https://tracker.yandex.ru/{res['key']}", update)
        send_menu(update, main_menu)


@yb.add_handler(button='/pass_no')
def pass_no(update):
    yb.send_message('"Заказ пропуска отменен', update)
    send_menu(update, main_menu)


@yb.add_handler(button='/art')
def art_button(update: Update):
    yb.send_message('Введите текст для генерации изображения:', update)
    art_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/art_yes')
def art_yes(update: Update):
    if update.callback_data:
        response = send_art_request(update.callback_data['text'])
        bot_logger.debug(f"Art response: {response}")
        try:
            yb.send_message(f"Отправлен запрос на генерацию изображения. Id запроса: {response['id']}", update)
            art_queue.update({f"{response['id']}": update})
        except KeyError:
            yb.send_message(f"Ошибка: {response['error']}", update)
            send_menu(update, main_menu)


@yb.add_handler(button='/art_no')
def art_no(update):
    yb.send_message('Генерация изображения отменена', update)
    send_menu(update, main_menu)


@yb.add_handler(any=True)
def process_any(update: Update):
    if update.file:
        try:
            yb.download_file(update, './downloads/')
            yb.send_message(f"Файл {update.file.name} ({update.file.size} байт) загружен", update)
        except Exception as e:
            yb.send_message(f"Ошибка при загрузке файла {update.file}\n{e}", update)

    elif f'{update.from_m.from_id}' in translate_requests:
        response = send_translate_request(update.text)
        text = response['translations'][0]['text']
        yb.send_message(f"Перевод:\n```{text}```", update)
        translate_requests.pop(f'{update.from_m.from_id}', None)
        send_menu(update, main_menu)
    elif f'{update.from_m.from_id}' in pass_requests:
        button_pass_yes = {'text': 'Да', 'callback_data': {'cmd': '/pass_yes', 'name': update.text}}
        button_pass_no = {'text': 'Нет', 'callback_data': {'cmd': '/pass_no'}}
        yb.send_inline_keyboard(
            f'Заказать пропуск для: {update.text}?',
            [button_pass_yes, button_pass_no],
            update
        )
        pass_requests.pop(f'{update.from_m.from_id}', None)
    elif f'{update.from_m.from_id}' in art_requests:
        button_art_yes = {'text': 'Да', 'callback_data': {'cmd': '/art_yes', 'text': update.text}}
        button_art_no = {'text': 'Нет', 'callback_data': {'cmd': '/art_no'}}
        yb.send_inline_keyboard(
            f'Сгенерировать изображение по запросу: {update.text}?',
            [button_art_yes, button_art_no],
            update
        )
    else:
        send_menu(update, main_menu)


def art_thread(art_q: Dict, menu):
    #  global art_queue

    try:
        while True:
            if len(art_q) > 0:
                bot_logger.debug(f"Art queue size: {len(art_q)}")
            for art_request in art_q.keys():
                response = get_art_response(art_request)
                if response['done']:
                    try:
                        yb.send_message("Изображение готово", art_q[art_request])
                        image_data = response['response']['image']
                        yb.send_image(image_data, art_q[art_request])
                        send_menu(art_q[art_request], menu)
                        art_q.pop(art_request, None)
                    except Exception as e:
                        bot_logger.error(f"Failed to send image: {str(e)}", exc_info=True)
                    break

                else:
                    bot_logger.debug(art_q)
                    yb.send_message("Генерируется...", art_q[art_request])

            sleep(10)
    except KeyboardInterrupt:
        bot_logger.info('Stopping art thread...')
    

def build_menu():
    button_help = {'text': 'Помощь', 'callback_data': {'cmd': '/help'}}
    button_hello = {'text': 'Я всё вижу', 'callback_data': {'cmd': '/hello'}}
    button_art = {'text': 'Генерация изображения', 'callback_data': {'cmd': '/art'}}
    button_translate = {'text': 'Перевод', 'callback_data': {'cmd': '/translate'}}
    button_pass = {'text': 'Пропуск', 'callback_data': {'cmd': '/pass'}}
    return [button_help, button_hello, button_art, button_translate, button_pass]


def send_menu(update, menu):
    yb.send_inline_keyboard(text='Доступные команды:', buttons=menu, update=update)


if __name__ == "__main__":
    main_menu = build_menu()
    manager = multiprocessing.Manager()
    art_queue = manager.dict()
    art_process = multiprocessing.Process(target=art_thread, args=(art_queue, main_menu))

    bot_logger.info('Starting art thread...')
    art_process.start()
    yb.start_pooling()
