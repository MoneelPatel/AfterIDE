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
        # Look up by file ID
        file = await db.execute(
            select(File).options(joinedload(File.session)).filter(File.id == submission_data.file_id)
        )
        file = file.scalar_one_or_none()
    elif submission_data.file_path:
        # Look up by file path - need to find the user's current session first
        user_session = await db.execute(
            select(Session).filter(
                and_(
                    Session.user_id == current_user.id,
                    Session.status == SessionStatus.ACTIVE.value
                )
            ).order_by(Session.created_at.desc())
        )
        user_session = user_session.scalar_one_or_none()
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found"
            )
        
        # Look up file by path in the user's session
        file = await db.execute(
            select(File).options(joinedload(File.session)).filter(
                and_(
                    File.session_id == user_session.id,
                    File.filepath == submission_data.file_path
                )
            )
        )
        file = file.scalar_one_or_none()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or file_path must be provided"
        )
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if user has access to the file (through session)
    if file.session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this file"
        )
    
    # Check if submission already exists for this file
    existing_submission = await db.execute(select(Submission).filter(
        and_(
            Submission.file_id == file.id,
            Submission.status.in_([SubmissionStatus.PENDING, SubmissionStatus.UNDER_REVIEW])
        )
    ))
    existing_submission = existing_submission.scalar_one_or_none()
    
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A submission already exists for this file"
        )
    
    # Handle reviewer assignment if specified
    reviewer_id = None
    if submission_data.reviewer_username:
        reviewer = await db.execute(select(User).filter(User.username == submission_data.reviewer_username))
        reviewer = reviewer.scalar_one_or_none()
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reviewer with username '{submission_data.reviewer_username}' not found"
            )
        
        if not reviewer.is_reviewer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{submission_data.reviewer_username}' is not a reviewer"
            )
        
        reviewer_id = reviewer.id
    
    # Create new submission
    submission = Submission(
        title=submission_data.title,
        description=submission_data.description,
        file_id=file.id,
        user_id=current_user.id,
        reviewer_id=reviewer_id,
        status=SubmissionStatus.PENDING
    )
    
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    # Load relationships for response
    await db.refresh(submission.user)
    await db.refresh(submission.reviewer)
    await db.refresh(submission.file)
    
    return _get_submission_response(submission)


