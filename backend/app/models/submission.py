"""
AfterIDE - Submission Model

Code submission and review workflow model.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
import uuid
import enum
import json

from app.core.database import Base, get_uuid_column, get_uuid_default, get_json_column


class JSONType(TypeDecorator):
    """Custom JSON type that handles SQLite compatibility."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python dict to JSON string when saving to database."""
        if value is None:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Convert JSON string back to Python dict when loading from database."""
        if value is None:
            return {}
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class Submission(Base):
    """Submission model for code review workflow."""
    
    __tablename__ = "submissions"
    
    # Primary key
    id = Column(get_uuid_column(), primary_key=True, default=get_uuid_default())
    
    # Foreign keys
    file_id = Column(get_uuid_column(), ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=False, index=True)
    reviewer_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=True, index=True)
    
    # Submission information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    
    # Review information
    review_comments = Column(Text, nullable=True)
    review_metadata = Column(JSONType, default=lambda: {}, nullable=False)  # Additional review data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="submissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="submissions")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews")
    
    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_pending(self) -> bool:
        """Check if submission is pending review."""
        return self.status == SubmissionStatus.PENDING 