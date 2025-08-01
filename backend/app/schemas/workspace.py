"""
AfterIDE - Workspace Schemas

Pydantic schemas for workspace management and file operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    name: str = Field(..., description="Session name")
    user_id: Optional[str] = Field(None, description="User identifier")


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: str = Field(..., description="Session identifier")
    name: str = Field(..., description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    status: str = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")


class FileInfo(BaseModel):
    """Schema for file information."""
    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    type: str = Field(..., description="File type (file or directory)")
    size: int = Field(..., description="File size in bytes")
    language: Optional[str] = Field(None, description="Programming language")
    modified: str = Field(..., description="Last modified timestamp")


class FileListResponse(BaseModel):
    """Schema for file list response."""
    session_id: str = Field(..., description="Session identifier")
    directory: str = Field(..., description="Directory path")
    files: List[FileInfo] = Field(..., description="List of files")


class FileContentResponse(BaseModel):
    """Schema for file content response."""
    session_id: str = Field(..., description="Session identifier")
    filepath: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language")


class FileCreate(BaseModel):
    """Schema for creating a new file."""
    filepath: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    language: Optional[str] = Field("python", description="Programming language")


class FileUpdate(BaseModel):
    """Schema for updating a file."""
    content: str = Field(..., description="File content")
    language: Optional[str] = Field(None, description="Programming language") 