"""
AfterIDE - Session Model

Session management for user development environments.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base, get_uuid_column, get_uuid_default, get_json_column


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Session(Base):
    """Session model for managing user development environments."""
    
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(get_uuid_column(), primary_key=True, default=get_uuid_default())
    
    # Foreign keys
    user_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=SessionStatus.ACTIVE.value, nullable=False)
    
    # Configuration and environment
    config = Column(get_json_column(), default=dict, nullable=False)  # Python packages, environment vars, etc.
    container_id = Column(String(100), nullable=True)  # Docker container identifier
    
    # Resource limits and usage
    max_memory_mb = Column(Integer, default=512, nullable=False)
    max_cpu_cores = Column(Integer, default=1, nullable=False)
    max_execution_time = Column(Integer, default=30, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    files = relationship("File", back_populates="session", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE.value
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at 