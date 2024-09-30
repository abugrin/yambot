import os
import re

from dotenv import load_dotenv
from yandex_tracker_client import TrackerClient
from yandex_tracker_client.exceptions import NotFound, BadRequest
from yandex_tracker_client.objects import Resource

from yambot.yambot import MessengerBot

load_dotenv()
yb = MessengerBot(os.getenv('BOT_KEY'))
tc = TrackerClient(token=os.getenv('TRACKER_KEY'), org_id=os.getenv('TRACKER_ORG'))
main_menu = []
tea_menu = []
order_selection = ''
order_email = None
order_name = ''
order_request = ''
status_request = ''
name_waiting = False
email_waiting = False
status_waiting = False
EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')


@yb.add_handler(command='/debug')
def show_handlers(update):
    yb.list_handlers()


@yb.add_handler(button='/list')
def list_button(update):
    yb.send_message('Варианты баблти:', update)
    with open("red.jpg", "rb") as f:
        yb.send_image(f, update)
        yb.send_message('1) Красный чай. С нотками кирпича!', update)
    with open("orange.jpg", "rb") as f:
        yb.send_image(f, update)
        yb.send_message('2) Оранжевый чай. Почти как апельсиновая корка!', update)
    with open("blue.jpg", "rb") as f:
        yb.send_image(f, update)
        yb.send_message('3) Синий чай. Море мне в рот!', update)
    send_menu(update, main_menu)


@yb.add_handler(button='/order')
def order_button(update):
    # yb.delete_message(update)
    yb.send_inline_keyboard(text='Выберите баблти:', buttons=tea_menu, update=update)

@yb.add_handler(button='/tea_red')
def tea_red_button(update):
    tea_button('Красный чай', update)

@yb.add_handler(button='/tea_orange')
def tea_red_button(update):
    tea_button('Оранжевый чай', update)

@yb.add_handler(button='/tea_blue')
def tea_blue_button(update):
    tea_button('Синий чай', update)

@yb.add_handler(button='/tea_back')
def tea_blue_button(update):
    send_menu(update, main_menu)

def tea_button(tea, update):
    global order_selection
    global name_waiting
    order_selection = tea
    name_waiting = True
    yb.send_message(text = 'Как вас зовут?', update=update)


@yb.add_handler(button='/status')
def status_button(update):
    global status_waiting
    status_waiting = True
    yb.send_message(f'Введите номер заказа. Например если ваш заказ PASS-27, то введите 27', update)


@yb.add_handler(any=True)
def process_any(update):
    global name_waiting
    global email_waiting
    global order_name
    global order_email
    global order_selection
    global status_waiting
    global status_request

    if name_waiting:
        order_name = update.text
        name_waiting = False
        email_waiting = True
        yb.send_message(text = f'{order_name}. Укажите ваш емейл для отправки уведомления о готовности:', update=update)
    elif email_waiting:
        if not EMAIL_REGEX.fullmatch(update.text):
            yb.send_message(text = 'Неверный формат емейла. Попробуйте еще раз.', update=update)
        else:
            order_email = update.text
            email_waiting = False
            res: Resource = tc.issues.create(
                queue='PASS', summary=f'Заказ для {order_name}', description=f'Коктейль: {order_selection}'
            )
            order_key = res.as_dict()['key']
            print(f"Issue created: {res.as_dict()}")
            yb.send_message(
                text = f'Заказано баблти {order_selection} для {order_name}.\n'
                       f'Задача в трекере: https://tracker.yandex.ru/{order_key}\n'
                       f'Мы свяжемся с вами по вашему емейлу {order_email} о готовности.', update=update)
            order_name = ''
            order_email = ''
            order_selection = ''
            send_menu(update, main_menu)
    elif status_waiting:
        status_request = update.text
        try:
            res: Resource = tc.issues.get(queue='PASS', key=f'PASS-{status_request}')
            print(f'Status response {res.as_dict()}')
            yb.send_message(f'Статус заказа: {res.as_dict()['status']['key']}', update)
        except NotFound:
            yb.send_message(f'Заказа с таким номером не существует.', update)
        except BadRequest:
            yb.send_message(f'Неправильный номер заказа.', update)

        status_waiting = False
        status_request = ''
        send_menu(update, main_menu)

    else:
        send_menu(update, main_menu)


def build_menu():
    button_list = {'text': 'Описание коктейлей', 'callback_data': {'cmd': '/list'}}
    button_order = {'text': 'Заказать баблти', 'callback_data': {'cmd': '/order'}}
    button_status = {'text': 'Статус заказа', 'callback_data': {'cmd': '/status'}}
    return [button_list, button_order, button_status]


def build_tea_menu():
    button_red = {'text': '1. Красный чай', 'callback_data': {'cmd': '/tea_red'}}
    button_orange = {'text': '2. Оранжевый чай', 'callback_data': {'cmd': '/tea_orange'}}
    button_blue = {'text': '3. Синий чай', 'callback_data': {'cmd': '/tea_blue'}}
    button_tea_back = {'text': 'Назад', 'callback_data': {'cmd': '/tea_back'}}
    return [button_red, button_orange, button_blue, button_tea_back]


def send_menu(update, menu):
    yb.send_inline_keyboard(text='Доступные команды:', buttons=menu, update=update)


if __name__ == "__main__":
    main_menu = build_menu()
    tea_menu = build_tea_menu()

    yb.start_pooling()
