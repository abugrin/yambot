from typing import Dict, Literal, Optional, List, Any
from pydantic import BaseModel, Field

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

    Attributes:
        text (str): Text on the button
        callback_data (Dict): Data to be sent when button is pressed
    """
    text: str
    callback_data: Optional[Dict] = None


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


class UpdatesResponse(BaseModel):
    updates: List[Update]
    ok: bool

