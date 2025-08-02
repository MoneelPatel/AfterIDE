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
        id=str(user.id),  # Convert UUID to string
        username=user.username,
        role=user.role
    )

def _get_file_summary(file: File) -> FileSummary:
    """Convert file model to summary."""
    return FileSummary(
        id=str(file.id),  # Convert UUID to string
        filename=file.filename,
        filepath=file.filepath,
        language=file.language,
        content=file.content  # Include file content for reviewers
    )

def _get_submission_response(submission: Submission) -> SubmissionResponse:
    """Convert submission model to response."""
    return SubmissionResponse(
        id=str(submission.id),  # Convert UUID to string
        title=submission.title,
        description=submission.description,
        file_id=str(submission.file_id),  # Convert UUID to string
        user_id=str(submission.user_id),  # Convert UUID to string
        reviewer_id=str(submission.reviewer_id) if submission.reviewer_id else None,  # Convert UUID to string
        status=submission.status,
        review_comments=submission.review_comments,
        review_metadata=submission.review_metadata,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
        submitted_at=submission.submitted_at,
        reviewed_at=submission.reviewed_at,
        user=_get_user_summary(submission.user) if submission.user else None,
        reviewer=_get_user_summary(submission.reviewer) if submission.reviewer else None,
        file=_get_file_summary(submission.file) if submission.file else None
    )

@router.get("/file-by-path/{filepath:path}")
async def get_file_by_path(
    filepath: str,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get file information by path for submission creation."""
    try:
        # Normalize the filepath to avoid double slashes
        normalized_filepath = f"/{filepath.lstrip('/')}"
        
        # Query file by filepath (assuming files belong to the current user's sessions)
        # First, get the user's sessions
        session_query = select(Session).where(Session.user_id == str(current_user.id))
        session_result = await db.execute(session_query)
        user_sessions = session_result.scalars().all()
        
        if not user_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sessions found for user"
            )
        
        # Search for the file in any of the user's sessions
        file_query = select(File).where(
            and_(
                File.session_id.in_([str(session.id) for session in user_sessions]),
                File.filepath == normalized_filepath
            )
        )
        
        file_result = await db.execute(file_query)
        file = file_result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {normalized_filepath}"
            )
        
        return {
            "file_id": str(file.id),
            "filename": file.filename,
            "filepath": file.filepath,
            "language": file.language,
            "session_id": str(file.session_id)
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error in get_file_by_path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file information"
        )

@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Create a new code submission for review."""
    try:
        # Validate that file_id is provided
        if not submission_data.file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_id is required for submissions"
            )
        
        # Verify the file exists and belongs to the user's session
        file_query = select(File).where(
            File.id == normalize_uuid_string(submission_data.file_id)
        ).options(joinedload(File.session))
        file_result = await db.execute(file_query)
        file = file_result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found. Please save your file before submitting."
            )
        
        # Check if the file belongs to the current user's session
        if str(file.session.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only submit files from your own sessions."
            )
        
        # Handle reviewer assignment if provided
        reviewer_id = None
        if submission_data.reviewer_username:
            # Find the reviewer by username (any user can be a reviewer)
            reviewer_query = select(User).where(
                User.username == submission_data.reviewer_username
            )
            reviewer_result = await db.execute(reviewer_query)
            reviewer = reviewer_result.scalar_one_or_none()
            
            if not reviewer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Reviewer '{submission_data.reviewer_username}' not found"
                )
            reviewer_id = str(reviewer.id)
        else:
            # If no reviewer specified, automatically assign admin
            admin_query = select(User).where(User.role == UserRole.ADMIN)
            admin_result = await db.execute(admin_query)
            admin = admin_result.scalar_one_or_none()
            
            if admin:
                reviewer_id = str(admin.id)
        
        # Create submission
        submission = Submission(
            id=str(uuid.uuid4()),
            title=submission_data.title,
            description=submission_data.description,
            file_id=submission_data.file_id,
            user_id=str(current_user.id),
            reviewer_id=reviewer_id,
            status=SubmissionStatus.PENDING
        )
        
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        
        # Load relationships for response
        await db.refresh(submission, ['user', 'file', 'reviewer'])
        
        return _get_submission_response(submission)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error in create_submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission"
        )

