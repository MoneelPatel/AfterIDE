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
            "updated_at": session.updated_at.isoformat(),
            "last_activity": session.last_activity.isoformat()
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
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session information
    """
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if user owns this session
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Ensure all attributes are loaded to avoid lazy loading issues in tests
    await db.refresh(session)
    
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
        "updated_at": session.updated_at.isoformat(),
        "last_activity": session.last_activity.isoformat()
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
        session_id: Session identifier
        updates: Session updates
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated session information
    """
    session_service = SessionService(db)
    
    # First check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update session
    updated_session = await session_service.update_session(session_id, updates)
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )
    
    return {
        "id": str(updated_session.id),
        "name": updated_session.name,
        "description": updated_session.description,
        "status": updated_session.status,
        "config": json.loads(updated_session.config) if isinstance(updated_session.config, str) else updated_session.config,
        "expires_at": updated_session.expires_at.isoformat(),
        "max_memory_mb": updated_session.max_memory_mb,
        "max_cpu_cores": updated_session.max_cpu_cores,
        "max_execution_time": updated_session.max_execution_time,
        "created_at": updated_session.created_at.isoformat(),
        "updated_at": updated_session.updated_at.isoformat(),
        "last_activity": updated_session.last_activity.isoformat()
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
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    session_service = SessionService(db)
    
    # First check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete session
    success = await session_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
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
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
    """
    session_service = SessionService(db)
    
    # Check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update session status to active
    updated_session = await session_service.update_session(
        session_id, 
        {"status": SessionStatus.ACTIVE.value}
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start session"
        )
    
    return {
        "id": str(updated_session.id),
        "status": updated_session.status,
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
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
    """
    session_service = SessionService(db)
    
    # Check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update session status to paused (using a custom status)
    updated_session = await session_service.update_session(
        session_id, 
        {"status": "paused"}
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause session"
        )
    
    return {
        "id": str(updated_session.id),
        "status": updated_session.status,
        "message": "Session paused successfully"
    }


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a paused session.
    
    Args:
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
    """
    session_service = SessionService(db)
    
    # Check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update session status to active
    updated_session = await session_service.update_session(
        session_id, 
        {"status": SessionStatus.ACTIVE.value}
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume session"
        )
    
    return {
        "id": str(updated_session.id),
        "status": updated_session.status,
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
        session_id: Session identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session status
    """
    session_service = SessionService(db)
    
    # Check if session exists and user has access
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if str(session.user_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Terminate session
    success = await session_service.terminate_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop session"
        )
    
    return {
        "id": session_id,
        "status": SessionStatus.TERMINATED.value,
        "message": "Session stopped successfully"
    } 