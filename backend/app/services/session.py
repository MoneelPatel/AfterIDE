"""
AfterIDE - Session Service

Manages user development sessions and container environments.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.session import Session, SessionStatus
from app.models.user import User

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for managing user development sessions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new development session for a user.
        
        Args:
            user_id: ID of the user creating the session
            name: Session name
            description: Optional session description
            config: Optional session configuration
            
        Returns:
            Created session object
        """
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Set expiration time (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        now = datetime.utcnow()
        
        # Create session object
        session = Session(
            id=session_id,
            user_id=user_id,
            name=name,
            description=description or "",
            status=SessionStatus.ACTIVE.value,
            config=json.dumps(config or {}),
            expires_at=expires_at,
            max_memory_mb=512,
            max_cpu_cores=1,
            max_execution_time=30,
            created_at=now,
            updated_at=now,
            last_activity=now
        )
        
        # Add to database
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(
            "Session created",
            session_id=session_id,
            user_id=user_id,
            name=name
        )
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if found, None otherwise
        """
        stmt = select(Session).where(Session.id == session_id)
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
            List of user's active sessions
        """
        stmt = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.status == SessionStatus.ACTIVE.value
            )
        ).order_by(Session.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Session]:
        """
        Update session properties.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply
            
        Returns:
            Updated session object if successful, None otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(session, key):
                if key == "config" and isinstance(value, dict):
                    # Convert dict to JSON string for SQLite compatibility
                    setattr(session, key, json.dumps(value))
                else:
                    setattr(session, key, value)
        
        # Update timestamp
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(
            "Session updated",
            session_id=session_id,
            updates=list(updates.keys())
        )
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the database.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Remove session from database
        await self.db.delete(session)
        await self.db.commit()
        
        logger.info("Session deleted", session_id=session_id)
        return True
    
    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was terminated, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Update session status
        session.status = SessionStatus.TERMINATED.value
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info("Session terminated", session_id=session_id)
        return True
    
    async def extend_session(self, session_id: str, hours: int = 1) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session identifier
            hours: Number of hours to extend
            
        Returns:
            True if session was extended, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Extend expiration time
        session.expires_at = datetime.utcnow() + timedelta(hours=hours)
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(
            "Session extended",
            session_id=session_id,
            extension_hours=hours
        )
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # Find expired sessions
        stmt = select(Session).where(
            and_(
                Session.status == SessionStatus.ACTIVE.value,
                Session.expires_at < datetime.utcnow()
            )
        )
        
        result = await self.db.execute(stmt)
        expired_sessions = result.scalars().all()
        
        # Terminate expired sessions
        for session in expired_sessions:
            session.status = SessionStatus.TERMINATED.value
            session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        cleaned_count = len(expired_sessions)
        logger.info("Expired sessions cleanup completed", cleaned_count=cleaned_count)
        return cleaned_count 