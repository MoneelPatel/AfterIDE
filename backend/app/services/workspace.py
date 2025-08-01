"""
AfterIDE - Workspace Service

Manages user-specific workspaces with database-backed file storage and isolation.
"""

import json
import os
import tempfile
import shutil
import structlog
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timedelta

from app.models.session import Session, SessionStatus
from app.models.file import File
from app.models.user import User
from app.core.config import settings

logger = structlog.get_logger(__name__)


class WorkspaceService:
    """Manages user workspaces with database-backed file storage."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.temp_workspaces: Dict[str, str] = {}  # session_id -> temp_dir
    
    async def create_user_workspace(self, user_id: str, session_name: str = "Default Session") -> Session:
        """
        Create a new workspace session for a user.
        
        Args:
            user_id: User identifier
            session_name: Name for the session
            
        Returns:
            Session: Created session
        """
        # Check if user has too many active sessions
        active_sessions = await self._get_active_sessions(user_id)
        if len(active_sessions) >= settings.MAX_SESSIONS_PER_USER:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            await self.terminate_session(oldest_session.id)
        
        # Create new session
        session = Session(
            user_id=user_id,
            name=session_name,
            description=f"Workspace session for user {user_id}",
            status=SessionStatus.ACTIVE.value,
            config=json.dumps({
                "python_packages": ["requests", "numpy", "pandas"],
                "environment_vars": {"PYTHONPATH": "/workspace"}
            }),  # Serialize as JSON string for SQLite
            expires_at=datetime.utcnow() + timedelta(hours=settings.SESSION_TIMEOUT // 3600),
            last_activity=datetime.utcnow()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Create default files for the workspace
        await self._create_default_files(session.id)
        
        logger.info(
            "User workspace created",
            user_id=user_id,
            session_id=str(session.id),
            session_name=session_name
        )
        
        return session
    
    async def get_user_workspace(self, user_id: str, session_id: str) -> Optional[Session]:
        """
        Get a user's workspace session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session: Session if found and accessible
        """
        stmt = select(Session).where(
            and_(
                Session.id == session_id,
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE.value
            )
        ).options(selectinload(Session.files))
        
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            await self.db.commit()
        
        return session
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List[Session]: Active sessions
        """
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE.value
            )
        ).order_by(Session.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session and clean up resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was terminated
        """
        stmt = select(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        # Mark session as terminated
        session.status = SessionStatus.TERMINATED.value
        session.updated_at = datetime.utcnow()
        
        # Clean up temporary workspace
        await self._cleanup_temp_workspace(session_id)
        
        await self.db.commit()
        
        logger.info("Session terminated", session_id=str(session_id))
        return True
    
    async def get_workspace_files(self, session_id: str, directory: str = "/") -> List[Dict[str, Any]]:
        """
        Get files in a workspace directory.
        
        Args:
            session_id: Session identifier
            directory: Directory path (relative to workspace root)
            
        Returns:
            List[Dict]: File information
        """
        # Normalize directory path
        if directory == "/" or directory == "":
            directory = "/"
        else:
            directory = directory.rstrip("/")
        
        # Get files in the specified directory
        if directory == "/":
            # For root directory, get files that are directly in root (have leading slash but no other slashes)
            stmt = select(File).where(
                and_(
                    File.session_id == session_id,
                    File.filepath.like("/%"),
                    File.filepath.notlike("/%/%")
                )
            ).order_by(File.filename)
        else:
            # For subdirectories, get files in the specified directory
            stmt = select(File).where(
                and_(
                    File.session_id == session_id,
                    File.filepath.like(f"{directory}/%")
                )
            ).order_by(File.filename)
        
        result = await self.db.execute(stmt)
        files = result.scalars().all()
        
        # Convert to file list format, filtering out hidden files
        file_list = []
        for file in files:
            # Skip hidden files (starting with .) 
            if file.filename.startswith('.'):
                continue
                
            file_list.append({
                "name": file.filename,
                "path": file.filepath,
                "type": "file",
                "size": file.size_bytes,
                "language": file.language,
                "modified": file.updated_at.isoformat()
            })
        
        # Add directories (detect from files with subdirectories)
        if directory == "/":
            # Get unique top-level directories by looking at all files with subdirectories
            stmt = select(File.filepath).where(
                and_(
                    File.session_id == session_id,
                    File.filepath.like("/%/%")
                )
            )
            result = await self.db.execute(stmt)
            paths = result.scalars().all()
            
            directories = set()
            for path in paths:
                # Extract directory name from path like "/folder-name/.placeholder" -> "folder-name"
                parts = path.split("/")
                if len(parts) >= 3:  # At least /folder/file format
                    dir_name = parts[1]  # First part after leading slash
                    if dir_name:  # Make sure it's not empty
                        directories.add(dir_name)
            
            # Add directory entries, sorted alphabetically
            for dir_name in sorted(directories):
                file_list.append({
                    "name": dir_name,
                    "path": f"/{dir_name}",
                    "type": "directory",
                    "size": 0,
                    "language": None,
                    "modified": datetime.utcnow().isoformat()
                })
        
        return file_list
    
    async def get_file_content(self, session_id: str, filepath: str) -> Optional[str]:
        """
        Get content of a file in the workspace.
        
        Args:
            session_id: Session identifier
            filepath: File path relative to workspace root
            
        Returns:
            str: File content if found
        """
        stmt = select(File).where(
            and_(
                File.session_id == session_id,
                File.filepath == filepath
            )
        )
        
        result = await self.db.execute(stmt)
        file = result.scalar_one_or_none()
        
        return file.content if file else None
    
    async def save_file(self, session_id: str, filepath: str, content: str, language: str = "python") -> File:
        """
        Save or update a file in the workspace.
        
        Args:
            session_id: Session identifier (can be string for development)
            filepath: File path relative to workspace root
            content: File content
            language: Programming language
            
        Returns:
            File: Saved file object
        """
        # For development, handle string session IDs
        # Check if session exists, if not create a default one
        session_stmt = select(Session).where(Session.id == session_id)
        result = await self.db.execute(session_stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            # Create a default session for development
            session = Session(
                id=session_id,  # Use the string ID directly
                user_id="default-user",  # Default user for development
                name="Default Session",
                description="Default development session",
                status=SessionStatus.ACTIVE.value,
                config=json.dumps({}),  # Serialize as JSON string for SQLite
                expires_at=datetime.utcnow() + timedelta(hours=24),
                last_activity=datetime.utcnow()
            )
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            # Check if any files already exist for this session before creating defaults
            existing_files_stmt = select(File).where(File.session_id == session_id)
            existing_result = await self.db.execute(existing_files_stmt)
            existing_files = existing_result.scalars().all()
            
            # Only create default files if no files exist for this session
            if not existing_files:
                await self._create_default_files(session_id)
        
        # Check if file exists
        stmt = select(File).where(
            and_(
                File.session_id == session_id,
                File.filepath == filepath
            )
        )
        
        result = await self.db.execute(stmt)
        file = result.scalar_one_or_none()
        
        if file:
            # Update existing file
            file.update_content(content)
            file.language = language
        else:
            # Create new file
            filename = os.path.basename(filepath)
            import hashlib
            checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
            size_bytes = len(content.encode('utf-8'))
            
            file = File(
                session_id=session_id,
                filename=filename,
                filepath=filepath,
                content=content,
                language=language,
                size_bytes=size_bytes,
                checksum=checksum
            )
            self.db.add(file)
        
        await self.db.commit()
        await self.db.refresh(file)
        
        logger.info(
            "File saved",
            session_id=str(session_id),
            filepath=filepath,
            size=len(content)
        )
        
        return file
    
    async def delete_file(self, session_id: str, filepath: str) -> bool:
        """
        Delete a file or folder from the workspace.
        
        Args:
            session_id: Session identifier
            filepath: File or folder path to delete
            
        Returns:
            bool: True if file/folder was deleted successfully
        """
        try:
            # First, try to find an exact file match
            file_stmt = select(File).where(
                File.session_id == session_id,
                File.filepath == filepath
            )
            result = await self.db.execute(file_stmt)
            file = result.scalar_one_or_none()
            
            if file:
                # Delete the specific file
                await self.db.delete(file)
                await self.db.commit()
                logger.info("File deleted successfully", session_id=session_id, filepath=filepath)
                return True
            
            # If no exact file match, check if this is a folder deletion
            # Folders are represented by .placeholder files and contain other files
            placeholder_path = f"{filepath}/.placeholder"
            
            # Check if folder exists by looking for its .placeholder file
            placeholder_stmt = select(File).where(
                File.session_id == session_id,
                File.filepath == placeholder_path
            )
            placeholder_result = await self.db.execute(placeholder_stmt)
            placeholder_file = placeholder_result.scalar_one_or_none()
            
            if placeholder_file:
                # This is a folder - delete all files within it and the placeholder
                folder_pattern = f"{filepath}/%"
                
                # Find all files in the folder (including subdirectories)
                folder_files_stmt = select(File).where(
                    File.session_id == session_id,
                    File.filepath.like(folder_pattern)
                )
                folder_result = await self.db.execute(folder_files_stmt)
                folder_files = folder_result.scalars().all()
                
                # Delete all files in the folder
                for folder_file in folder_files:
                    await self.db.delete(folder_file)
                
                # Delete the placeholder file (represents the folder itself)
                await self.db.delete(placeholder_file)
                
                await self.db.commit()
                
                files_deleted = len(folder_files) + 1  # +1 for placeholder
                logger.info(
                    "Folder deleted successfully", 
                    session_id=session_id, 
                    filepath=filepath,
                    files_deleted=files_deleted
                )
                return True
            
            # Neither file nor folder found
            logger.warning("File or folder not found for deletion", session_id=session_id, filepath=filepath)
            return False
                
        except Exception as e:
            logger.error("Error deleting file/folder", error=str(e), session_id=session_id, filepath=filepath)
            await self.db.rollback()
            return False
    
    async def rename_file(self, session_id: str, old_filepath: str, new_filepath: str) -> bool:
        """
        Rename a file in the workspace.
        
        Args:
            session_id: Session identifier
            old_filepath: Current file path
            new_filepath: New file path
            
        Returns:
            bool: True if file was renamed successfully
        """
        try:
            # Find the file
            file_stmt = select(File).where(
                File.session_id == session_id,
                File.filepath == old_filepath
            )
            result = await self.db.execute(file_stmt)
            file = result.scalar_one_or_none()
            
            if file:
                # Update file path and filename
                file.filepath = new_filepath
                file.filename = os.path.basename(new_filepath)
                
                # Update checksum if needed
                file.update_content(file.content)
                
                await self.db.commit()
                await self.db.refresh(file)
                logger.info("File renamed successfully", session_id=session_id, old_filepath=old_filepath, new_filepath=new_filepath)
                return True
            else:
                logger.warning("File not found for rename", session_id=session_id, filepath=old_filepath)
                return False
                
        except Exception as e:
            logger.error("Error renaming file", error=str(e), session_id=session_id, old_filepath=old_filepath, new_filepath=new_filepath)
            await self.db.rollback()
            return False

    async def create_folder(self, session_id: str, folder_name: str, parent_path: str = "/") -> str:
        """
        Create a folder in the workspace by creating a placeholder file.
        In a file-based system, folders are implicit through file paths.
        
        Args:
            session_id: Session identifier
            folder_name: Name of the folder to create
            parent_path: Parent directory path (default: root)
            
        Returns:
            str: Full folder path that was created
        """
        try:
            # Normalize parent path
            if parent_path == "/" or parent_path == "":
                parent_path = ""
            else:
                parent_path = parent_path.rstrip("/")
            
            # Create folder path
            folder_path = f"{parent_path}/{folder_name}" if parent_path else f"/{folder_name}"
            
            # Create a placeholder file to ensure the folder exists
            placeholder_path = f"{folder_path}/.placeholder"
            placeholder_content = f"# This is a placeholder file to ensure the '{folder_name}' folder exists.\n# You can delete this file once you add other files to this folder."
            
            await self.save_file(
                session_id=session_id,
                filepath=placeholder_path,
                content=placeholder_content,
                language="text"
            )
            
            logger.info(
                "Folder created",
                session_id=session_id,
                folder_name=folder_name,
                folder_path=folder_path,
                parent_path=parent_path
            )
            
            return folder_path
            
        except Exception as e:
            logger.error("Error creating folder", error=str(e), session_id=session_id, folder_name=folder_name, parent_path=parent_path)
            raise
    
    async def create_temp_workspace(self, session_id: str) -> str:
        """
        Create a temporary filesystem workspace for execution.
        
        Args:
            session_id: Session identifier
            
        Returns:
            str: Path to temporary workspace
        """
        if session_id in self.temp_workspaces:
            return self.temp_workspaces[session_id]
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"afteride_workspace_{session_id}_")
        
        # Get all files for this session
        stmt = select(File).where(File.session_id == session_id)
        result = await self.db.execute(stmt)
        files = result.scalars().all()
        
        # Create files in temporary directory
        for file in files:
            try:
                # Skip if filepath is empty or just a slash
                if not file.filepath or file.filepath == "/":
                    continue
                    
                file_path = os.path.join(temp_dir, file.filepath.lstrip("/"))
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Only create the file if it doesn't already exist as a directory
                if not os.path.exists(file_path) or not os.path.isdir(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file.content or "")
                        
            except Exception as e:
                logger.warning(
                    "Failed to create file in temp workspace",
                    session_id=str(session_id),
                    filepath=file.filepath,
                    error=str(e)
                )
                continue
        
        self.temp_workspaces[session_id] = temp_dir
        
        logger.info(
            "Temporary workspace created",
            session_id=str(session_id),
            temp_dir=temp_dir
        )
        
        return temp_dir
    
    async def cleanup_temp_workspace(self, session_id: str) -> None:
        """
        Clean up temporary workspace.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.temp_workspaces:
            temp_dir = self.temp_workspaces[session_id]
            try:
                shutil.rmtree(temp_dir)
                del self.temp_workspaces[session_id]
                
                logger.info(
                    "Temporary workspace cleaned up",
                    session_id=str(session_id),
                    temp_dir=temp_dir
                )
            except Exception as e:
                logger.error(
                    "Failed to cleanup temporary workspace",
                    session_id=str(session_id),
                    temp_dir=temp_dir,
                    error=str(e)
                )

    async def _cleanup_temp_workspace(self, session_id: str) -> None:
        """
        Internal cleanup method for temporary workspace.
        
        Args:
            session_id: Session identifier
        """
        await self.cleanup_temp_workspace(session_id)
    
    async def _get_active_sessions(self, user_id: str) -> List[Session]:
        """Get active sessions for a user."""
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE.value
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _create_default_files(self, session_id: str) -> None:
        """Create default files for a new workspace."""
        default_files = [
            {
                "filename": "main.py",
                "filepath": "/main.py",
                "content": """# Welcome to AfterIDE!
# This is your main Python file.

def hello_world():
    print("Hello, AfterIDE!")
    print("You can run this code in the terminal below.")

if __name__ == "__main__":
    hello_world()""",
                "language": "python"
            },
            {
                "filename": "README.md",
                "filepath": "/README.md",
                "content": """# My AfterIDE Workspace

Welcome to your personal development environment!

## Getting Started

1. Edit files in the file editor
2. Run code in the terminal
3. Use `python main.py` to execute your code

Happy coding! 🚀""",
                "language": "markdown"
            },
            {
                "filename": "requirements.txt",
                "filepath": "/requirements.txt",
                "content": """# Python dependencies
requests==2.31.0
numpy==1.24.3
pandas==2.0.3""",
                "language": "text"
            }
        ]
        
        for file_info in default_files:
            await self.save_file(
                session_id=session_id,
                filepath=file_info["filepath"],
                content=file_info["content"],
                language=file_info["language"]
            ) 