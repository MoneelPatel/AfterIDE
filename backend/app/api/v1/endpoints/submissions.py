"""
AfterIDE - Submissions Endpoints

Code submission and review endpoints for the AfterIDE backend.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, select, func
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user_dependency
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus
from app.models.file import File
from app.models.session import Session, SessionStatus
from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionReview,
    SubmissionResponse,
    SubmissionListResponse,
    SubmissionStats,
    UserSummary,
    FileSummary
)

router = APIRouter()

def normalize_uuid_string(uuid_str: str) -> str:
    """Convert UUID string to proper format for SQLite (with hyphens)."""
    try:
        # Parse the UUID and return it in the standard format with hyphens
        return str(UUID(uuid_str))
    except ValueError:
        # If it's not a valid UUID, return as is
        return uuid_str

def _get_user_summary(user: User) -> UserSummary:
    """Convert user model to summary."""
    return UserSummary(
        id=user.id,
        username=user.username,
        role=user.role
    )

def _get_file_summary(file: File) -> FileSummary:
    """Convert file model to summary."""
    return FileSummary(
        id=file.id,
        filename=file.filename,
        filepath=file.filepath,
        language=file.language,
        content=file.content  # Include file content for reviewers
    )

def _get_submission_response(submission: Submission) -> SubmissionResponse:
    """Convert submission model to response."""
    return SubmissionResponse(
        id=submission.id,
        title=submission.title,
        description=submission.description,
        file_id=submission.file_id,
        user_id=submission.user_id,
        reviewer_id=submission.reviewer_id,
        status=submission.status,
        review_comments=submission.review_comments,
        review_metadata=submission.review_metadata,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
        submitted_at=submission.submitted_at,
        reviewed_at=submission.reviewed_at,
        user=_get_user_summary(submission.user),
        reviewer=_get_user_summary(submission.reviewer) if submission.reviewer else None,
        file=_get_file_summary(submission.file)
    )

@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Create a new code submission for review."""
    # Verify the file exists and belongs to the user
    if submission_data.file_id:
        # Check if file exists and belongs to current user
        file_query = select(File).where(
            and_(
                File.id == normalize_uuid_string(submission_data.file_id),
                File.user_id == str(current_user.id)
            )
        )
        file_result = await db.execute(file_query)
        file = file_result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )
    
    # Create submission
    submission = Submission(
        id=str(uuid.uuid4()),
        title=submission_data.title,
        description=submission_data.description,
        file_id=submission_data.file_id,
        user_id=str(current_user.id),
        status=SubmissionStatus.PENDING
    )
    
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    # Load relationships for response
    await db.refresh(submission, ['user', 'file'])
    
    return _get_submission_response(submission)

