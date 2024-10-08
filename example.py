import logging
import multiprocessing
import os
from time import sleep

from dotenv import load_dotenv

from api.gpt_api import send_translate_request, send_art_request, get_art_response
from api.tracker_api import create_ticket
from yambot.yambot import MessengerBot

load_dotenv()
yb = MessengerBot(os.getenv('BOT_KEY'), log_level=logging.DEBUG)
main_menu = []
translate_requests = {}
pass_requests = {}
art_requests = {}
art_queue = {}


@yb.add_handler(command='/debug')
def show_handlers(update):
    yb.list_handlers()


@yb.add_handler(button='/translate')
def translate_button(update):
    yb.send_message(f'Введите текст для перевода:', update)
    translate_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/pass')
def pass_button(update):
    yb.send_message(f'Введите имя и фамилию для заказа пропуска:', update)
    pass_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/pass_yes')
def pass_yes(update):
    res = create_ticket(update.callback_data['name'])
    yb.send_message(f"Заявка на пропуск оформлена: https://tracker.yandex.ru/{res['key']}", update)
    send_menu(update, main_menu)


@yb.add_handler(button='/pass_no')
def pass_no(update):
    yb.send_message(f'"Заказ пропуска отменен', update)
    send_menu(update, main_menu)


@yb.add_handler(button='/art')
def art_button(update):
    yb.send_message(f'Введите текст для генерации изображения:', update)
    art_requests.update({f'{update.from_m.from_id}': update})


@yb.add_handler(button='/art_yes')
def art_yes(update):
    response = send_art_request(update.callback_data['text'])
    print(f"Art response: {response}")
    try:
        yb.send_message(f"Отправлен запрос на генерацию изображения. Id запроса: {response['id']}", update)
        art_queue.update({f"{response['id']}": update})
    except KeyError:
        yb.send_message(f"Ошибка: {response['error']}", update)
        send_menu(update, main_menu)


@yb.add_handler(button='/art_no')
def art_no(update):
    yb.send_message(f'"Генерация изображения отменена', update)
    send_menu(update, main_menu)


@yb.add_handler(any=True)
def process_any(update):
    if f'{update.from_m.from_id}' in translate_requests:
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


def art_thread(art_q, menu):
    #  global art_queue
    while True:
        print("Art queue size: ", len(art_q))
        for art_request in art_q.keys():
            response = get_art_response(art_request)
            if response['done']:
                yb.send_message("Изображение готово", art_q[art_request])
                yb.send_image(response['response']['image'], art_q[art_request])
                send_menu(art_q[art_request], menu)
                art_q.pop(art_request, None)
                break

            else:
                print(art_q)
                yb.send_message("Генерируется...", art_q[art_request])
        # print("Sleeping")
        sleep(10)


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

    print('Starting art thread...')
    art_process.start()
    yb.start_pooling()
