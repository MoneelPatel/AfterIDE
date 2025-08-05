"""
AfterIDE - WebSocket Router

WebSocket endpoints for real-time terminal communication and file synchronization.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from typing import Dict, Set, Optional
import structlog
import json
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.services.websocket import WebSocketManager
from app.services.workspace import WorkspaceService
from app.services.auth import AuthService
from app.services.session import SessionService
from app.schemas.websocket import (
    ConnectionMessage, create_error_message, MessageType
)

router = APIRouter()
logger = structlog.get_logger(__name__)

# WebSocket connection manager
websocket_manager = WebSocketManager()

# Dependency to get workspace service with database session
async def get_workspace_service():
    """Get workspace service with database session."""
    async for db in get_db():
        workspace_service = WorkspaceService(db)
        # Set the workspace service for the WebSocket manager
        websocket_manager.set_workspace_service(workspace_service)
        # Set the WebSocket manager for the terminal service
        from app.services.terminal import terminal_service
        terminal_service.set_websocket_manager(websocket_manager)
        return workspace_service


async def get_user_session_id(user: any, session_service: SessionService) -> str:
    """
    Get or create a session ID for the user.
    
    Args:
        user: User object
        session_service: Session service instance
        
    Returns:
        Session ID string
    """
    # Get user's sessions
    user_sessions = await session_service.get_user_sessions(str(user.id))
    
    if user_sessions:
        # Use the first active session
        user_session = next((s for s in user_sessions if s.is_active), user_sessions[0])
        return str(user_session.id)
    else:
        # Create a new session for the user
        user_session = await session_service.create_session(
            user_id=str(user.id),
            name="Development Session",
            description="User development workspace"
        )
        return str(user_session.id)


@router.websocket("/ws/terminal/{session_id}")
async def websocket_terminal(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """
    WebSocket endpoint for terminal communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier (from frontend)
        token: Authentication token from query parameter
        workspace_service: Workspace service instance
    """
    connection_id = None
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        user = None
        actual_session_id = session_id
        
        if token:
            # Validate token and get user
            async for db in get_db():
                user = await AuthService.get_current_user(db, token)
                if user:
                    # Get or create user's actual session
                    session_service = SessionService(db)
                    actual_session_id = await get_user_session_id(user, session_service)
                    break
        else:
            # For development, allow connections without authentication
            logger.warning("No authentication token provided, using default session")
        
        # Register connection
        connection_id = str(uuid.uuid4())
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=actual_session_id,
            user_id=str(user.id) if user else None,
            connection_type="terminal"
        )
        
        logger.info(
            "WebSocket terminal connected",
            connection_id=connection_id,
            frontend_session_id=session_id,
            actual_session_id=actual_session_id,
            user_id=str(user.id) if user else None
        )
        
        # Send welcome message
        welcome_message = ConnectionMessage(
            type=MessageType.CONNECTION_ESTABLISHED,
            connection_id=connection_id,
            session_id=actual_session_id,
            user_id=str(user.id) if user else None,
            message="Terminal connection established"
        )
        await websocket_manager.send_message(connection_id, welcome_message)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                print(f"[WEBSOCKET ROUTER] Waiting for message on connection {connection_id}")
                data = await websocket.receive_text()
                print(f"[WEBSOCKET ROUTER] Received raw data: {data}")
                message = json.loads(data)
                print(f"[WEBSOCKET ROUTER] Parsed message: {message}")
                
                # Process message
                print(f"[WEBSOCKET ROUTER] Calling handle_terminal_message for connection {connection_id}")
                await websocket_manager.handle_terminal_message(
                    connection_id=connection_id,
                    message_data=message
                )
                print(f"[WEBSOCKET ROUTER] Message processed successfully for connection {connection_id}")
                print(f"[WEBSOCKET ROUTER] About to wait for next message on connection {connection_id}")
                
            except WebSocketDisconnect:
                print(f"[WEBSOCKET ROUTER] WebSocket disconnected for connection {connection_id}")
                break
            except json.JSONDecodeError as e:
                print(f"[WEBSOCKET ROUTER] JSON decode error: {e}")
                logger.warning("Invalid JSON received", connection_id=connection_id, error=str(e))
                error_msg = create_error_message("INVALID_JSON", "Invalid JSON format")
                await websocket_manager.send_message(connection_id, error_msg)
            except Exception as e:
                print(f"[WEBSOCKET ROUTER] Unexpected error: {e}")
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
    token: Optional[str] = Query(None),
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """
    WebSocket endpoint for file synchronization.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier (from frontend)
        token: Authentication token from query parameter
        workspace_service: Workspace service instance
    """
    connection_id = None
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        user = None
        actual_session_id = session_id
        
        if token:
            # Validate token and get user
            async for db in get_db():
                user = await AuthService.get_current_user(db, token)
                if user:
                    # Get or create user's actual session
                    session_service = SessionService(db)
                    actual_session_id = await get_user_session_id(user, session_service)
                    break
        else:
            # For development, allow connections without authentication
            logger.warning("No authentication token provided, using default session")
        
        # Register connection
        connection_id = str(uuid.uuid4())
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=actual_session_id,
            user_id=str(user.id) if user else None,
            connection_type="files"
        )
        
        logger.info(
            "WebSocket files connected",
            connection_id=connection_id,
            frontend_session_id=session_id,
            actual_session_id=actual_session_id,
            user_id=str(user.id) if user else None
        )
        
        # Send welcome message
        welcome_message = ConnectionMessage(
            type=MessageType.CONNECTION_ESTABLISHED,
            connection_id=connection_id,
            session_id=actual_session_id,
            user_id=str(user.id) if user else None,
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
            except json.JSONDecodeError as e:
                print(f"[WEBSOCKET ROUTER] JSON decode error: {e}")
                logger.warning("Invalid JSON received", connection_id=connection_id, error=str(e))
                error_msg = create_error_message("INVALID_JSON", "Invalid JSON format")
                await websocket_manager.send_message(connection_id, error_msg)
            except Exception as e:
                print(f"[WEBSOCKET ROUTER] Unexpected error: {e}")
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