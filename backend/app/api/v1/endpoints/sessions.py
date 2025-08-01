"""
AfterIDE - Sessions API Endpoints

REST API endpoints for managing user development sessions.
"""

import json
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import Session, SessionStatus
from app.services.session import SessionService
from app.api.v1.endpoints.auth import get_current_user_dependency
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
async def create_session(
    name: str,
    description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new development session.
    
    Args:
        name: Session name
        description: Optional session description
        config: Optional session configuration
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created session information
    """
    session_service = SessionService(db)
    session = await session_service.create_session(
        user_id=str(current_user["id"]),
        name=name,
        description=description,
        config=config
    )
    
    return {
        "id": str(session.id),
        "name": session.name,
        "description": session.description,
        "status": session.status,
        "config": json.loads(session.config) if isinstance(session.config, str) else session.config,
        "expires_at": session.expires_at.isoformat(),
        "max_memory_mb": session.max_memory_mb,
        "max_cpu_cores": session.max_cpu_cores,
        "max_execution_time": session.max_execution_time
    }

@router.get("/", response_model=List[Dict[str, Any]])
async def list_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    List all sessions for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user's sessions
    """
    session_service = SessionService(db)
    sessions = await session_service.get_user_sessions(str(current_user["id"]))
    
    return [
        {
            "id": str(session.id),
            "name": session.name,
            "description": session.description,
            "status": session.status,
            "config": json.loads(session.config) if isinstance(session.config, str) else session.config,
            "expires_at": session.expires_at.isoformat(),
            "max_memory_mb": session.max_memory_mb,
            "max_cpu_cores": session.max_cpu_cores,
            "max_execution_time": session.max_execution_time,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        for session in sessions
    ]

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session information
        
    Raises:
        HTTPException: If session not found or access denied
    """
    session_service = SessionService(db)
    session = await session_service.get_session(session_id, str(current_user["id"]))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "id": str(session.id),
        "name": session.name,
        "description": session.description,
        "status": session.status,
        "config": json.loads(session.config) if isinstance(session.config, str) else session.config,
        "expires_at": session.expires_at.isoformat(),
        "max_memory_mb": session.max_memory_mb,
        "max_cpu_cores": session.max_cpu_cores,
        "max_execution_time": session.max_execution_time,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }

@router.put("/{session_id}", response_model=Dict[str, Any])
async def update_session(
    session_id: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a session.
    
    Args:
        session_id: Session ID
        updates: Session updates
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated session information
        
    Raises:
        HTTPException: If session not found or access denied
    """
    session_service = SessionService(db)
    session = await session_service.update_session(
        session_id, 
        str(current_user["id"]), 
        updates
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "id": str(session.id),
        "name": session.name,
        "description": session.description,
        "status": session.status,
        "config": json.loads(session.config) if isinstance(session.config, str) else session.config,
        "expires_at": session.expires_at.isoformat(),
        "max_memory_mb": session.max_memory_mb,
        "max_cpu_cores": session.max_cpu_cores,
        "max_execution_time": session.max_execution_time,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If session not found or access denied
    """
    session_service = SessionService(db)
    success = await session_service.delete_session(session_id, str(current_user["id"]))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session deleted successfully"}

@router.post("/{session_id}/start")
async def start_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
        
    Raises:
        HTTPException: If session not found or cannot be started
    """
    session_service = SessionService(db)
    session = await session_service.start_session(session_id, str(current_user["id"]))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be started"
        )
    
    return {
        "id": str(session.id),
        "status": session.status,
        "message": "Session started successfully"
    }

@router.post("/{session_id}/pause")
async def pause_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Pause a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
        
    Raises:
        HTTPException: If session not found or cannot be paused
    """
    session_service = SessionService(db)
    session = await session_service.pause_session(session_id, str(current_user["id"]))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be paused"
        )
    
    return {
        "id": str(session.id),
        "status": session.status,
        "message": "Session paused successfully"
    }

@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
        
    Raises:
        HTTPException: If session not found or cannot be resumed
    """
    session_service = SessionService(db)
    session = await session_service.resume_session(session_id, str(current_user["id"]))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be resumed"
        )
    
    return {
        "id": str(session.id),
        "status": session.status,
        "message": "Session resumed successfully"
    }

@router.post("/{session_id}/stop")
async def stop_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Stop a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
        
    Raises:
        HTTPException: If session not found or cannot be stopped
    """
    session_service = SessionService(db)
    session = await session_service.stop_session(session_id, str(current_user["id"]))
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be stopped"
        )
    
    return {
        "id": str(session.id),
        "status": session.status,
        "message": "Session stopped successfully"
    }

@router.get("/status")
async def sessions_status():
    """Get sessions service status."""
    return {
        "message": "Sessions service is running",
        "status": "active"
    }