## Yandex Messenger Bot API library

Obtaining Messenger bot token: [link](https://yandex.ru/support/yandex-360/business/admin/ru/bot-platform.html#bot-create) 

Usage: 
```pip install yambot-client```

```python
# Add handlers to MessengerBot
# Supported handlers: text, command, button, regex, any

from yambot import MessengerBot

yb = MessengerBot('bot_token')

# Add command handler ex. when user sends /my_command
@yb.add_handler(command='/my_command')
def my_handler1(update):
    yb.send_message('test1', update)

# Add text handler ex. when user sends some_text
@yb.add_handler(text='some_text')
def my_handler2(update):
    yb.send_message('test2', update)

# Add button handler. Button must have callback_data with 'cmd': '/my_button' JSON object
# For more details about CallbackData see API description: https://yandex.ru/dev/messenger/doc/ru/data-types#button 
@yb.add_handler(button='/my_button')
def my_handler3(update):
    yb.send_message('test3', update)

# Add regex handler. Provide regular expression that will be tested against user text message 
@yb.add_handler(regex='\d{5}')
def my_handler3(update):
    yb.send_message('test4', update)

# Handler that will be applied when no other handlers match
@yb.add_handler(any=True)
def process_any(update):
    yb.send_message('Unknown text', update)


```

Available Bot methods:

```python
# Send text message. If update has chat or thread id message will be sent to chat or thread
# Otherwise message will be sent directly to user
yb.send_message('text', update)

# Send image. image_data can be either ASCII string or bytes object
yb.send_image(image_data, update)

# Send buttons. buttons must be a list of Button objects
yb.send_inline_keyboard(buttons, update)

```

Button example for `send_inline_keyboard()`:
```python
button1 = {'text': 'Button 1', 'callback_data': {'cmd': '/button_1'}}
button2 = {'text': 'Button 2', 'callback_data': {'cmd': '/button_2'}}

buttons = [button1, button2]
```

### Example: [link](https://github.com/abugrin/yambot/blob/master/example.py)


### Update 0.0.5
- Added bot send gallery method `yb.send_gallery(images, update)` where `images` is a list of image objects same as in`send_image` method  
- Bot send methods will return JSON response with `message_id`
- Added optional argument `disable_web_page_preview` to `yb.send_message(images, update, disable_web_page_preview=True)` method. Default value is `True`

### Update 0.0.4
- Added logger support.
Create bot instance with `log_level=logging.DEBUG` argument for debug output. By default log level is INFO.   
```yb = MessengerBot('bot_token', log_level=logging.DEBUG)```


