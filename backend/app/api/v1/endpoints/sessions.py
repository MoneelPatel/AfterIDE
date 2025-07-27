"""
AfterIDE - Sessions API Endpoints

REST API endpoints for managing user development sessions.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models.session import Session, SessionStatus
from app.services.session import SessionService
from app.api.v1.endpoints.auth import get_current_user_dependency

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def create_session(
    name: str,
    description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Create a new development session.
    
    Args:
        name: Session name
        description: Optional session description
        config: Optional session configuration
        current_user: Current authenticated user
        
    Returns:
        Created session information
    """
    session = await SessionService.create_session(
        user_id=str(current_user["id"]),
        name=name,
        description=description,
        config=config
    )
    
    return {
        "id": str(session["id"]),
        "name": session["name"],
        "description": session["description"],
        "status": session["status"],
        "config": session["config"],
        "expires_at": session["expires_at"].isoformat(),
        "max_memory_mb": session["max_memory_mb"],
        "max_cpu_cores": session["max_cpu_cores"],
        "max_execution_time": session["max_execution_time"]
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Get all sessions for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of user's sessions
    """
    sessions = await SessionService.get_user_sessions(str(current_user["id"]))
    
    return [
        {
            "id": str(session["id"]),
            "name": session["name"],
            "description": session["description"],
            "status": session["status"],
            "config": session["config"],
            "expires_at": session["expires_at"].isoformat(),
            "max_memory_mb": session["max_memory_mb"],
            "max_cpu_cores": session["max_cpu_cores"],
            "max_execution_time": session["max_execution_time"],
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat()
        }
        for session in sessions
    ]


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session identifier
        current_user: Current authenticated user
        
    Returns:
        Session information
        
    Raises:
        HTTPException: If session not found
    """
    session = await SessionService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # TODO: Check if user has access to this session
    
    return {
        "id": str(session["id"]),
        "name": session["name"],
        "description": session["description"],
        "status": session["status"],
        "config": session["config"],
        "expires_at": session["expires_at"].isoformat(),
        "max_memory_mb": session["max_memory_mb"],
        "max_cpu_cores": session["max_cpu_cores"],
        "max_execution_time": session["max_execution_time"],
        "created_at": session["created_at"].isoformat(),
        "updated_at": session["updated_at"].isoformat(),
        "last_activity": session["last_activity"].isoformat()
    }


@router.put("/{session_id}", response_model=Dict[str, Any])
async def update_session(
    session_id: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Update session properties.
    
    Args:
        session_id: Session identifier
        updates: Dictionary of updates to apply
        current_user: Current authenticated user
        
    Returns:
        Updated session information
        
    Raises:
        HTTPException: If session not found
    """
    session = await SessionService.update_session(session_id, updates)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "id": str(session["id"]),
        "name": session["name"],
        "description": session["description"],
        "status": session["status"],
        "config": session["config"],
        "expires_at": session["expires_at"].isoformat(),
        "max_memory_mb": session["max_memory_mb"],
        "max_cpu_cores": session["max_cpu_cores"],
        "max_execution_time": session["max_execution_time"],
        "updated_at": session["updated_at"].isoformat()
    }


@router.delete("/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Terminate a session.
    
    Args:
        session_id: Session identifier
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If session not found
    """
    success = await SessionService.terminate_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session terminated successfully"}


@router.post("/{session_id}/extend")
async def extend_session(
    session_id: str,
    hours: int = 1,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Extend session expiration time.
    
    Args:
        session_id: Session identifier
        hours: Number of hours to extend
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If session not found
    """
    success = await SessionService.extend_session(session_id, hours)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": f"Session extended by {hours} hours"}


@router.get("/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency)
):
    """
    Get session status and health information.
    
    Args:
        session_id: Session identifier
        current_user: Current authenticated user
        
    Returns:
        Session status information
    """
    session = await SessionService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if session is expired
    is_expired = datetime.utcnow() > session["expires_at"]
    is_active = session["status"] == SessionStatus.ACTIVE and not is_expired
    
    return {
        "id": str(session["id"]),
        "status": session["status"],
        "is_active": is_active,
        "is_expired": is_expired,
        "expires_at": session["expires_at"].isoformat(),
        "last_activity": session["last_activity"].isoformat(),
        "container_id": session.get("container_id")
    } 