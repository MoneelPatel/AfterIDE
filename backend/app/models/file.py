"""
AfterIDE - File Model

File management for code files within development sessions.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import hashlib

from app.core.database import Base, get_uuid_column, get_uuid_default


class File(Base):
    """File model for managing code files within sessions."""
    
    __tablename__ = "files"
    
    # Primary key
    id = Column(get_uuid_column(), primary_key=True, default=get_uuid_default())
    
    # Foreign keys
    session_id = Column(get_uuid_column(), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)  # Relative path within session
    content = Column(Text, nullable=False)
    
    # File metadata
    language = Column(String(50), nullable=False, default="python")  # python, javascript, etc.
    size_bytes = Column(Integer, nullable=False, default=0)
    checksum = Column(String(64), nullable=False)  # SHA-256 hash of content
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="files")
    submissions = relationship("Submission", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename='{self.filename}', session_id={self.session_id})>"
    
    def update_content(self, new_content: str) -> None:
        """
        Update file content and recalculate metadata.
        
        Args:
            new_content: New file content
        """
        self.content = new_content
        self.size_bytes = len(new_content.encode('utf-8'))
        self.checksum = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
        self.updated_at = func.now()
    
    @property
    def is_python_file(self) -> bool:
        """Check if file is a Python file."""
        return self.language.lower() == "python" or self.filename.endswith('.py')
    
    @property
    def display_name(self) -> str:
        """Get display name for the file."""
        return self.filename or "Untitled" 