"""
AfterIDE - User Model

User authentication and profile management.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base, get_uuid_column, get_uuid_default, get_json_column, get_boolean_column


class UserRole(str, enum.Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    REVIEWER = "reviewer"


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(get_uuid_column(), primary_key=True, default=get_uuid_default())
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(get_boolean_column(), default=True, nullable=False)
    preferences = Column(get_json_column(), default=dict, nullable=False)  # User preferences, settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", foreign_keys="Submission.user_id", cascade="all, delete-orphan")
    reviews = relationship("Submission", back_populates="reviewer", foreign_keys="Submission.reviewer_id")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_reviewer(self) -> bool:
        """Check if user has reviewer role."""
        return self.role in [UserRole.REVIEWER, UserRole.ADMIN]
    
    @property
    def is_active_bool(self) -> bool:
        """Get is_active as boolean."""
        return bool(self.is_active) 