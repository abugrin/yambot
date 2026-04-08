from typing import Annotated, Dict, Literal, Optional, List, Any, Union
from pydantic import BaseModel, Discriminator, Field, Tag

class Sender(BaseModel):
    """ Message sender model
    Can have login or id, but not both

    Attributes:
        login (str): User login if message was sent to personal or group chat
        from_id (str): Channel id if message was sent to channel
        display_name (str): Sender display name
        robot (bool): Is sender a robot

    """
    login: Optional[str] = None
    from_id: Optional[str] = Field(alias='id', default=None)
    display_name: Optional[str] = None
    robot: Optional[bool] = None

class Chat(BaseModel):
    """ Chat object model

    Attributes:
        chat_type (Literal['private', 'group', 'channel']): Chat type
        chat_id (str): Chat id. Only if chat type is group or channel

    """

    chat_type: Literal['private', 'group', 'channel'] = Field(alias = 'type')
    chat_id: Optional[str] = Field(alias = 'id', default = None)
    thread_id: Optional[int] = None


class File(BaseModel):
    """ File object model

    Attributes:
        file_id (str): File id. Used to download file
        name (str): File name
        size (int): File size in bytes

    """
    file_id: str = Field(alias = 'id')
    name: str
    size: int

class Image(BaseModel):
    """Image object model

    Attributes:
        file_id (str): File id. Used to download file
        width (int): Image width
        height (int): Image height
        size (int): Image size in bytes
        name (str): Image name
    """

    file_id: str
    width: int
    height: int
    size: Optional[int] = None
    name: Optional[str] = None


class Button(BaseModel):
    """Button object model for inline keyboard

    .. deprecated:: 0.2.0
        Use :class:`InlineSuggestButton` and :class:`SuggestButtons` instead.

    Attributes:
        text (str): Text on the button
        callback_data (Dict): Data to be sent when button is pressed
    """
    text: str
    callback_data: Optional[Dict] = None


class OpenUriDirective(BaseModel):
    """Opens a URL in the browser when button is clicked."""
    type: Literal['open_uri'] = 'open_uri'
    uri: str


class SendMessageDirective(BaseModel):
    """Sends a message to the chat on behalf of the user who clicked the button."""
    type: Literal['send_message'] = 'send_message'
    text: str
    payload: Optional[Dict] = None


class ServerActionDirective(BaseModel):
    """Sends a server action to the bot. The message does not appear in chat --
    the bot only receives a notification about the button click."""
    type: Literal['server_action'] = 'server_action'
    name: str
    payload: Dict
    text: Optional[str] = None


class SetElementsStateDirective(BaseModel):
    """Changes the state of UI elements (e.g. disables buttons while processing)."""
    type: Literal['set_elements_state'] = 'set_elements_state'
    ids: List[str]
    state: Literal['disabled', 'loading']
    timeout_seconds: Optional[int] = None


def _directive_discriminator(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('type', '')
    return getattr(v, 'type', '')


Directive = Annotated[
    Union[
        Annotated[OpenUriDirective, Tag('open_uri')],
        Annotated[SendMessageDirective, Tag('send_message')],
        Annotated[ServerActionDirective, Tag('server_action')],
        Annotated[SetElementsStateDirective, Tag('set_elements_state')],
    ],
    Discriminator(_directive_discriminator),
]


class InlineSuggestButton(BaseModel):
    """Button displayed under a message with directive-based actions.

    Attributes:
        id: Unique button identifier (max 255 chars)
        title: Button text (max 255 chars)
        directives: Actions to perform on click (max 3)
    """
    id: Optional[str] = None
    title: Optional[str] = None
    directives: Optional[List[Directive]] = None


class SuggestButtons(BaseModel):
    """Keyboard with buttons displayed under a message.

    Attributes:
        layout: Display mode. "false" -- buttons in a single row with wrapping.
                "true" -- buttons arranged in rows per the 2D array in buttons.
        persist: Whether buttons persist after click. If True, buttons remain.
        buttons: Array of buttons. 1D when layout="false", 2D when layout="true".
                 Max 100 buttons total.
    """
    layout: Optional[str] = None
    persist: Optional[bool] = None
    buttons: Optional[Union[List[InlineSuggestButton], List[List[InlineSuggestButton]]]] = None


class ServerAction(BaseModel):
    """Server action received when a user clicks a button with server_action directive.

    Attributes:
        name: Action name (as specified in the directive)
        payload: Arbitrary action data
    """
    name: str
    payload: Optional[Dict] = None


class BotRequestError(BaseModel):
    """Error that occurred while executing a directive on the client.

    Attributes:
        type: Error type (unsupported_directive, invalid_directive_payload, client_error)
        name: Directive name that caused the error
        message: Error message text
    """
    type: str
    name: Optional[str] = None
    message: Optional[str] = None


class BotRequest(BaseModel):
    """Bot request received when a user clicks a button with server_action directive.

    Attributes:
        server_action: The server action from the button
        element_id: ID of the clicked element (button)
        errors: Array of directive execution errors
    """
    server_action: Optional[ServerAction] = None
    element_id: Optional[str] = None
    errors: Optional[List[BotRequestError]] = None


class User(BaseModel):
    """User object model for requests

    Attributes:
        login (str): User login
    """
    login: str


class Vote(BaseModel):
    """Vote object model for polls

    Attributes:
        timestamp (int): Vote ID
        user (Sender): User who voted
    """
    timestamp: int
    user: Sender


class Sticker(BaseModel):
    """Sticker object model

    Attributes:
        sticker_id (str): Sticker ID
        set_id (str): Sticker set ID
    """
    sticker_id: str = Field(alias='id')
    set_id: str


class ForwardedMessage(BaseModel):
    """Forwarded message object model

    Attributes:
        message_id (int): Message ID
        timestamp (int): Message timestamp
        chat (Chat): Chat where message was sent
        from_m (Sender): Original message sender
        text (str): Message text
    """
    message_id: int
    timestamp: int
    chat: Chat
    from_m: Sender = Field(alias='from')
    text: Optional[str] = None


class Update(BaseModel):
    """ Update object bot receives on new messages in personal or group chats or channels

    Attributes:
        from_m (Sender): Message sender
        chat (Chat): Chat object where message was sent
        text (str): Message text
        timestamp (int): Message server time UNIX timestamp
        message_id (int): Message id
        update_id (int): Update id
        callback_data (Dict): Callback data if message was sent by inline keyboard
        file (File): File object if message contains file
        images (List[List[Image]]): List of image lists (for galleries)
        forwarded_messages (List[ForwardedMessage]): Forwarded messages
        sticker (Sticker): Sticker object
        bot_request (BotRequest): Bot request from server_action button click

    """

    from_m: Sender = Field(alias='from')
    chat: Chat
    text: Optional[str] = None
    timestamp: int
    message_id: int
    update_id: int
    callback_data: Optional[Dict] = None
    file: Optional[File] = None
    images: Optional[List[List[Image]]] = None
    forwarded_messages: Optional[List[ForwardedMessage]] = None
    sticker: Optional[Sticker] = None
    bot_request: Optional[BotRequest] = None


class UpdatesResponse(BaseModel):
    updates: List[Update]
    ok: bool

