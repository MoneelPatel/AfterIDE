"""
AfterIDE - Submission Schemas

Pydantic models for code submission and review workflow.
"""

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.submission import SubmissionStatus
from app.models.user import UserRole


class SubmissionBase(BaseModel):
    """Base submission model."""
    title: str = Field(..., min_length=1, max_length=200, description="Submission title")
    description: Optional[str] = Field(None, description="Submission description")
    file_id: str = Field(..., description="ID of the file being submitted")
    file_path: Optional[str] = Field(None, description="Path of the file being submitted (alternative to file_id)")


class SubmissionCreate(SubmissionBase):
    """Model for creating a new submission."""
    reviewer_username: Optional[str] = Field(None, description="Username of the reviewer to assign")


class SubmissionUpdate(BaseModel):
    """Model for updating a submission."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    review_comments: Optional[str] = None
    status: Optional[SubmissionStatus] = None


class SubmissionReview(BaseModel):
    """Model for reviewing a submission."""
    status: SubmissionStatus = Field(..., description="Review decision")
    review_comments: Optional[str] = Field(None, description="Review comments")
    review_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserSummary(BaseModel):
    """Summary of user information."""
    id: str
    username: str
    role: UserRole


class FileSummary(BaseModel):
    """Summary of file information."""
    id: str
    filename: str
    filepath: str
    language: Optional[str] = None
    content: Optional[str] = None  # Add file content for reviewers


class SubmissionResponse(BaseModel):
    """Full submission response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    description: Optional[str] = None
    file_id: str
    user_id: str
    reviewer_id: Optional[str] = None
    status: SubmissionStatus
    review_comments: Optional[str] = None
    review_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    
    # Related data
    user: UserSummary
    reviewer: Optional[UserSummary] = None
    file: FileSummary
    
    @field_serializer('created_at', 'updated_at', 'submitted_at', 'reviewed_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is None:
            return None
        return value.isoformat()


class SubmissionListResponse(BaseModel):
    """Response model for listing submissions."""
    submissions: List[SubmissionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SubmissionStats(BaseModel):
    """Statistics for submissions."""
    total: int
    pending: int
    approved: int
    rejected: int
    under_review: int 