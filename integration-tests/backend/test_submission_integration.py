"""
AfterIDE - Submission Integration Tests

Integration tests for the submission system, testing the complete workflow
from submission creation to review and management.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus
from app.models.file import File
from app.models.session import Session, SessionStatus
from app.schemas.submissions import SubmissionCreate, SubmissionReview


class TestSubmissionIntegration:
    """Integration tests for the submission system."""

    @pytest_asyncio.fixture
    async def reviewer_user(self, test_db_session: AsyncSession) -> User:
        """Create a reviewer user for testing."""
        reviewer_data = {
            "username": "reviewer",
            "password": "reviewerpass123",
            "email": "reviewer@example.com",
            "role": UserRole.REVIEWER
        }
        
        # Create reviewer user
        reviewer = User(**reviewer_data)
        test_db_session.add(reviewer)
        await test_db_session.commit()
        await test_db_session.refresh(reviewer)
        
        return reviewer

    @pytest_asyncio.fixture
    async def test_file(self, test_db_session: AsyncSession, test_session: Session) -> File:
        """Create a test file for submission."""
        file_data = {
            "filename": "test_file.py",
            "filepath": "/test_file.py",
            "language": "python",
            "content": "print('Hello, World!')",
            "session_id": str(test_session.id)
        }
        
        file = File(**file_data)
        test_db_session.add(file)
        await test_db_session.commit()
        await test_db_session.refresh(file)
        
        return file

    async def test_create_submission_success(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test successful submission creation."""
        submission_data = {
            "title": "Test Submission",
            "description": "This is a test submission",
            "file_id": str(test_file.id)
        }
        
        response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == submission_data["title"]
        assert data["description"] == submission_data["description"]
        assert data["file_id"] == str(test_file.id)
        assert data["user_id"] == authenticated_user["user_id"]
        assert data["status"] == SubmissionStatus.PENDING.value
        assert "id" in data
        assert "created_at" in data

    async def test_create_submission_with_file_path(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test submission creation using file path instead of file_id."""
        submission_data = {
            "title": "Test Submission with Path",
            "description": "Using file path for submission",
            "file_path": test_file.filepath
        }
        
        response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == submission_data["title"]
        assert data["file_id"] == str(test_file.id)
        assert data["status"] == SubmissionStatus.PENDING.value

    async def test_create_submission_with_reviewer(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        reviewer_user: User,
        test_file: File
    ):
        """Test submission creation with a specific reviewer."""
        submission_data = {
            "title": "Test Submission with Reviewer",
            "description": "Submission assigned to specific reviewer",
            "file_id": str(test_file.id),
            "reviewer_username": reviewer_user.username
        }
        
        response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["reviewer_id"] == str(reviewer_user.id)
        assert data["reviewer"]["username"] == reviewer_user.username

    async def test_create_submission_invalid_file(
        self,
        async_client: AsyncClient,
        authenticated_user: dict
    ):
        """Test submission creation with invalid file ID."""
        submission_data = {
            "title": "Test Submission",
            "description": "This should fail",
            "file_id": "invalid-uuid"
        }
        
        response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 404

    async def test_create_submission_missing_title(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test submission creation without title."""
        submission_data = {
            "description": "This should fail",
            "file_id": str(test_file.id)
        }
        
        response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 422

    async def test_get_file_by_path_success(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test getting file information by path."""
        response = await async_client.get(
            f"/api/v1/submissions/file-by-path{test_file.filepath}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["file_id"] == str(test_file.id)
        assert data["filename"] == test_file.filename
        assert data["filepath"] == test_file.filepath
        assert data["language"] == test_file.language

    async def test_get_file_by_path_not_found(
        self,
        async_client: AsyncClient,
        authenticated_user: dict
    ):
        """Test getting non-existent file by path."""
        response = await async_client.get(
            "/api/v1/submissions/file-by-path/nonexistent.py",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 404

    async def test_get_all_submissions(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File,
        test_db_session: AsyncSession
    ):
        """Test getting all submissions with pagination."""
        # Create multiple submissions
        submissions_data = [
            {"title": f"Submission {i}", "file_id": str(test_file.id)}
            for i in range(3)
        ]
        
        for submission_data in submissions_data:
            await async_client.post(
                "/api/v1/submissions/",
                json=submission_data,
                headers=authenticated_user["headers"]
            )
        
        response = await async_client.get(
            "/api/v1/submissions/all?page=1&per_page=10",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "submissions" in data
        assert "pagination" in data
        assert len(data["submissions"]) >= 3
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10

    async def test_get_pending_submissions(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test getting pending submissions."""
        # Create a submission
        submission_data = {
            "title": "Pending Submission",
            "file_id": str(test_file.id)
        }
        
        await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        response = await async_client.get(
            "/api/v1/submissions/pending",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(sub["status"] == SubmissionStatus.PENDING.value for sub in data)

    async def test_get_available_reviewers(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        reviewer_user: User
    ):
        """Test getting available reviewers."""
        response = await async_client.get(
            "/api/v1/submissions/reviewers",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our reviewer is in the list
        reviewer_usernames = [r["username"] for r in data]
        assert reviewer_user.username in reviewer_usernames

    async def test_get_submission_stats(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test getting submission statistics."""
        # Create a submission first
        submission_data = {
            "title": "Stats Test Submission",
            "file_id": str(test_file.id)
        }
        
        await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        response = await async_client.get(
            "/api/v1/submissions/stats",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_submissions" in data
        assert "pending_submissions" in data
        assert "reviewed_submissions" in data
        assert "rejected_submissions" in data
        assert "approved_submissions" in data
        assert data["total_submissions"] >= 1

    async def test_get_single_submission(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test getting a single submission by ID."""
        # Create a submission
        submission_data = {
            "title": "Single Submission Test",
            "file_id": str(test_file.id)
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        submission_id = create_response.json()["id"]
        
        # Get the submission
        response = await async_client.get(
            f"/api/v1/submissions/{submission_id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == submission_id
        assert data["title"] == submission_data["title"]
        assert data["file_id"] == str(test_file.id)

    async def test_get_submission_not_found(
        self,
        async_client: AsyncClient,
        authenticated_user: dict
    ):
        """Test getting a non-existent submission."""
        response = await async_client.get(
            "/api/v1/submissions/invalid-uuid",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 404

    async def test_review_submission(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        reviewer_user: User,
        test_file: File
    ):
        """Test reviewing a submission."""
        # Create a submission with a reviewer
        submission_data = {
            "title": "Review Test Submission",
            "file_id": str(test_file.id),
            "reviewer_username": reviewer_user.username
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        submission_id = create_response.json()["id"]
        
        # Login as reviewer
        reviewer_auth_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": reviewer_user.username,
                "password": "reviewerpass123"
            }
        )
        
        reviewer_token = reviewer_auth_response.json()["access_token"]
        reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
        
        # Review the submission
        review_data = {
            "status": SubmissionStatus.APPROVED.value,
            "comments": "Great work! This looks good.",
            "metadata": {"score": 95, "feedback": "Excellent implementation"}
        }
        
        response = await async_client.put(
            f"/api/v1/submissions/{submission_id}/review",
            json=review_data,
            headers=reviewer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == SubmissionStatus.APPROVED.value
        assert data["review_comments"] == review_data["comments"]
        assert data["review_metadata"] == review_data["metadata"]
        assert data["reviewed_at"] is not None

    async def test_update_submission(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test updating a submission."""
        # Create a submission
        submission_data = {
            "title": "Update Test Submission",
            "file_id": str(test_file.id)
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        submission_id = create_response.json()["id"]
        
        # Update the submission
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        response = await async_client.put(
            f"/api/v1/submissions/{submission_id}",
            json=update_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    async def test_delete_submission(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        test_file: File
    ):
        """Test deleting a submission."""
        # Create a submission
        submission_data = {
            "title": "Delete Test Submission",
            "file_id": str(test_file.id)
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        submission_id = create_response.json()["id"]
        
        # Delete the submission
        response = await async_client.delete(
            f"/api/v1/submissions/{submission_id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await async_client.get(
            f"/api/v1/submissions/{submission_id}",
            headers=authenticated_user["headers"]
        )
        
        assert get_response.status_code == 404

    async def test_submission_workflow_complete(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        reviewer_user: User,
        test_file: File
    ):
        """Test the complete submission workflow from creation to review."""
        # 1. Create submission
        submission_data = {
            "title": "Complete Workflow Test",
            "description": "Testing the complete workflow",
            "file_id": str(test_file.id),
            "reviewer_username": reviewer_user.username
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        assert create_response.status_code == 201
        submission_id = create_response.json()["id"]
        
        # 2. Verify submission is pending
        get_response = await async_client.get(
            f"/api/v1/submissions/{submission_id}",
            headers=authenticated_user["headers"]
        )
        
        assert get_response.status_code == 200
        assert get_response.json()["status"] == SubmissionStatus.PENDING.value
        
        # 3. Login as reviewer
        reviewer_auth_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": reviewer_user.username,
                "password": "reviewerpass123"
            }
        )
        
        reviewer_token = reviewer_auth_response.json()["access_token"]
        reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
        
        # 4. Review submission
        review_data = {
            "status": SubmissionStatus.APPROVED.value,
            "comments": "Excellent work! Approved.",
            "metadata": {"score": 98, "feedback": "Outstanding implementation"}
        }
        
        review_response = await async_client.put(
            f"/api/v1/submissions/{submission_id}/review",
            json=review_data,
            headers=reviewer_headers
        )
        
        assert review_response.status_code == 200
        reviewed_submission = review_response.json()
        
        assert reviewed_submission["status"] == SubmissionStatus.APPROVED.value
        assert reviewed_submission["review_comments"] == review_data["comments"]
        assert reviewed_submission["reviewed_at"] is not None
        
        # 5. Verify stats are updated
        stats_response = await async_client.get(
            "/api/v1/submissions/stats",
            headers=authenticated_user["headers"]
        )
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        assert stats["total_submissions"] >= 1
        assert stats["approved_submissions"] >= 1

    async def test_submission_permissions(
        self,
        async_client: AsyncClient,
        authenticated_user: dict,
        reviewer_user: User,
        test_file: File
    ):
        """Test submission permissions and access control."""
        # Create a submission
        submission_data = {
            "title": "Permission Test",
            "file_id": str(test_file.id)
        }
        
        create_response = await async_client.post(
            "/api/v1/submissions/",
            json=submission_data,
            headers=authenticated_user["headers"]
        )
        
        submission_id = create_response.json()["id"]
        
        # Try to access without authentication
        response = await async_client.get(f"/api/v1/submissions/{submission_id}")
        assert response.status_code == 401
        
        # Try to access with invalid token
        response = await async_client.get(
            f"/api/v1/submissions/{submission_id}",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    async def test_submission_validation(
        self,
        async_client: AsyncClient,
        authenticated_user: dict
    ):
        """Test submission data validation."""
        # Test with empty title
        response = await async_client.post(
            "/api/v1/submissions/",
            json={"title": "", "file_id": "some-uuid"},
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 422
        
        # Test with missing required fields
        response = await async_client.post(
            "/api/v1/submissions/",
            json={"description": "No title or file"},
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 422
        
        # Test with invalid status in review
        response = await async_client.put(
            "/api/v1/submissions/some-uuid/review",
            json={"status": "INVALID_STATUS"},
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 422 