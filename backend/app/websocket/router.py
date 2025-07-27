"""
AfterIDE - WebSocket Router

WebSocket endpoints for real-time terminal communication and file synchronization.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Set
import structlog
import json
import uuid

from app.core.config import settings
from app.services.websocket import WebSocketManager
from app.services.auth import AuthService
from app.services.session import SessionService
from app.schemas.websocket import (
    ConnectionMessage, create_error_message, MessageType
)

router = APIRouter()
logger = structlog.get_logger(__name__)

# WebSocket connection manager
websocket_manager = WebSocketManager()


@router.websocket("/ws/terminal/{session_id}")
async def websocket_terminal(
    websocket: WebSocket,
    session_id: str,
    token: str = None
):
    """
    WebSocket endpoint for terminal communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        token: Authentication token (optional for development)
    """
    connection_id = None
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # For development, allow connections without authentication
        user_id = None
        if token:
            # TODO: Implement proper token validation
            user_id = "dev-user"
        
        # Register connection
        connection_id = str(uuid.uuid4())
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            connection_type="terminal"
        )
        
        logger.info(
            "WebSocket terminal connected",
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id
        )
        
        # Send welcome message
        welcome_message = ConnectionMessage(
            type=MessageType.CONNECTION_ESTABLISHED,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            message="Terminal connection established"
        )
        await websocket_manager.send_message(connection_id, welcome_message)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message
                await websocket_manager.handle_terminal_message(
                    connection_id=connection_id,
                    message_data=message
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received", connection_id=connection_id)
                error_msg = create_error_message("INVALID_JSON", "Invalid JSON format")
                await websocket_manager.send_message(connection_id, error_msg)
            except Exception as e:
                logger.error("WebSocket error", error=str(e), connection_id=connection_id)
                error_msg = create_error_message("INTERNAL_ERROR", "Internal server error")
                await websocket_manager.send_message(connection_id, error_msg)
                
    except WebSocketDisconnect:
        logger.info("WebSocket terminal disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket terminal error", error=str(e), session_id=session_id)
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.websocket("/ws/files/{session_id}")
async def websocket_files(
    websocket: WebSocket,
    session_id: str,
    token: str = None
):
    """
    WebSocket endpoint for file synchronization.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        token: Authentication token (optional for development)
    """
    connection_id = None
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # For development, allow connections without authentication
        user_id = None
        if token:
            # TODO: Implement proper token validation
            user_id = "dev-user"
        
        # Register connection
        connection_id = str(uuid.uuid4())
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            connection_type="files"
        )
        
        logger.info(
            "WebSocket files connected",
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id
        )
        
        # Send welcome message
        welcome_message = ConnectionMessage(
            type=MessageType.CONNECTION_ESTABLISHED,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            message="File synchronization connection established"
        )
        await websocket_manager.send_message(connection_id, welcome_message)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message
                await websocket_manager.handle_file_message(
                    connection_id=connection_id,
                    message_data=message
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received", connection_id=connection_id)
                error_msg = create_error_message("INVALID_JSON", "Invalid JSON format")
                await websocket_manager.send_message(connection_id, error_msg)
            except Exception as e:
                logger.error("WebSocket error", error=str(e), connection_id=connection_id)
                error_msg = create_error_message("INTERNAL_ERROR", "Internal server error")
                await websocket_manager.send_message(connection_id, error_msg)
                
    except WebSocketDisconnect:
        logger.info("WebSocket files disconnected", session_id=session_id)
    except Exception as e:
        logger.error("WebSocket files error", error=str(e), session_id=session_id)
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)

# Export the router
websocket_router = router 