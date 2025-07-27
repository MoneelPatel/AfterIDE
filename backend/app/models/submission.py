"""
AfterIDE - Submission Model

Code submission and review workflow model.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Submission information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    
    # Review information
    review_comments = Column(Text, nullable=True)
    review_metadata = Column(JSONB, default=dict, nullable=False)  # Additional review data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="submissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="submissions")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviewed_submissions")
    
    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_pending(self) -> bool:
        """Check if submission is pending review."""
        return self.status == SubmissionStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Check if submission has been approved."""
        return self.status == SubmissionStatus.APPROVED
    
    @property
    def is_rejected(self) -> bool:
        """Check if submission has been rejected."""
        return self.status == SubmissionStatus.REJECTED
    
    @property
    def has_reviewer(self) -> bool:
        """Check if submission has been assigned to a reviewer."""
        return self.reviewer_id is not None 