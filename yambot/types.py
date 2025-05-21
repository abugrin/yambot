from typing import Dict, Literal, Optional, List, Tuple
from pydantic import BaseModel, Field

class Sender(BaseModel):
    """ Message sender model
    Can have login or id, but not both

    Attributes:
        login (str): User login if message was sent to persinal or group chat
        from_id (str): Channel id if message was sent to channel
        display_name (str): Sender display name
        robot (bool): Is sender a robot

    """
    login: Optional[str] = None
    from_id: str = Field(alias = 'id')
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

class ImageThumb(BaseModel):
    """ Image thumb object model
    
    Attributes:
        file_id (str): File id with thumbnail size parameter
        width (int): Image width
        height (int): Image height
    """
    file_id: str
    width: int
    height: int


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


class Update(BaseModel):
    """ Update object bot recieve on new messages in personal or group chats or channels

    Attributes:
        from_m (Sender): Message sender
        chat (Chat): Chat object if message was sent to group or channel
        text (str): Message text
        timestamp (int): Message server time UNIX timestamp
        message_id (int): Message id
        update_id (int): Update id
        callback_data (Dict): Callback data if message was sent by inline keyboard
        file (File): File object if message contains file
        image (List[Image]): List of images if message contains images

    """

    from_m: Sender = Field(alias = 'from')
    chat: Optional[Chat] = None
    text: Optional[str] = None
    timestamp: int
    message_id: int
    update_id: int
    callback_data: Optional[Dict] = None
    file: Optional[File] = None
    images: Optional[List[Tuple[ImageThumb, ImageThumb, ImageThumb, Image]]] = None


class UpdatesResponse(BaseModel):
    updates: List[Update]
    ok: bool

