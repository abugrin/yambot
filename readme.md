## Unofficial Yandex Messenger Bot API library

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
# Send text message
yb.send_message('text', update)

# Send image
yb.send_image(image_data, update)

# Send buttons
yb.send_inline_keyboard('Choose:', buttons, update)

# Delete message (from group chat)
yb.delete_message(message_id=123, chat_id='0/0/group-id')

# Delete message (from private chat)
yb.delete_message(message_id=456, login='user@example.com')

# Delete message (from thread)
yb.delete_message(message_id=789, chat_id='0/0/group-id', thread_id=100)

```

Button example for `send_inline_keyboard()`:
```python
button1 = {'text': 'Button 1', 'callback_data': {'cmd': '/button_1'}}
button2 = {'text': 'Button 2', 'callback_data': {'cmd': '/button_2'}}

buttons = [button1, button2]
```

### Example: [link](https://github.com/abugrin/yambot/blob/master/example.py)


### Update 0.1.0 (Latest)
**Improvements:**
- ✅ Fixed bugs
- ✅ Added error handling
- ✅ Implemented rate limiting
- ✅ Added support for **Polls API** (`create_poll`, `get_poll_results`, `get_poll_voters`)
- ✅ Added support for **Chat Management API** (`create_chat`, `create_channel`, `update_members`, `get_user_link`)
- ✅ Added new type models: `Button`, `User`, `Vote`, `Sticker`, `ForwardedMessage`
- ✅ Enhanced `send_message()` with additional parameters: `payload_id`, `reply_message_id`, `disable_notification`, `important`, `thread_id`
- ✅ Fixed naming: `pooling` → `polling`

**New Methods:**
```python
# Polls
yb.create_poll(title, answers, update)
yb.get_poll_results(message_id, update)
yb.get_poll_voters(message_id, answer_id, update)

# Chat Management
yb.create_chat(name, description, members, admins)
yb.create_channel(name, description, subscribers, admins)
yb.update_members(chat_id, members, admins, remove)
yb.get_user_link(login)
```

**Important Changes:**
- `Update.chat` is now required (not Optional)
- `Update.images` type changed from `List[Tuple[...]]` to `List[List[Image]]`

**Deprecations:**
- `start_pooling()` → use `start_polling()` instead
- `pool_interval` parameter → use `poll_interval` instead

### Update 0.0.5
- Added bot send gallery method `yb.send_gallery(images, update)` where `images` is a list of image objects same as in`send_image` method  
- Bot send methods will return JSON response with `message_id`
- Added optional argument `disable_web_page_preview` to `yb.send_message(images, update, disable_web_page_preview=True)` method. Default value is `True`

### Update 0.0.4
- Added logger support.
Create bot instance with `log_level=logging.DEBUG` argument for debug output. By default log level is INFO.   
```yb = MessengerBot('bot_token', log_level=logging.DEBUG)```


