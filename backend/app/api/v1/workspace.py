"""
AfterIDE - Workspace API

API endpoints for workspace management and file operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.services.workspace import WorkspaceService
from app.schemas.workspace import (
    SessionCreate, SessionResponse, FileListResponse, FileContentResponse,
    FileCreate, FileUpdate
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workspace session for a user.
    
    Args:
        session_data: Session creation data
        db: Database session
        
    Returns:
        SessionResponse: Created session information
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # For now, use a default user ID (in production, get from authentication)
        user_id = session_data.user_id or "default-user"
        
        session = await workspace_service.create_user_workspace(
            user_id=user_id,
            session_name=session_data.name
        )
        
        return SessionResponse(
            id=str(session.id),
            name=session.name,
            description=session.description,
            status=session.status,
            created_at=session.created_at,
            expires_at=session.expires_at
        )
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a workspace session.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        db: Database session
        
    Returns:
        SessionResponse: Session information
    """
    try:
        workspace_service = WorkspaceService(db)
        
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return SessionResponse(
            id=str(session.id),
            name=session.name,
            description=session.description,
            status=session.status,
            created_at=session.created_at,
            expires_at=session.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.get("/sessions/{session_id}/files", response_model=FileListResponse)
async def get_workspace_files(
    session_id: str,
    user_id: str,
    directory: str = "/",
    db: AsyncSession = Depends(get_db)
):
    """
    Get files in a workspace directory.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        directory: Directory path (default: "/")
        db: Database session
        
    Returns:
        FileListResponse: List of files in the directory
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        files = await workspace_service.get_workspace_files(
            session_id=session_id,
            directory=directory
        )
        
        return FileListResponse(
            session_id=session_id,
            directory=directory,
            files=files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workspace files", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workspace files"
        )


@router.get("/sessions/{session_id}/files/{filepath:path}", response_model=FileContentResponse)
async def get_file_content(
    session_id: str,
    filepath: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get content of a file in the workspace.
    
    Args:
        session_id: Session identifier
        filepath: File path
        user_id: User identifier
        db: Database session
        
    Returns:
        FileContentResponse: File content and metadata
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        content = await workspace_service.get_file_content(
            session_id=session_id,
            filepath=f"/{filepath}"
        )
        
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileContentResponse(
            session_id=session_id,
            filepath=f"/{filepath}",
            content=content,
            language="python"  # TODO: Detect language from file extension
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file content", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file content"
        )


@router.post("/sessions/{session_id}/files", response_model=FileContentResponse)
async def create_file(
    session_id: str,
    file_data: FileCreate,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new file in the workspace.
    
    Args:
        session_id: Session identifier
        file_data: File creation data
        user_id: User identifier
        db: Database session
        
    Returns:
        FileContentResponse: Created file information
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        file = await workspace_service.save_file(
            session_id=session_id,
            filepath=file_data.filepath,
            content=file_data.content,
            language=file_data.language or "python"
        )
        
        return FileContentResponse(
            session_id=session_id,
            filepath=file.filepath,
            content=file.content,
            language=file.language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create file"
        )


@router.put("/sessions/{session_id}/files/{filepath:path}", response_model=FileContentResponse)
async def update_file(
    session_id: str,
    filepath: str,
    file_data: FileUpdate,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a file in the workspace.
    
    Args:
        session_id: Session identifier
        filepath: File path
        file_data: File update data
        user_id: User identifier
        db: Database session
        
    Returns:
        FileContentResponse: Updated file information
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        file = await workspace_service.save_file(
            session_id=session_id,
            filepath=f"/{filepath}",
            content=file_data.content,
            language=file_data.language or "python"
        )
        
        return FileContentResponse(
            session_id=session_id,
            filepath=file.filepath,
            content=file.content,
            language=file.language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file"
        )


@router.delete("/sessions/{session_id}/files/{filepath:path}")
async def delete_file(
    session_id: str,
    filepath: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file from the workspace.
    
    Args:
        session_id: Session identifier
        filepath: File path
        user_id: User identifier
        db: Database session
        
    Returns:
        dict: Success message
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        success = await workspace_service.delete_file(
            session_id=session_id,
            filepath=f"/{filepath}"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Terminate a workspace session.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        db: Database session
        
    Returns:
        dict: Success message
    """
    try:
        workspace_service = WorkspaceService(db)
        
        # Verify user has access to this session
        session = await workspace_service.get_user_workspace(
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        success = await workspace_service.terminate_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to terminate session"
            )
        
        return {"message": "Session terminated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to terminate session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate session"
        ) 