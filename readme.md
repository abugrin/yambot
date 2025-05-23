# Yambot Client

## Unofficial Yandex Messenger Bot API library

## Documentation
Messenget Bot API [link](https://yandex.ru/dev/messenger/doc/ru/)
Obtaining Messenger Bot token: [link](https://yandex.ru/support/yandex-360/business/admin/ru/bot-platform.html#bot-create) 

### Installation

Basic installation with requests:
```bash
pip install yambot-client
```

With async support (aiohttp):
```bash
pip install yambot-client[async]
```

With HTTPX support:
```bash
pip install yambot-client[httpx]
```

With all HTTP clients:
```bash
pip install yambot-client[all]
```

### Usage

Basic usage with default requests client:
```python
from yambot import MessengerBot

# Create bot with default requests client
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

Using HTTPX client:
```python
# Create bot with HTTPX client
yb = MessengerBot('bot_token', client_type='httpx')
```

Using async client with aiohttp:
```python
import asyncio
from yambot import MessengerBot

async def main():
    # Create bot with async client
    yb = MessengerBot('bot_token', client_type='async')
    
    # Note: When using async client, all bot methods become coroutines
    await yb.send_message('Hello', update)
    
    # Don't forget to close the client when done
    await yb.close()

asyncio.run(main())
```

### Available Bot methods

```python
# Send text message. If update has chat or thread id message will be sent to chat or thread
# Otherwise message will be sent directly to user
yb.send_message('text', update, disable_web_page_preview=True)  # disable_web_page_preview is optional, defaults to True

# Send image. image_data can be either ASCII string or bytes object
yb.send_image(image_data, update)

# Send multiple images as a gallery
images = [image1_data, image2_data, image3_data]  # List of image data (ASCII strings or bytes)
yb.send_gallery(images, update)

# Send buttons. buttons must be a list of Button objects
yb.send_inline_keyboard(text='Menu text', buttons=buttons, update=update)

# Send file with specific MIME type
with open('document.pdf', 'rb') as f:
    yb.send_file(f, 'document.pdf', 'application/pdf', update)

# Download file from update to specific directory
yb.download_file(update, dir='downloads/')

# List all registered handlers
handlers = yb.list_handlers()  # Returns List[Tuple[Dict, Callable]]

# Close the bot client (important when using async client)
await yb.close()  # Only for async client
```

### Button Examples

You can create various types of inline keyboard buttons:

```python
# Simple command buttons
button1 = {'text': 'Help', 'callback_data': {'cmd': '/help'}}
button2 = {'text': 'Start', 'callback_data': {'cmd': '/start'}}

# Buttons with additional data
button3 = {'text': 'Process Item', 'callback_data': {'cmd': '/process', 'item_id': '123'}}

# Creating a menu with multiple buttons
menu_buttons = [
    {'text': 'Help', 'callback_data': {'cmd': '/help'}},
    {'text': 'Settings', 'callback_data': {'cmd': '/settings'}},
    {'text': 'Profile', 'callback_data': {'cmd': '/profile'}}
]

# Send the menu
yb.send_inline_keyboard(text='Choose an option:', buttons=menu_buttons, update=update)
```

### Handler Examples

Here are examples of different types of handlers:

```python
# Command handler with specific command
@yb.add_handler(command='/start')
def start_handler(update):
    yb.send_message('Welcome!', update)

# Text handler that matches exact text
@yb.add_handler(text='hello')
def hello_handler(update):
    yb.send_message('Hi there!', update)

# Button handler for specific callback command
@yb.add_handler(button='/settings')
def settings_handler(update):
    # Access additional callback data if provided
    if update.callback_data:
        setting_id = update.callback_data.get('setting_id')
        yb.send_message(f'Accessing setting {setting_id}', update)

# Regex handler for pattern matching
@yb.add_handler(regex=r'\d{4}-\d{2}-\d{2}')  # Matches dates like 2024-03-21
def date_handler(update):
    yb.send_message('Found a date!', update)

# File handler example
@yb.add_handler(any=True)
def file_handler(update):
    if update.file:
        try:
            yb.download_file(update, './downloads/')
            yb.send_message(f"File {update.file.name} ({update.file.size} bytes) downloaded", update)
        except Exception as e:
            yb.send_message(f"Error downloading file: {e}", update)
```

### HTTP Client Configuration

You can configure the HTTP client behavior using additional parameters:

```python
# Configure requests client
yb = MessengerBot(
    'bot_token',
    client_type='requests',
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10,
    retry_delay=2
)

# Configure HTTPX client
from httpx import Limits
yb = MessengerBot(
    'bot_token',
    client_type='httpx',
    max_retries=3,
    limits=Limits(max_keepalive_connections=10, max_connections=10)
)

# Configure async client
yb = MessengerBot(
    'bot_token',
    client_type='async',
    max_retries=3
)
```

### Logging Configuration

The library uses Python's standard logging module. You can configure it like this:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('yambot')
logger.setLevel(logging.DEBUG)

# Create bot with specific log level
yb = MessengerBot('bot_token', log_level=logging.DEBUG)
```

### Example
For a complete example, see: [link](https://github.com/abugrin/yambot/blob/master/example.py)

### Updates

#### 0.2.0
- Added support for multiple HTTP clients (requests, httpx, aiohttp)
- Improved error handling and retry logic
- Added proper logging configuration
- Added type hints and improved documentation

#### 0.0.5
- Added bot send gallery method `yb.send_gallery(images, update)` where `images` is a list of image objects same as in`send_image` method  
- Bot send methods will return JSON response with `message_id`
- Added optional argument `disable_web_page_preview` to `yb.send_message(images, update, disable_web_page_preview=True)` method. Default value is `True`

#### 0.0.4
- Added logger support.
Create bot instance with `log_level=logging.DEBUG` argument for debug output. By default log level is INFO.   
```yb = MessengerBot('bot_token', log_level=logging.DEBUG)```


