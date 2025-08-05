"""
AfterIDE - WebSocket Service

Manages WebSocket connections for real-time terminal communication and file synchronization.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import json
import structlog
import uuid
from datetime import datetime

from app.schemas.websocket import (
    validate_message, create_error_message, create_pong_message,
    MessageType, BaseMessage, CommandMessage, FileUpdateMessage,
    FileRequestMessage, FileListMessage, CommandResponseMessage,
    FileDeleteMessage, FileRenameMessage, FolderCreateMessage,
    PongMessage, InputResponseMessage, InterruptMessage
)
from app.services.terminal import terminal_service
from app.services.workspace import WorkspaceService

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self):
        # Connection storage
        self.connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Session-based connection groups
        self.session_connections: Dict[str, Set[str]] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Message queue for offline scenarios
        self.message_queue: Dict[str, list] = {}
        
        # Workspace service (will be set by dependency injection)
        self.workspace_service = None
    
    def set_workspace_service(self, workspace_service: WorkspaceService):
        """Set the workspace service for database operations."""
        self.workspace_service = workspace_service
        # Also set it for the terminal service
        terminal_service.set_workspace_service(workspace_service)
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        connection_type: str = "general"
    ):
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            connection_id: Unique connection identifier
            session_id: Session identifier
            user_id: User identifier (optional)
            connection_type: Type of connection (terminal, files, etc.)
        """
        # Store connection
        self.connections[connection_id] = websocket
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "connection_type": connection_type,
            "connected_at": datetime.utcnow()
        }
        
        # Add to session group
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
        
        # Add to user group
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Initialize message queue for this connection
        self.message_queue[connection_id] = []
        
        # Create terminal session if this is a terminal connection
        if connection_type == "terminal":
            terminal_service.create_session(session_id)
        
        logger.info(
            "WebSocket connected",
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            connection_type=connection_type
        )
    
    async def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id not in self.connections:
            return
        
        # Get metadata before removal
        metadata = self.connection_metadata.get(connection_id, {})
        session_id = metadata.get("session_id")
        user_id = metadata.get("user_id")
        connection_type = metadata.get("connection_type")
        
        # Remove from connections
        del self.connections[connection_id]
        del self.connection_metadata[connection_id]
        
        # Remove from session group
        if session_id and session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
                # Clean up terminal session if no more terminal connections
                if connection_type == "terminal":
                    terminal_service.cleanup_session(session_id)
        
        # Remove from user group
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clean up message queue
        if connection_id in self.message_queue:
            del self.message_queue[connection_id]
        
        logger.info(
            "WebSocket disconnected",
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            connection_type=connection_type
        )
    
    async def send_message(self, connection_id: str, message: BaseMessage):
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Target connection identifier
            message: Message to send
        """
        if connection_id not in self.connections:
            # Queue message for later delivery
            if connection_id not in self.message_queue:
                self.message_queue[connection_id] = []
            self.message_queue[connection_id].append(message)
            return
        
        try:
            websocket = self.connections[connection_id]
            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.error(
                "Failed to send message",
                connection_id=connection_id,
                error=str(e)
            )
            # Queue message for later delivery
            if connection_id not in self.message_queue:
                self.message_queue[connection_id] = []
            self.message_queue[connection_id].append(message)
    
    async def broadcast_to_session(self, session_id: str, message: BaseMessage):
        """
        Broadcast a message to all connections in a session.
        
        Args:
            session_id: Target session identifier
            message: Message to broadcast
        """
        if session_id not in self.session_connections:
            logger.warning(f"[DEBUG] No session connections found for session_id: {session_id}")
            return
        
        connection_ids = list(self.session_connections[session_id])
        logger.info(f"[DEBUG] Broadcasting to session {session_id} with {len(connection_ids)} connections: {connection_ids}")
        
        for connection_id in connection_ids:
            logger.info(f"[DEBUG] Sending message to connection {connection_id}")
            await self.send_message(connection_id, message)
    
    async def broadcast_to_user(self, user_id: str, message: BaseMessage):
        """
        Broadcast a message to all connections of a user.
        
        Args:
            user_id: Target user identifier
            message: Message to broadcast
        """
        if user_id not in self.user_connections:
            return
        
        connection_ids = list(self.user_connections[user_id])
        for connection_id in connection_ids:
            await self.send_message(connection_id, message)
    
    async def handle_terminal_message(self, connection_id: str, message_data: Dict[str, Any]):
        """
        Handle terminal-related WebSocket messages.
        
        Args:
            connection_id: Source connection identifier
            message_data: Received message data
        """
        try:
            # Validate message
            message = validate_message(message_data)
            print(f"[DEBUG] Terminal WebSocket received message type: {message.type}")  # Debug all messages
            
            if message.type == MessageType.COMMAND:
                # Handle terminal command
                command_msg = CommandMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "Terminal command received",
                    connection_id=connection_id,
                    session_id=session_id,
                    command=command_msg.command[:100]  # Truncate for logging
                )
                
                # Execute command using terminal service
                result = await terminal_service.execute_command(
                    session_id=session_id,
                    command=command_msg.command,
                    timeout=30,
                    working_directory=command_msg.working_directory
                )
                
                # Check if this was a streaming command (empty stdout/stderr means it was already streamed)
                is_streaming_command = (result["stdout"] == "" and result["stderr"] == "")
                
                # Only send final response if it wasn't already streamed
                if not is_streaming_command:
                    # Create response message
                    response = CommandResponseMessage(
                        type=MessageType.COMMAND_RESPONSE,
                        command=command_msg.command,
                        stdout=result["stdout"],
                        stderr=result["stderr"],
                        return_code=result["return_code"],
                        execution_time=result.get("execution_time", 0.0),
                        working_directory=result.get("working_directory")
                    )
                    
                    logger.info(
                        "Sending command response",
                        connection_id=connection_id,
                        session_id=session_id,
                        command=command_msg.command,
                        working_directory=result.get("working_directory"),
                        has_working_directory=bool(result.get("working_directory"))
                    )
                    
                    await self.send_message(connection_id, response)
                else:
                    # This was a streaming command - send only a completion signal with no output
                    response = CommandResponseMessage(
                        type=MessageType.COMMAND_RESPONSE,
                        command=command_msg.command,
                        stdout="",
                        stderr="",
                        return_code=result["return_code"],
                        execution_time=result.get("execution_time", 0.0),
                        working_directory=result.get("working_directory")
                    )
                    
                    logger.info(
                        "Sending streaming command completion signal",
                        connection_id=connection_id,
                        session_id=session_id,
                        command=command_msg.command,
                        return_code=result["return_code"]
                    )
                    
                    await self.send_message(connection_id, response)
                
            elif message.type == MessageType.PING:
                # Handle ping
                pong_msg = PongMessage(type=MessageType.PONG)
                await self.send_message(connection_id, pong_msg)
                
            elif message.type == MessageType.INPUT_RESPONSE:
                # Handle input response from frontend
                input_msg = InputResponseMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "Input response received",
                    connection_id=connection_id,
                    session_id=session_id,
                    input_length=len(input_msg.input)
                )
                
                # Forward input to the waiting process
                if session_id:
                    logger.info(f"Forwarding input to session {session_id}: {input_msg.input}")
                    await terminal_service.handle_input_response(session_id, input_msg.input)
                else:
                    logger.warning(f"No session_id found for connection {connection_id}, cannot send input")
                
            elif message.type == MessageType.INTERRUPT:
                # Handle interrupt signal (Ctrl+C)
                interrupt_msg = InterruptMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "Interrupt signal received",
                    connection_id=connection_id,
                    session_id=session_id,
                    working_directory=interrupt_msg.working_directory
                )
                
                # Send interrupt signal to terminal service
                if session_id:
                    logger.info(f"Calling interrupt_session for session_id: {session_id}")
                    result = await terminal_service.interrupt_session(session_id)
                    logger.info(f"Interrupt result: {result}")
                else:
                    logger.warning(f"No session_id found for connection {connection_id}, cannot interrupt")
                    logger.warning(f"Available sessions: {list(self.connection_metadata.keys())}")
                    logger.warning(f"Connection metadata: {self.connection_metadata.get(connection_id, {})}")
                    
                    # Send response back to frontend
                    response = CommandResponseMessage(
                        type=MessageType.COMMAND_RESPONSE,
                        command="^C",
                        stdout="",
                        stderr="" if result["success"] else f"Failed to interrupt: {result.get('error', 'Unknown error')}",
                        return_code=130 if result["success"] else 1,  # 130 is standard for SIGINT
                        working_directory=interrupt_msg.working_directory
                    )
                    
                    await self.send_message(connection_id, response)
                
                # Input response is handled by the terminal service via the interrupt handling above
                # No additional forwarding needed here
                    
            elif message.type == MessageType.TERMINAL_RESIZE:
                # Handle terminal resize
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                logger.info(
                    "Terminal resize received",
                    connection_id=connection_id,
                    session_id=session_id,
                    cols=message_data.get("cols"),
                    rows=message_data.get("rows")
                )
                
                # TODO: Handle terminal resize in container if needed
                
            else:
                logger.warning(
                    "Unknown terminal message type",
                    connection_id=connection_id,
                    message_type=message.type
                )
                
        except Exception as e:
            logger.error("Error handling terminal message", error=str(e), connection_id=connection_id)
            error_msg = create_error_message("INVALID_MESSAGE", str(e))
            await self.send_message(connection_id, error_msg)
    
    async def handle_file_message(self, connection_id: str, message_data: Dict[str, Any]):
        """
        Handle file synchronization WebSocket messages.
        
        Args:
            connection_id: Source connection identifier
            message_data: Received message data
        """
        try:
            # Validate message
            message = validate_message(message_data)
            
            if message.type == MessageType.FILE_UPDATE:
                # Handle file update
                file_msg = FileUpdateMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "File update received",
                    connection_id=connection_id,
                    session_id=session_id,
                    filename=file_msg.filename,
                    content_length=len(file_msg.content),
                    language=file_msg.language
                )
                
                # Save file to database using workspace service
                if self.workspace_service:
                    try:
                        saved_file = await self.workspace_service.save_file(
                            session_id=session_id,
                            filepath=file_msg.filename,
                            content=file_msg.content,
                            language=file_msg.language or "python"
                        )
                        logger.info(
                            "File saved successfully",
                            connection_id=connection_id,
                            session_id=session_id,
                            filename=file_msg.filename,
                            file_id=saved_file.id if saved_file else None
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to save file",
                            connection_id=connection_id,
                            session_id=session_id,
                            filename=file_msg.filename,
                            error=str(e)
                        )
                else:
                    logger.error(
                        "Workspace service not available for file save",
                        connection_id=connection_id,
                        session_id=session_id,
                        filename=file_msg.filename
                    )
                
                # Broadcast to other connections in the session
                from app.schemas.websocket import FileUpdatedMessage
                broadcast_message = FileUpdatedMessage(
                    type=MessageType.FILE_UPDATED,
                    filename=file_msg.filename,
                    content=file_msg.content,
                    updated_by=connection_id,
                    language=file_msg.language
                )
                
                await self.broadcast_to_session(session_id, broadcast_message)
                logger.info(
                    "File update broadcast sent",
                    connection_id=connection_id,
                    session_id=session_id,
                    filename=file_msg.filename
                )
                
            elif message.type == MessageType.FILE_REQUEST:
                # Handle file request
                file_msg = FileRequestMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "File request received",
                    connection_id=connection_id,
                    session_id=session_id,
                    filename=file_msg.filename
                )
                
                # Get file content from database using workspace service
                content = ""
                if self.workspace_service:
                    content = await self.workspace_service.get_file_content(
                        session_id=session_id,
                        filepath=file_msg.filename
                    ) or ""
                
                # Send file content back to client
                
                from app.schemas.websocket import FileContentMessage
                response = FileContentMessage(
                    type=MessageType.FILE_CONTENT,
                    filename=file_msg.filename,
                    content=content,
                    language="python"  # TODO: Detect language from file extension
                )
                
                await self.send_message(connection_id, response)
                
            elif message.type == MessageType.FILE_LIST:
                # Handle file list request
                file_msg = FileListMessage(**message_data)
                connection_meta = self.connection_metadata.get(connection_id, {})
                session_id = connection_meta.get("session_id")
                user_id = connection_meta.get("user_id")
                
                logger.info(
                    "File list request received",
                    connection_id=connection_id,
                    session_id=session_id,
                    user_id=user_id,
                    directory=file_msg.directory,
                    connection_metadata=connection_meta
                )
                
                # SECURITY: Verify user has access to this session
                files = []
                if self.workspace_service and session_id and user_id:
                    try:
                        # First verify user owns this session
                        session = await self.workspace_service.get_user_workspace(
                            user_id=user_id,
                            session_id=session_id
                        )
                        
                        if session:
                            # User is authorized - get the files
                            files = await self.workspace_service.get_workspace_files(
                                session_id=session_id,
                                directory=file_msg.directory or "/"
                            )
                            logger.info(
                                "File list authorized and retrieved",
                                connection_id=connection_id,
                                session_id=session_id,
                                user_id=user_id,
                                file_count=len(files)
                            )
                        else:
                            logger.warning(
                                "Unauthorized file list access attempt",
                                connection_id=connection_id,
                                session_id=session_id,
                                user_id=user_id
                            )
                    except Exception as e:
                        logger.error(
                            "Failed to authorize file list access",
                            connection_id=connection_id,
                            session_id=session_id,
                            user_id=user_id,
                            error=str(e)
                        )
                else:
                    logger.warning(
                        "File list request missing required data",
                        connection_id=connection_id,
                        session_id=session_id,
                        user_id=user_id,
                        workspace_service_available=bool(self.workspace_service)
                    )
                
                from app.schemas.websocket import FileListResponseMessage
                response = FileListResponseMessage(
                    type=MessageType.FILE_LIST_RESPONSE,
                    files=files,
                    directory=file_msg.directory or "/"
                )
                
                await self.send_message(connection_id, response)
                
            elif message.type == MessageType.FILE_DELETE:
                # Handle file delete
                file_msg = FileDeleteMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "File delete request received",
                    connection_id=connection_id,
                    session_id=session_id,
                    filename=file_msg.filename
                )
                
                # Delete file from database using workspace service
                if self.workspace_service:
                    success = await self.workspace_service.delete_file(
                        session_id=session_id,
                        filepath=file_msg.filename
                    )
                    
                    if success:
                        # Broadcast delete notification to all connections in the session
                        from app.schemas.websocket import FileDeletedMessage
                        broadcast_message = FileDeletedMessage(
                            type=MessageType.FILE_DELETED,
                            filename=file_msg.filename,
                            deleted_by=connection_id
                        )
                        await self.broadcast_to_session(session_id, broadcast_message)
                
            elif message.type == MessageType.FILE_RENAME:
                # Handle file rename
                file_msg = FileRenameMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "File rename request received",
                    connection_id=connection_id,
                    session_id=session_id,
                    old_filename=file_msg.old_filename,
                    new_filename=file_msg.new_filename
                )
                
                # Rename file in database using workspace service
                if self.workspace_service:
                    success = await self.workspace_service.rename_file(
                        session_id=session_id,
                        old_filepath=file_msg.old_filename,
                        new_filepath=file_msg.new_filename
                    )
                    
                    if success:
                        # Broadcast rename notification to all connections in the session
                        from app.schemas.websocket import FileRenamedMessage
                        broadcast_message = FileRenamedMessage(
                            type=MessageType.FILE_RENAMED,
                            old_filename=file_msg.old_filename,
                            new_filename=file_msg.new_filename,
                            renamed_by=connection_id
                        )
                        await self.broadcast_to_session(session_id, broadcast_message)
                
            elif message.type == MessageType.FOLDER_CREATE:
                # Handle folder creation
                folder_msg = FolderCreateMessage(**message_data)
                session_id = self.connection_metadata.get(connection_id, {}).get("session_id")
                
                logger.info(
                    "Folder create request received",
                    connection_id=connection_id,
                    session_id=session_id,
                    folder_name=folder_msg.foldername,
                    parent_path=folder_msg.parent_path
                )
                
                # Create folder using workspace service
                if self.workspace_service:
                    try:
                        folder_path = await self.workspace_service.create_folder(
                            session_id=session_id,
                            folder_name=folder_msg.foldername,
                            parent_path=folder_msg.parent_path or "/"
                        )
                        
                        # Broadcast folder creation notification to all connections in the session
                        from app.schemas.websocket import FolderCreatedMessage
                        broadcast_message = FolderCreatedMessage(
                            type=MessageType.FOLDER_CREATED,
                            foldername=folder_msg.foldername,
                            folderpath=folder_path,
                            parent_path=folder_msg.parent_path or "/"
                        )
                        await self.broadcast_to_session(session_id, broadcast_message)
                        
                    except Exception as e:
                        logger.error("Failed to create folder", error=str(e), session_id=session_id, folder_name=folder_msg.foldername)
                        error_msg = create_error_message("FOLDER_CREATE_FAILED", f"Failed to create folder: {str(e)}")
                        await self.send_message(connection_id, error_msg)
                
            elif message.type == MessageType.PING:
                # Handle ping
                pong = create_pong_message()
                await self.send_message(connection_id, pong)
                
            else:
                logger.warning("Unknown file message type", message_type=message.type)
                
        except Exception as e:
            logger.error("Error handling file message", error=str(e), connection_id=connection_id)
            error_msg = create_error_message("INVALID_MESSAGE", str(e))
            await self.send_message(connection_id, error_msg)
    
    async def flush_message_queue(self, connection_id: str):
        """
        Flush queued messages for a connection.
        
        Args:
            connection_id: Connection identifier
        """
        if connection_id not in self.message_queue:
            return
        
        messages = self.message_queue[connection_id]
        if not messages:
            return
        
        # Send all queued messages
        for message in messages:
            await self.send_message(connection_id, message)
        
        # Clear queue
        self.message_queue[connection_id] = []
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connections)
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of connections for a session."""
        return len(self.session_connections.get(session_id, set()))
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a user."""
        return len(self.user_connections.get(user_id, set()))
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information."""
        return self.connection_metadata.get(connection_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager() 