@router.get("/", response_model=SubmissionListResponse)
async def list_submissions_old(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[SubmissionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """List submissions with pagination and filtering (legacy endpoint)."""
    return await list_submissions(page, per_page, status_filter, current_user, db)

@router.get("/list", response_model=SubmissionListResponse)
async def list_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[SubmissionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """List submissions with pagination and filtering."""
    # Build query based on user role
    if current_user.role == UserRole.REVIEWER:
        # Reviewers can see all submissions
        query = select(Submission).options(
            joinedload(Submission.user),
            joinedload(Submission.reviewer),
            joinedload(Submission.file)
        )
    else:
        # Regular users can only see their own submissions
        query = select(Submission).where(
            Submission.user_id == str(current_user.id)
        ).options(
            joinedload(Submission.user),
            joinedload(Submission.reviewer),
            joinedload(Submission.file)
        )
    
    # Apply status filter if provided
    if status_filter:
        query = query.where(Submission.status == status_filter)
    
    # Add ordering
    query = query.order_by(Submission.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute query
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return SubmissionListResponse(
        submissions=[_get_submission_response(sub) for sub in submissions],
        total=total_count,
        page=page,
        per_page=per_page,
        total_pages=(total_count + per_page - 1) // per_page
    )

@router.get("/pending", response_model=List[SubmissionResponse])
async def get_pending_submissions(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get pending submissions for reviewers."""
    if current_user.role != UserRole.REVIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can access pending submissions"
        )
    
    query = select(Submission).where(
        Submission.status == SubmissionStatus.PENDING
    ).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file)
    ).order_by(Submission.created_at.asc())
    
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return [_get_submission_response(sub) for sub in submissions]

@router.get("/reviewers", response_model=List[UserSummary])
async def get_available_reviewers(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available reviewers."""
    query = select(User).where(User.role == UserRole.REVIEWER)
    result = await db.execute(query)
    reviewers = result.scalars().all()
    
    return [_get_user_summary(reviewer) for reviewer in reviewers]

@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific submission by ID."""
    query = select(Submission).where(
        Submission.id == normalize_uuid_string(submission_id)
    ).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file)
    )
    
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check access permissions
    if (current_user.role != UserRole.REVIEWER and 
        str(submission.user_id) != str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return _get_submission_response(submission)

@router.put("/{submission_id}/review", response_model=SubmissionResponse)
async def review_submission(
    submission_id: str,
    review_data: SubmissionReview,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Review a submission (reviewers only)."""
    if current_user.role != UserRole.REVIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can review submissions"
        )
    
    # Get submission
    query = select(Submission).where(
        Submission.id == normalize_uuid_string(submission_id)
    ).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file)
    )
    
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.status != SubmissionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is not pending review"
        )
    
    # Update submission with review
    submission.status = review_data.status
    submission.review_comments = review_data.comments
    submission.review_metadata = review_data.metadata
    submission.reviewer_id = str(current_user.id)
    submission.reviewed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(submission)
    
    return _get_submission_response(submission)

@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: str,
    update_data: SubmissionUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Update a submission (owner only)."""
    query = select(Submission).where(
        Submission.id == normalize_uuid_string(submission_id)
    ).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file)
    )
    
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check ownership
    if str(submission.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Only allow updates if submission is pending
    if submission.status != SubmissionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update submission that is not pending"
        )
    
    # Update fields
    if update_data.title is not None:
        submission.title = update_data.title
    if update_data.description is not None:
        submission.description = update_data.description
    
    await db.commit()
    await db.refresh(submission)
    
    return _get_submission_response(submission)

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Delete a submission (owner only)."""
    query = select(Submission).where(
        Submission.id == normalize_uuid_string(submission_id)
    )
    
    result = await db.execute(query)
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check ownership
    if str(submission.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await db.delete(submission)
    await db.commit()

@router.get("/analytics/dashboard", response_model=SubmissionStats)
async def get_submission_stats_old(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get submission statistics (legacy endpoint)."""
    return await get_submission_stats(current_user, db)

@router.get("/stats", response_model=SubmissionStats)
async def get_submission_stats(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get submission statistics."""
    if current_user.role == UserRole.REVIEWER:
        # Reviewers see all submissions
        total_query = select(func.count(Submission.id))
        pending_query = select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatus.PENDING
        )
        reviewed_query = select(func.count(Submission.id)).where(
            Submission.status.in_([SubmissionStatus.APPROVED, SubmissionStatus.REJECTED])
        )
    else:
        # Users see only their submissions
        total_query = select(func.count(Submission.id)).where(
            Submission.user_id == str(current_user.id)
        )
        pending_query = select(func.count(Submission.id)).where(
            and_(
                Submission.user_id == str(current_user.id),
                Submission.status == SubmissionStatus.PENDING
            )
        )
        reviewed_query = select(func.count(Submission.id)).where(
            and_(
                Submission.user_id == str(current_user.id),
                Submission.status.in_([SubmissionStatus.APPROVED, SubmissionStatus.REJECTED])
            )
        )
    
    total = await db.scalar(total_query)
    pending = await db.scalar(pending_query)
    reviewed = await db.scalar(reviewed_query)
    
    return SubmissionStats(
        total=total or 0,
        pending=pending or 0,
        reviewed=reviewed or 0
    )

@router.get("/test")
async def test_submissions_endpoint():
    """Test endpoint to verify submissions router is working."""
    return {
        "message": "Submissions router is working",
        "endpoints": [
            "/list",
            "/stats",
            "/pending",
            "/reviewers"
        ]
    }

@router.get("/status")
async def submissions_status():
    """Get submissions service status."""
    return {
        "message": "Submissions service is running",
        "status": "active"
    }