@router.get("/all", response_model=SubmissionListResponse)
async def get_all_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[SubmissionStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get all submissions with pagination and filtering (new endpoint)."""
    try:
        # Build query based on user role
        if current_user.role in [UserRole.REVIEWER, UserRole.ADMIN]:
            # Reviewers and admins can see all submissions
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
            total=total_count or 0,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page if total_count else 0
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_all_submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch submissions"
        )

@router.get("/pending", response_model=List[SubmissionResponse])
async def get_pending_submissions(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get pending submissions assigned to the current user for review."""
    # Build query based on user role
    if current_user.role == UserRole.ADMIN:
        # Admins can see all pending submissions
        query = select(Submission).where(
            Submission.status == SubmissionStatus.PENDING
        ).options(
            joinedload(Submission.user),
            joinedload(Submission.reviewer),
            joinedload(Submission.file)
        )
    else:
        # Any user can see pending submissions assigned to them
        query = select(Submission).where(
            and_(
                Submission.status == SubmissionStatus.PENDING,
                Submission.reviewer_id == str(current_user.id)
            )
        ).options(
            joinedload(Submission.user),
            joinedload(Submission.reviewer),
            joinedload(Submission.file)
        )
    
    # Add ordering
    query = query.order_by(Submission.created_at.asc())
    
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return [_get_submission_response(sub) for sub in submissions]

@router.get("/reviewers", response_model=List[UserSummary])
async def get_available_reviewers(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all available users who can be assigned as reviewers."""
    # Query all users (any user can be a reviewer)
    query = select(User).where(User.is_active == True)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [_get_user_summary(user) for user in users]

@router.get("/stats", response_model=SubmissionStats)
async def get_submission_stats(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Get submission statistics."""
    if current_user.role in [UserRole.REVIEWER, UserRole.ADMIN]:
        # Reviewers and admins see all submissions
        total_query = select(func.count(Submission.id))
        pending_query = select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatus.PENDING
        )
        approved_query = select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatus.APPROVED
        )
        rejected_query = select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatus.REJECTED
        )
        under_review_query = select(func.count(Submission.id)).where(
            Submission.status == SubmissionStatus.UNDER_REVIEW
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
        approved_query = select(func.count(Submission.id)).where(
            and_(
                Submission.user_id == str(current_user.id),
                Submission.status == SubmissionStatus.APPROVED
            )
        )
        rejected_query = select(func.count(Submission.id)).where(
            and_(
                Submission.user_id == str(current_user.id),
                Submission.status == SubmissionStatus.REJECTED
            )
        )
        under_review_query = select(func.count(Submission.id)).where(
            and_(
                Submission.user_id == str(current_user.id),
                Submission.status == SubmissionStatus.UNDER_REVIEW
            )
        )
    
    total = await db.scalar(total_query)
    pending = await db.scalar(pending_query)
    approved = await db.scalar(approved_query)
    rejected = await db.scalar(rejected_query)
    under_review = await db.scalar(under_review_query)
    
    return SubmissionStats(
        total=total or 0,
        pending=pending or 0,
        approved=approved or 0,
        rejected=rejected or 0,
        under_review=under_review or 0
    )

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
    """Review a submission (assigned reviewer only)."""
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
    
    # Check if the current user is the assigned reviewer (or admin can review any)
    if (current_user.role != UserRole.ADMIN and 
        (not submission.reviewer_id or str(submission.reviewer_id) != str(current_user.id))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to review this submission"
        )
    
    # Update submission with review
    submission.status = review_data.status
    submission.review_comments = review_data.review_comments
    submission.review_metadata = review_data.review_metadata or {}
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