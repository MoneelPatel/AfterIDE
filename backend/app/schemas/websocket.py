"""
AfterIDE - WebSocket Message Schemas

Defines message structures and validation for WebSocket communication.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from enum import Enum
from datetime import datetime


class MessageType(str, Enum):
    """WebSocket message types."""
    # Connection messages
    CONNECTION_ESTABLISHED = "connection_established"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Terminal messages
    COMMAND = "command"
    COMMAND_RESPONSE = "command_response"
    TERMINAL_OUTPUT = "terminal_output"
    TERMINAL_RESIZE = "terminal_resize"
    
    # File messages
    FILE_UPDATE = "file_update"
    FILE_UPDATED = "file_updated"
    FILE_REQUEST = "file_request"
    FILE_CONTENT = "file_content"
    FILE_DELETE = "file_delete"
    FILE_DELETED = "file_deleted"
    FILE_RENAME = "file_rename"
    FILE_RENAMED = "file_renamed"
    FILE_LIST = "file_list"
    FILE_LIST_RESPONSE = "file_list_response"
    FOLDER_CREATE = "folder_create"
    FOLDER_CREATED = "folder_created"
    
    # Notification messages
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system_message"


class BaseMessage(BaseModel):
    """Base message structure."""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None


class ConnectionMessage(BaseMessage):
    """Connection establishment message."""
    connection_id: str
    session_id: str
    user_id: Optional[str] = None
    message: str


class ErrorMessage(BaseMessage):
    """Error message."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PingMessage(BaseMessage):
    """Ping message for heartbeat."""
    pass


class PongMessage(BaseMessage):
    """Pong response message."""
    pass


# Terminal Messages
class CommandMessage(BaseMessage):
    """Terminal command message."""
    command: str
    working_directory: Optional[str] = None


class CommandResponseMessage(BaseMessage):
    """Terminal command response message."""
    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: Optional[float] = None
    working_directory: Optional[str] = None


class TerminalOutputMessage(BaseMessage):
    """Terminal output message."""
    output: str
    stream: str = "stdout"  # stdout or stderr


class TerminalResizeMessage(BaseMessage):
    """Terminal resize message."""
    cols: int
    rows: int


# File Messages
class FileUpdateMessage(BaseMessage):
    """File update message."""
    filename: str
    content: str
    language: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None


class FileUpdatedMessage(BaseMessage):
    """File updated notification message."""
    filename: str
    content: str
    updated_by: str
    language: Optional[str] = None


class FileRequestMessage(BaseMessage):
    """File request message."""
    filename: str


class FileContentMessage(BaseMessage):
    """File content response message."""
    filename: str
    content: str
    language: Optional[str] = None
    last_modified: Optional[datetime] = None


class FileDeleteMessage(BaseMessage):
    """Message for file deletion."""
    type: MessageType = MessageType.FILE_DELETE
    filename: str = Field(..., description="File path to delete")


class FolderCreateMessage(BaseMessage):
    """Message for folder creation."""
    type: MessageType = MessageType.FOLDER_CREATE
    foldername: str = Field(..., description="Folder name to create")
    parent_path: Optional[str] = Field(default="/", description="Parent directory path")


class FolderCreatedMessage(BaseMessage):
    """Message sent when folder is created."""
    type: MessageType = MessageType.FOLDER_CREATED
    foldername: str = Field(..., description="Created folder name")
    folderpath: str = Field(..., description="Full folder path")
    parent_path: Optional[str] = Field(default="/", description="Parent directory path")


class FileDeletedMessage(BaseMessage):
    """File deleted notification message."""
    type: MessageType = MessageType.FILE_DELETED
    filename: str = Field(..., description="Deleted file path")
    deleted_by: str = Field(..., description="ID of connection that deleted the file")


class FileRenameMessage(BaseMessage):
    """File rename message."""
    old_filename: str
    new_filename: str


class FileRenamedMessage(BaseMessage):
    """File renamed notification message."""
    old_filename: str
    new_filename: str
    renamed_by: str


class FileListMessage(BaseMessage):
    """File list request message."""
    directory: Optional[str] = None


class FileListResponseMessage(BaseMessage):
    """File list response message."""
    files: List[Dict[str, Any]]
    directory: str


# Notification Messages
class NotificationMessage(BaseMessage):
    """General notification message."""
    title: str
    message: str
    level: str = "info"  # info, warning, error, success
    duration: Optional[int] = None  # milliseconds


class SystemMessage(BaseMessage):
    """System message."""
    message: str
    level: str = "info"
    data: Optional[Dict[str, Any]] = None


# Message validation functions
def validate_message(data: Dict[str, Any]) -> BaseMessage:
    """Validate and create appropriate message object."""
    message_type = data.get("type")
    
    if not message_type:
        raise ValueError("Message type is required")
    
    try:
        message_type_enum = MessageType(message_type)
    except ValueError:
        raise ValueError(f"Invalid message type: {message_type}")
    
    # Create appropriate message object based on type
    message_classes = {
        MessageType.CONNECTION_ESTABLISHED: ConnectionMessage,
        MessageType.ERROR: ErrorMessage,
        MessageType.PING: PingMessage,
        MessageType.PONG: PongMessage,
        MessageType.COMMAND: CommandMessage,
        MessageType.COMMAND_RESPONSE: CommandResponseMessage,
        MessageType.TERMINAL_OUTPUT: TerminalOutputMessage,
        MessageType.TERMINAL_RESIZE: TerminalResizeMessage,
        MessageType.FILE_UPDATE: FileUpdateMessage,
        MessageType.FILE_UPDATED: FileUpdatedMessage,
        MessageType.FILE_REQUEST: FileRequestMessage,
        MessageType.FILE_CONTENT: FileContentMessage,
        MessageType.FILE_DELETE: FileDeleteMessage,
        MessageType.FILE_DELETED: FileDeletedMessage,
        MessageType.FILE_RENAME: FileRenameMessage,
        MessageType.FILE_RENAMED: FileRenamedMessage,
        MessageType.FILE_LIST: FileListMessage,
        MessageType.FILE_LIST_RESPONSE: FileListResponseMessage,
        MessageType.FOLDER_CREATE: FolderCreateMessage,
        MessageType.FOLDER_CREATED: FolderCreatedMessage,
        MessageType.NOTIFICATION: NotificationMessage,
        MessageType.SYSTEM_MESSAGE: SystemMessage,
    }
    
    message_class = message_classes.get(message_type_enum)
    if not message_class:
        raise ValueError(f"No message class found for type: {message_type}")
    
    return message_class(**data)


def create_error_message(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> ErrorMessage:
    """Create an error message."""
    return ErrorMessage(
        type=MessageType.ERROR,
        error_code=error_code,
        message=message,
        details=details
    )


def create_pong_message() -> PongMessage:
    """Create a pong response message."""
    return PongMessage(type=MessageType.PONG) 