@router.get("/", response_model=SubmissionListResponse)
async def list_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[SubmissionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """List submissions based on user role and filters."""
    query = select(Submission).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file).joinedload(File.session)
    )
    
    # Filter based on user role
    if current_user.is_reviewer:
        # Reviewers can see all submissions
        if status_filter:
            query = query.filter(Submission.status == status_filter)
    else:
        # Regular users can only see their own submissions
        query = query.filter(Submission.user_id == current_user.id)
        if status_filter:
            query = query.filter(Submission.status == status_filter)
    
    # Get total count
    total = await db.scalar(select(func.count()).select_from(query.alias()))
    
    # Apply pagination
    submissions = await db.scalars(query.order_by(Submission.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page))
    
    total_pages = (total + per_page - 1) // per_page
    
    return SubmissionListResponse(
        submissions=[_get_submission_response(sub) for sub in submissions],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/pending", response_model=List[SubmissionResponse])
async def get_pending_submissions(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get pending submissions for reviewers."""
    if not current_user.is_reviewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can access pending submissions"
        )
    
    # Get submissions that are either unassigned or assigned to the current reviewer
    submissions = await db.scalars(select(Submission).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file).joinedload(File.session)
    ).filter(
        and_(
            Submission.status == SubmissionStatus.PENDING,
            or_(
                Submission.reviewer_id.is_(None),  # Unassigned submissions
                Submission.reviewer_id == current_user.id  # Assigned to current reviewer
            )
        )
    ).order_by(Submission.created_at.asc()))
    
    return [_get_submission_response(sub) for sub in submissions]


@router.get("/reviewers", response_model=List[UserSummary])
async def get_available_reviewers(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available reviewers."""
    # All authenticated users can see the list of available reviewers
    reviewers = await db.scalars(select(User).filter(
        User.role.in_([UserRole.REVIEWER, UserRole.ADMIN])
    ).filter(User.is_active == 1)) # Use 1 for SQLite boolean
    
    return [_get_user_summary(reviewer) for reviewer in reviewers]


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific submission by ID."""
    # Use direct string comparison - the ID should match exactly as stored in database
    submission = await db.scalar(select(Submission).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file).joinedload(File.session)
    ).filter(Submission.id == submission_id))
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check access permissions
    if not current_user.is_reviewer and submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this submission"
        )
    
    return _get_submission_response(submission)


@router.put("/{submission_id}/review", response_model=SubmissionResponse)
async def review_submission(
    submission_id: str,
    review_data: SubmissionReview,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Review a submission (approve/reject)."""
    if not current_user.is_reviewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can review submissions"
        )
    
    # Use direct string comparison - the ID should match exactly as stored in database
    submission = await db.scalar(select(Submission).options(
        joinedload(Submission.user),
        joinedload(Submission.reviewer),
        joinedload(Submission.file).joinedload(File.session)
    ).filter(Submission.id == submission_id))
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.status not in [SubmissionStatus.PENDING, SubmissionStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is not in a reviewable state"
        )
    
    # Check if submission is assigned to a specific reviewer
    if submission.reviewer_id and submission.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This submission is assigned to another reviewer"
        )
    
    # Update submission with review
    submission.status = review_data.status
    submission.review_comments = review_data.review_comments
    submission.review_metadata = review_data.review_metadata or {}
    submission.reviewer_id = current_user.id
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
    """Update a submission (only by the original author)."""
    submission = await db.scalar(select(Submission).filter(Submission.id == submission_id))
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the submission author can update it"
        )
    
    if submission.status not in [SubmissionStatus.PENDING, SubmissionStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update submission in current state"
        )
    
    # Update fields
    if update_data.title is not None:
        submission.title = update_data.title
    if update_data.description is not None:
        submission.description = update_data.description
    
    await db.commit()
    await db.refresh(submission)
    
    # Load relationships for response
    await db.refresh(submission.user)
    await db.refresh(submission.reviewer)
    await db.refresh(submission.file)
    
    return _get_submission_response(submission)


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Delete a submission (only by the original author if pending)."""
    submission = await db.scalar(select(Submission).filter(Submission.id == submission_id))
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the submission author or admin can delete it"
        )
    
    if submission.status not in [SubmissionStatus.PENDING] and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete submission in current state"
        )
    
    await db.delete(submission)
    await db.commit()


@router.get("/stats/overview", response_model=SubmissionStats)
async def get_submission_stats(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get submission statistics."""
    query = select(Submission)
    
    # Filter based on user role
    if not current_user.is_reviewer:
        query = query.filter(Submission.user_id == current_user.id)
    
    total = await db.scalar(select(func.count()).select_from(query.alias()))
    pending = await db.scalar(select(func.count()).select_from(query.filter(Submission.status == SubmissionStatus.PENDING).alias()))
    approved = await db.scalar(select(func.count()).select_from(query.filter(Submission.status == SubmissionStatus.APPROVED).alias()))
    rejected = await db.scalar(select(func.count()).select_from(query.filter(Submission.status == SubmissionStatus.REJECTED).alias()))
    under_review = await db.scalar(select(func.count()).select_from(query.filter(Submission.status == SubmissionStatus.UNDER_REVIEW).alias()))
    
    return SubmissionStats(
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
        under_review=under_review
    ) 


@router.get("/debug/ids", include_in_schema=False)
async def debug_submission_ids(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to inspect submission IDs."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all submission IDs
    submissions = await db.scalars(select(Submission.id))
    ids = submissions.all()
    
    # Get the specific ID we're looking for
    target_id = "524c423e-3fe5-4571-8bba-beaac4645614"
    target_id_no_hyphens = target_id.replace("-", "")
    
    # Check if either format exists
    submission_with_hyphens = await db.scalar(select(Submission).filter(Submission.id == target_id))
    submission_without_hyphens = await db.scalar(select(Submission).filter(Submission.id == target_id_no_hyphens))
    
    return {
        "all_ids": [str(id) for id in ids],
        "target_id_with_hyphens": target_id,
        "target_id_without_hyphens": target_id_no_hyphens,
        "found_with_hyphens": submission_with_hyphens is not None,
        "found_without_hyphens": submission_without_hyphens is not None,
        "total_submissions": len(ids)
    } 


@router.get("/test/{submission_id}", include_in_schema=False)
async def test_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint to check basic submission retrieval."""
    try:
        submission = await db.scalar(select(Submission).filter(Submission.id == submission_id))
        if submission:
            return {"found": True, "id": str(submission.id), "title": submission.title}
        else:
            return {"found": False, "searched_id": submission_id}
    except Exception as e:
        return {"error": str(e), "searched_id": submission_id} 