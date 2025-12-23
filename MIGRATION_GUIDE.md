# Migration Guide: 0.0.8 → 0.0.9

## Important Changes

### 1. Renamed Methods and Parameters

**Before (0.0.8):**
```python
yb = MessengerBot('token', pool_interval=2)
yb.start_pooling()
```

**After (0.0.9):**
```python
yb = MessengerBot('token', poll_interval=2)
yb.start_polling()
```

**Note:** For backward compatibility, `start_pooling()` and `pool_interval` parameter are still supported but deprecated.

### 2. Type Changes

**Update.chat is now required:**
```python
# Before: chat was Optional[Chat]
# After: chat is Chat (always present)
```

**Update.images type changed:**
```python
# Before: Optional[List[Tuple[ImageThumb, ImageThumb, ImageThumb, Image]]]
# After: Optional[List[List[Image]]]
```

**Sender.from_id is now Optional:**
```python
# Before: from_id: str (always required)
# After: from_id: Optional[str] (either login or from_id is present)
```

### 3. Removed Classes

- `ImageThumb` class removed (not in official API)

## New Features

### 1. Enhanced send_message()

```python
# New parameters available:
yb.send_message(
    text='Hello',
    update=update,
    disable_web_page_preview=True,
    payload_id='unique_id',           # NEW: for idempotency
    reply_message_id=123,             # NEW: reply to message
    disable_notification=False,       # NEW: silent message
    important=True,                   # NEW: mark as important
    thread_id=456                     # NEW: send to thread
)
```

### 2. Polls API

```python
# Create poll
response = yb.create_poll(
    title='What do you prefer?',
    answers=['Option 1', 'Option 2', 'Option 3'],
    update=update,
    max_choices=1,
    is_anonymous=False
)

# Get poll results
results = yb.get_poll_results(message_id=123, update=update)
# Returns: {'voted_count': 5, 'answers': {'1': 3, '2': 2}}

# Get voters for specific answer
voters = yb.get_poll_voters(
    message_id=123,
    answer_id=1,
    update=update,
    limit=100
)
```

### 3. Chat Management API

```python
from yambot import User

# Create chat
response = yb.create_chat(
    name='Team Chat',
    description='Our team discussion',
    members=[User(login='user1@example.com'), User(login='user2@example.com')],
    admins=[User(login='admin@example.com')]
)

# Create channel
response = yb.create_channel(
    name='Announcements',
    description='Company announcements',
    subscribers=[User(login='user1@example.com')],
    admins=[User(login='admin@example.com')]
)

# Update members
yb.update_members(
    chat_id='chat_id_here',
    members=[User(login='newuser@example.com')],
    remove=[User(login='olduser@example.com')]
)

# Get user link
link = yb.get_user_link('user@example.com')
# Returns: {'id': 'user_id', 'chat_link': '...', 'call_link': '...'}
```

### 4. New Type Models

```python
from yambot import Button, User, Vote, Sticker, ForwardedMessage

# Button (typed)
button = Button(text='Click me', callback_data={'cmd': '/action'})

# User (for API requests)
user = User(login='user@example.com')

# Vote (from polls)
vote = Vote(timestamp=123456, user=sender)

# Sticker
sticker = Sticker(id='sticker_id', set_id='set_id')

# ForwardedMessage
forwarded = ForwardedMessage(
    message_id=123,
    timestamp=456,
    chat=chat,
    from_m=sender,
    text='Original message'
)
```

### 5. Error Handling

```python
from yambot import APIError, RateLimitError, ValidationError

try:
    yb.send_message('Hello', update)
except RateLimitError:
    print('Rate limit exceeded, wait and retry')
except ValidationError as e:
    print(f'Invalid input: {e}')
except APIError as e:
    print(f'API error {e.status_code}: {e.message}')
```

### 6. Middleware System

```python
from yambot import LoggingMiddleware, FilterMiddleware, MiddlewareManager

# Add logging middleware
logging_mw = LoggingMiddleware()

# Add filter middleware
def only_text_messages(update):
    return update.text is not None

filter_mw = FilterMiddleware(only_text_messages)

# Note: Middleware integration with MessengerBot is available
# but requires manual setup in current version
```

## Improvements

### Security
- ✅ Added filename sanitization in `send_file()`
- ✅ Input validation for all methods
- ✅ Rate limiting

### Error Handling
- ✅ Automatic retry with exponential backoff
- ✅ Proper handling of 429, 500, 502, 503 errors
- ✅ Custom exception classes for better error handling
- ✅ Detailed error messages and logging

### Code Quality
- ✅ Fixed all type hints
- ✅ Removed code duplication
- ✅ Added comprehensive docstrings
- ✅ Unit tests for core functionality

## Installation

```bash
pip install --upgrade yambot-client
```

## Testing Your Migration

Run your bot with the new version and check for:

1. **Optional but recommended:** Replace `start_pooling()` with `start_polling()` (old method still works with deprecation warning)
2. **Optional but recommended:** Replace `pool_interval` with `poll_interval` (old parameter still works with deprecation warning)
3. Handle new exception types if needed
4. Update any code that accessed `ImageThumb` (should use `Image` instead)
5. Check if your code assumed `Update.chat` could be None

**Note:** Your existing code will continue to work without changes, but you'll see deprecation warnings for `start_pooling()` and `pool_interval`. Update at your convenience.

## Support

If you encounter issues during migration:
- Check the [README](readme.md) for updated examples
- Review the [API documentation](https://yandex.ru/dev/messenger/doc/ru/)
- Open an issue on [GitHub](https://github.com/abugrin/yambot/issues)

