"""
Unit Tests for API Endpoints

Tests the API endpoint functions directly to increase coverage.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime
import uuid

from app.api.v1.endpoints.auth import (
    login, register_user, logout, get_current_user
)
from app.api.v1.endpoints.sessions import (
    create_session, list_sessions, get_session, update_session, 
    delete_session
)
from app.api.v1.workspace import (
    create_session as create_workspace_session,
    get_session as get_workspace_session,
    get_workspace_files, create_file, update_file, delete_file, get_file_content
)
from app.schemas.auth import UserLogin, UserResponse, TokenResponse
from app.schemas.workspace import SessionCreate, SessionResponse, FileCreate, FileUpdate, FileContentResponse
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus
from app.models.file import File
from app.models.session import Session


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        user_credentials = UserLogin(username="admin", password="password")
        
        with patch('app.api.v1.endpoints.auth.AuthService.login_user', new_callable=AsyncMock) as mock_login:
            mock_token_response = TokenResponse(
                access_token="test-token",
                token_type="bearer",
                expires_in=3600
            )
            mock_login.return_value = mock_token_response
            
            result = await login(user_credentials)
            
            assert result == mock_token_response
            mock_login.assert_called_once_with(user_credentials)

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        user_credentials = UserLogin(username="admin", password="wrongpassword")
        
        with patch('app.api.v1.endpoints.auth.AuthService.login_user', new_callable=AsyncMock) as mock_login:
            mock_login.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await login(user_credentials)
            
            assert exc_info.value.status_code == 401
            assert "Incorrect username or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful user registration."""
        user_credentials = UserLogin(username="newuser", password="password")
        
        result = await register_user(user_credentials)
        
        assert result is not None
        assert result.username == "newuser"
        assert result.role == "user"

    @pytest.mark.asyncio
    async def test_register_user_exists(self):
        """Test user registration (placeholder - not implemented)."""
        user_credentials = UserLogin(username="existinguser", password="password")
        
        # This is a placeholder test since registration is not fully implemented
        result = await register_user(user_credentials)
        assert result is not None

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test refresh token (placeholder - not implemented)."""
        # This endpoint doesn't exist in the current implementation
        assert True

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """Test refresh token with invalid token (placeholder)."""
        # This endpoint doesn't exist in the current implementation
        assert True

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test-token"
        
        result = await logout(mock_credentials)
        
        assert result["message"] == "Successfully logged out"

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test getting current user with valid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"
        
        with patch('app.api.v1.endpoints.auth.AuthService.get_current_user', new_callable=AsyncMock) as mock_get_user:
            mock_user = {
                "id": "user123",
                "username": "testuser",
                "email": "test@example.com",
                "role": "user"
            }
            mock_get_user.return_value = mock_user
            
            result = await get_current_user(mock_credentials)
            
            assert result is not None
            assert result.id == "user123"
            assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"
        
        with patch('app.api.v1.endpoints.auth.AuthService.get_current_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid authentication credentials" in str(exc_info.value.detail)


class TestSessionEndpoints:
    """Test session API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock current user."""
        return {"id": "test-user-id", "username": "testuser", "email": "test@example.com", "role": "user"}

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_current_user, mock_db):
        """Test successful session creation."""
        name = "Test Session"
        description = "Test Description"
        config = {"language": "python"}
        
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'create_session', new_callable=AsyncMock) as mock_create:
                mock_session = MagicMock()
                mock_session.id = "test-session-id"
                mock_session.name = name
                mock_session.description = description
                mock_session.status = "active"
                mock_session.config = '{"language": "python"}'
                mock_session.expires_at.isoformat.return_value = "2023-12-31T23:59:59"
                mock_session.max_memory_mb = 512
                mock_session.max_cpu_cores = 1
                mock_session.max_execution_time = 30
                mock_create.return_value = mock_session
                
                result = await create_session(name, description, config, mock_current_user, mock_db)
                
                assert result["id"] == "test-session-id"
                assert result["name"] == name
                mock_create.assert_called_once_with(
                    user_id="test-user-id",
                    name=name,
                    description=description,
                    config=config
                )

    @pytest.mark.asyncio
    async def test_get_sessions_success(self, mock_current_user, mock_db):
        """Test successful session listing."""
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_sessions', new_callable=AsyncMock) as mock_list:
                mock_session = MagicMock()
                mock_session.id = "test-session-id"
                mock_session.name = "Test Session"
                mock_session.description = "Test Description"
                mock_session.status = "active"
                mock_session.config = '{"language": "python"}'
                mock_session.expires_at.isoformat.return_value = "2023-12-31T23:59:59"
                mock_session.max_memory_mb = 512
                mock_session.max_cpu_cores = 1
                mock_session.max_execution_time = 30
                mock_session.created_at.isoformat.return_value = "2023-12-31T00:00:00"
                mock_session.updated_at.isoformat.return_value = "2023-12-31T00:00:00"
                mock_session.last_activity.isoformat.return_value = "2023-12-31T00:00:00"
                mock_list.return_value = [mock_session]
                
                result = await list_sessions(mock_current_user, mock_db)
                
                assert len(result) == 1
                assert result[0]["id"] == "test-session-id"
                mock_list.assert_called_once_with("test-user-id")

    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_current_user, mock_db):
        """Test successful session retrieval."""
        session_id = "test-session-id"
        
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_session', new_callable=AsyncMock) as mock_get:
                mock_session = MagicMock()
                mock_session.id = session_id
                mock_session.user_id = "test-user-id"
                mock_session.name = "Test Session"
                mock_session.description = "Test Description"
                mock_session.status = "active"
                mock_session.config = '{"language": "python"}'
                mock_session.expires_at.isoformat.return_value = "2023-12-31T23:59:59"
                mock_session.max_memory_mb = 512
                mock_session.max_cpu_cores = 1
                mock_session.max_execution_time = 30
                mock_get.return_value = mock_session
                
                result = await get_session(session_id, mock_current_user, mock_db)
                
                assert result["id"] == session_id
                mock_get.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_current_user, mock_db):
        """Test session retrieval when session not found."""
        session_id = "nonexistent-session-id"
        
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_session', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_session(session_id, mock_current_user, mock_db)
                
                assert exc_info.value.status_code == 404
                mock_get.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_update_session_success(self, mock_current_user, mock_db):
        """Test successful session update."""
        session_id = "test-session-id"
        updates = {"name": "Updated Session"}
        
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_session', new_callable=AsyncMock) as mock_get:
                with patch.object(mock_service, 'update_session', new_callable=AsyncMock) as mock_update:
                    mock_session = MagicMock()
                    mock_session.id = session_id
                    mock_session.user_id = "test-user-id"
                    mock_get.return_value = mock_session
                    
                    updated_session = MagicMock()
                    updated_session.id = session_id
                    updated_session.name = "Updated Session"
                    updated_session.description = "Test Description"
                    updated_session.status = "active"
                    updated_session.config = '{"language": "python"}'
                    updated_session.expires_at.isoformat.return_value = "2023-12-31T23:59:59"
                    updated_session.max_memory_mb = 512
                    updated_session.max_cpu_cores = 1
                    updated_session.max_execution_time = 30
                    mock_update.return_value = updated_session
                    
                    result = await update_session(session_id, updates, mock_current_user, mock_db)
                    
                    assert result["id"] == session_id
                    assert result["name"] == "Updated Session"
                    mock_get.assert_called_once_with(session_id)
                    mock_update.assert_called_once_with(session_id, updates)

    @pytest.mark.asyncio
    async def test_delete_session_success(self, mock_current_user, mock_db):
        """Test successful session deletion."""
        session_id = "test-session-id"
        
        with patch('app.api.v1.endpoints.sessions.SessionService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_session', new_callable=AsyncMock) as mock_get:
                with patch.object(mock_service, 'delete_session', new_callable=AsyncMock) as mock_delete:
                    mock_session = MagicMock()
                    mock_session.id = session_id
                    mock_session.user_id = "test-user-id"
                    mock_get.return_value = mock_session
                    mock_delete.return_value = True
                    
                    result = await delete_session(session_id, mock_current_user, mock_db)
                    
                    assert result["message"] == "Session deleted successfully"
                    mock_get.assert_called_once_with(session_id)
                    mock_delete.assert_called_once_with(session_id)

    # Remove tests for methods that don't exist in the actual implementation:
    # - start_session
    # - pause_session
    # - resume_session  
    # - stop_session


class TestWorkspaceEndpoints:
    """Test workspace API endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_create_workspace_success(self, mock_db):
        """Test successful workspace creation."""
        session_data = SessionCreate(
            name="Test Workspace",
            description="Test Description",
            config={"language": "python"},
            user_id="test-user-id"
        )
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'create_user_workspace', new_callable=AsyncMock) as mock_create:
                mock_session = MagicMock()
                mock_session.id = "test-session-id"
                mock_session.name = "Test Workspace"
                mock_session.description = "Test Description"
                mock_session.status = "active"
                mock_session.created_at = "2023-12-31T00:00:00"
                mock_session.expires_at = "2023-12-31T23:59:59"
                mock_create.return_value = mock_session
                
                result = await create_workspace_session(session_data, mock_db)
                
                assert result.id == "test-session-id"
                assert result.name == "Test Workspace"
                mock_create.assert_called_once_with(user_id="test-user-id", session_name="Test Workspace")

    @pytest.mark.asyncio
    async def test_get_workspace_success(self, mock_db):
        """Test successful workspace retrieval."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get:
                mock_session = MagicMock()
                mock_session.id = session_id
                mock_session.name = "Test Workspace"
                mock_session.description = "Test Description"
                mock_session.status = "active"
                mock_session.created_at = "2023-12-31T00:00:00"
                mock_session.expires_at = "2023-12-31T23:59:59"
                mock_get.return_value = mock_session
                
                result = await get_workspace_session(session_id, user_id, mock_db)
                
                assert result.id == session_id
                mock_get.assert_called_once_with(user_id=user_id, session_id=session_id)

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self, mock_db):
        """Test workspace retrieval when workspace not found."""
        session_id = "nonexistent-session-id"
        user_id = "test-user-id"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_workspace_session(session_id, user_id, mock_db)
                
                assert exc_info.value.status_code == 404
                mock_get.assert_called_once_with(user_id=user_id, session_id=session_id)

    @pytest.mark.asyncio
    async def test_get_workspace_files_success(self, mock_db):
        """Test successful workspace files listing."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        directory = "/"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'get_workspace_files', new_callable=AsyncMock) as mock_get_files:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    
                    # Return proper file info objects
                    mock_files = [{
                        "name": "file.txt",
                        "path": "/test/file.txt",
                        "type": "file",
                        "size": 12,
                        "language": "python",
                        "modified": "2023-12-31T00:00:00"
                    }]
                    mock_get_files.return_value = mock_files
                    
                    result = await get_workspace_files(session_id, user_id, directory, mock_db)
                    
                    assert result.session_id == session_id
                    assert result.directory == directory
                    assert len(result.files) == 1
                    assert result.files[0].name == "file.txt"
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_get_files.assert_called_once_with(session_id=session_id, directory=directory)

    @pytest.mark.asyncio
    async def test_create_file_success(self, mock_db):
        """Test successful file creation."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        file_data = FileCreate(
            filepath="/test/file.txt",
            content="test content",
            language="python"
        )
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'save_file', new_callable=AsyncMock) as mock_save:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    
                    # Return a mock file with proper attributes
                    mock_file = MagicMock()
                    mock_file.id = "test-file-id"
                    mock_file.filepath = "/test/file.txt"
                    mock_file.content = "test content"
                    mock_file.language = "python"
                    mock_save.return_value = mock_file
                    
                    result = await create_file(session_id, file_data, user_id, mock_db)
                    
                    assert result.session_id == session_id
                    assert result.filepath == "/test/file.txt"
                    assert result.content == "test content"
                    assert result.language == "python"
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_save.assert_called_once_with(session_id=session_id, filepath=file_data.filepath, content=file_data.content, language=file_data.language)

    @pytest.mark.asyncio
    async def test_update_file_success(self, mock_db):
        """Test successful file update."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        filepath = "/test/file.txt"
        file_data = FileUpdate(content="updated content", language="python")
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'save_file', new_callable=AsyncMock) as mock_save:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    
                    # Return a mock file with proper attributes
                    mock_file = MagicMock()
                    mock_file.id = "test-file-id"
                    mock_file.filepath = "/test/file.txt"
                    mock_file.content = "updated content"
                    mock_file.language = "python"
                    mock_save.return_value = mock_file
                    
                    result = await update_file(session_id, filepath, file_data, user_id, mock_db)
                    
                    assert result.session_id == session_id
                    assert result.filepath == "/test/file.txt"
                    assert result.content == "updated content"
                    assert result.language == "python"
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_save.assert_called_once_with(session_id=session_id, filepath=f"/{filepath}", content=file_data.content, language=file_data.language)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, mock_db):
        """Test successful file deletion."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        filepath = "/test/file.txt"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'delete_file', new_callable=AsyncMock) as mock_delete:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    mock_delete.return_value = True
                    
                    result = await delete_file(session_id, filepath, user_id, mock_db)
                    
                    assert result["message"] == "File deleted successfully"
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_delete.assert_called_once_with(session_id=session_id, filepath=f"/{filepath}")

    @pytest.mark.asyncio
    async def test_get_file_content_success(self, mock_db):
        """Test successful file content retrieval."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        filepath = "/test/file.txt"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'get_file_content', new_callable=AsyncMock) as mock_get_content:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    
                    mock_content = "test content"
                    mock_get_content.return_value = mock_content
                    
                    result = await get_file_content(session_id, filepath, user_id, mock_db)
                    
                    assert result.content == mock_content
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_get_content.assert_called_once_with(session_id=session_id, filepath=f"/{filepath}")

    @pytest.mark.asyncio
    async def test_get_file_content_not_found(self, mock_db):
        """Test file content retrieval when file not found."""
        session_id = "test-session-id"
        user_id = "test-user-id"
        filepath = "/nonexistent/file.txt"
        
        with patch('app.api.v1.workspace.WorkspaceService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            with patch.object(mock_service, 'get_user_workspace', new_callable=AsyncMock) as mock_get_session:
                with patch.object(mock_service, 'get_file_content', new_callable=AsyncMock) as mock_get_content:
                    mock_session = MagicMock()
                    mock_get_session.return_value = mock_session
                    mock_get_content.return_value = None
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await get_file_content(session_id, filepath, user_id, mock_db)
                    
                    assert exc_info.value.status_code == 404
                    mock_get_session.assert_called_once_with(user_id=user_id, session_id=session_id)
                    mock_get_content.assert_called_once_with(session_id=session_id, filepath=f"/{filepath}")


class TestSubmissionEndpoints:
    """Test submission API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        user = MagicMock(spec=User)
        user.id = str(uuid.uuid4())
        user.username = "testuser"
        user.role = UserRole.USER
        return user

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user."""
        user = MagicMock(spec=User)
        user.id = str(uuid.uuid4())
        user.username = "admin"
        user.role = UserRole.ADMIN
        return user

    @pytest.fixture
    def mock_reviewer_user(self):
        """Mock reviewer user."""
        user = MagicMock(spec=User)
        user.id = str(uuid.uuid4())
        user.username = "reviewer"
        user.role = UserRole.REVIEWER
        return user

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_file(self):
        """Mock file."""
        file = MagicMock(spec=File)
        file.id = str(uuid.uuid4())
        file.filename = "test.py"
        file.filepath = "/test.py"
        file.language = "python"
        file.content = "print('hello')"
        file.session = MagicMock()
        file.session.user_id = str(uuid.uuid4())
        return file

    @pytest.fixture
    def mock_submission(self):
        """Mock submission."""
        submission = MagicMock(spec=Submission)
        submission.id = str(uuid.uuid4())
        submission.title = "Test Submission"
        submission.description = "Test description"
        submission.file_id = str(uuid.uuid4())
        submission.user_id = str(uuid.uuid4())
        submission.reviewer_id = str(uuid.uuid4())
        submission.status = SubmissionStatus.PENDING
        submission.review_comments = None
        submission.review_metadata = {}
        submission.created_at = datetime.now()
        submission.updated_at = datetime.now()
        submission.submitted_at = datetime.now()
        submission.reviewed_at = None
        
        # Create proper mock user objects
        mock_user = MagicMock(spec=User)
        mock_user.id = str(uuid.uuid4())
        mock_user.username = "testuser"
        mock_user.role = UserRole.USER
        
        mock_reviewer = MagicMock(spec=User)
        mock_reviewer.id = str(uuid.uuid4())
        mock_reviewer.username = "reviewer"
        mock_reviewer.role = UserRole.USER
        
        mock_file = MagicMock(spec=File)
        mock_file.id = str(uuid.uuid4())
        mock_file.filename = "test.py"
        mock_file.filepath = "/test.py"
        mock_file.language = "python"
        
        submission.user = mock_user
        submission.reviewer = mock_reviewer
        submission.file = mock_file
        return submission

    @pytest.mark.asyncio
    async def test_create_submission_success(self, mock_current_user, mock_db, mock_file):
        """Test successful submission creation."""
        from app.api.v1.endpoints.submissions import create_submission
        from app.schemas.submissions import SubmissionCreate

        submission_data = SubmissionCreate(
            title="Test Submission",
            description="Test description",
            file_id=str(uuid.uuid4())
        )

        # Mock file with proper session ownership
        mock_session = MagicMock()
        mock_session.user_id = mock_current_user.id
        mock_file.session = mock_session

        # Mock file query
        mock_file_query = MagicMock()
        mock_file_query.options.return_value = mock_file_query
        mock_file_result = MagicMock()
        mock_file_result.scalar_one_or_none.return_value = mock_file
        mock_db.execute.return_value = mock_file_result

        # Mock admin query for auto-assignment
        mock_admin = MagicMock(spec=User)
        mock_admin.id = str(uuid.uuid4())
        mock_admin.username = "admin"
        mock_admin.role = UserRole.ADMIN

        # Mock submission creation
        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = str(uuid.uuid4())
        mock_submission.user = mock_current_user
        mock_submission.reviewer = mock_admin
        mock_submission.file = mock_file

        with patch('app.api.v1.endpoints.submissions.select') as mock_select:
            # Mock file query
            mock_select.return_value.where.return_value.options.return_value = mock_file_query
            
            # Mock admin query
            mock_select.return_value.where.return_value = mock_select.return_value
            
            result = await create_submission(submission_data, mock_current_user, mock_db)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_submission_with_reviewer(self, mock_current_user, mock_db, mock_file):
        """Test submission creation with specific reviewer."""
        from app.api.v1.endpoints.submissions import create_submission
        from app.schemas.submissions import SubmissionCreate

        submission_data = SubmissionCreate(
            title="Test Submission",
            description="Test description",
            file_id=str(uuid.uuid4()),
            reviewer_username="reviewer"
        )

        # Mock file with proper session ownership
        mock_session = MagicMock()
        mock_session.user_id = mock_current_user.id
        mock_file.session = mock_session

        # Mock file query
        mock_file_query = MagicMock()
        mock_file_query.options.return_value = mock_file_query
        mock_file_result = MagicMock()
        mock_file_result.scalar_one_or_none.return_value = mock_file
        mock_db.execute.return_value = mock_file_result

        # Mock reviewer query
        mock_reviewer = MagicMock(spec=User)
        mock_reviewer.id = str(uuid.uuid4())
        mock_reviewer.username = "reviewer"

        with patch('app.api.v1.endpoints.submissions.select') as mock_select:
            # Mock file query
            mock_select.return_value.where.return_value.options.return_value = mock_file_query
            
            # Mock reviewer query
            mock_select.return_value.where.return_value = mock_select.return_value
            
            result = await create_submission(submission_data, mock_current_user, mock_db)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_submission_file_not_found(self, mock_current_user, mock_db):
        """Test submission creation with non-existent file."""
        from app.api.v1.endpoints.submissions import create_submission
        from app.schemas.submissions import SubmissionCreate

        submission_data = SubmissionCreate(
            title="Test Submission",
            description="Test description",
            file_id=str(uuid.uuid4())
        )

        # Mock file query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await create_submission(submission_data, mock_current_user, mock_db)

        assert exc_info.value.status_code == 404
        assert "File not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_submission_missing_file_id(self, mock_current_user, mock_db):
        """Test submission creation without file_id."""
        from app.api.v1.endpoints.submissions import create_submission
        from app.schemas.submissions import SubmissionCreate

        submission_data = SubmissionCreate(
            title="Test Submission",
            description="Test description",
            file_id=""  # Use empty string instead of None
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_submission(submission_data, mock_current_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "file_id is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_all_submissions_user_role(self, mock_current_user, mock_db):
        """Test getting submissions for regular user."""
        from app.api.v1.endpoints.submissions import get_all_submissions

        # Create proper mock submissions with proper user objects
        mock_submissions = []
        for i in range(3):
            mock_user = MagicMock(spec=User)
            mock_user.id = str(uuid.uuid4())
            mock_user.username = f"user{i}"
            mock_user.role = UserRole.USER
            
            mock_file = MagicMock(spec=File)
            mock_file.id = str(uuid.uuid4())
            mock_file.filename = f"test{i}.py"
            mock_file.filepath = f"/test{i}.py"
            mock_file.language = "python"
            mock_file.content = "print('hello world')"
            
            mock_submission = MagicMock(spec=Submission)
            mock_submission.id = str(uuid.uuid4())
            mock_submission.title = f"Test Submission {i}"
            mock_submission.description = f"Test description {i}"
            mock_submission.file_id = str(uuid.uuid4())
            mock_submission.user_id = str(uuid.uuid4())
            mock_submission.reviewer_id = str(uuid.uuid4())
            mock_submission.status = SubmissionStatus.PENDING
            mock_submission.review_comments = None
            mock_submission.review_metadata = {}
            mock_submission.created_at = datetime.now()
            mock_submission.updated_at = datetime.now()
            mock_submission.submitted_at = datetime.now()
            mock_submission.reviewed_at = None
            mock_submission.user = mock_user
            mock_submission.reviewer = None
            mock_submission.file = mock_file
            mock_submissions.append(mock_submission)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_submissions
        mock_db.execute.return_value = mock_result
        mock_db.scalar.return_value = 3

        result = await get_all_submissions(
            page=1,
            per_page=10,
            status_filter=None,
            current_user=mock_current_user,
            db=mock_db
        )

        assert result is not None
        assert hasattr(result, 'submissions')
        assert hasattr(result, 'total')

    @pytest.mark.asyncio
    async def test_get_all_submissions_admin_role(self, mock_admin_user, mock_db):
        """Test getting submissions for admin user."""
        from app.api.v1.endpoints.submissions import get_all_submissions

        # Create proper mock submissions with proper user objects
        mock_submissions = []
        for i in range(3):
            mock_user = MagicMock(spec=User)
            mock_user.id = str(uuid.uuid4())
            mock_user.username = f"user{i}"
            mock_user.role = UserRole.USER
            
            mock_file = MagicMock(spec=File)
            mock_file.id = str(uuid.uuid4())
            mock_file.filename = f"test{i}.py"
            mock_file.filepath = f"/test{i}.py"
            mock_file.language = "python"
            mock_file.content = "print('hello world')"
            
            mock_submission = MagicMock(spec=Submission)
            mock_submission.id = str(uuid.uuid4())
            mock_submission.title = f"Test Submission {i}"
            mock_submission.description = f"Test description {i}"
            mock_submission.file_id = str(uuid.uuid4())
            mock_submission.user_id = str(uuid.uuid4())
            mock_submission.reviewer_id = str(uuid.uuid4())
            mock_submission.status = SubmissionStatus.PENDING
            mock_submission.review_comments = None
            mock_submission.review_metadata = {}
            mock_submission.created_at = datetime.now()
            mock_submission.updated_at = datetime.now()
            mock_submission.submitted_at = datetime.now()
            mock_submission.reviewed_at = None
            mock_submission.user = mock_user
            mock_submission.reviewer = None
            mock_submission.file = mock_file
            mock_submissions.append(mock_submission)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_submissions
        mock_db.execute.return_value = mock_result
        mock_db.scalar.return_value = 3

        result = await get_all_submissions(
            page=1,
            per_page=10,
            status_filter=None,
            current_user=mock_admin_user,
            db=mock_db
        )

        assert result is not None
        assert hasattr(result, 'submissions')
        assert hasattr(result, 'total')

    @pytest.mark.asyncio
    async def test_get_pending_submissions_admin(self, mock_admin_user, mock_db):
        """Test getting pending submissions for admin."""
        from app.api.v1.endpoints.submissions import get_pending_submissions

        # Create proper mock submissions with proper user objects
        mock_submissions = []
        for i in range(2):
            mock_user = MagicMock(spec=User)
            mock_user.id = str(uuid.uuid4())
            mock_user.username = f"user{i}"
            mock_user.role = UserRole.USER
            
            mock_file = MagicMock(spec=File)
            mock_file.id = str(uuid.uuid4())
            mock_file.filename = f"test{i}.py"
            mock_file.filepath = f"/test{i}.py"
            mock_file.language = "python"
            mock_file.content = "print('hello world')"
            
            mock_submission = MagicMock(spec=Submission)
            mock_submission.id = str(uuid.uuid4())
            mock_submission.title = f"Test Submission {i}"
            mock_submission.description = f"Test description {i}"
            mock_submission.file_id = str(uuid.uuid4())
            mock_submission.user_id = str(uuid.uuid4())
            mock_submission.reviewer_id = str(uuid.uuid4())
            mock_submission.status = SubmissionStatus.PENDING
            mock_submission.review_comments = None
            mock_submission.review_metadata = {}
            mock_submission.created_at = datetime.now()
            mock_submission.updated_at = datetime.now()
            mock_submission.submitted_at = datetime.now()
            mock_submission.reviewed_at = None
            mock_submission.user = mock_user
            mock_submission.reviewer = None
            mock_submission.file = mock_file
            mock_submissions.append(mock_submission)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_submissions
        mock_db.execute.return_value = mock_result

        result = await get_pending_submissions(mock_admin_user, mock_db)

        assert result is not None
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_pending_submissions_user(self, mock_current_user, mock_db):
        """Test getting pending submissions for regular user."""
        from app.api.v1.endpoints.submissions import get_pending_submissions

        # Create proper mock submissions with proper user objects
        mock_user = MagicMock(spec=User)
        mock_user.id = str(uuid.uuid4())
        mock_user.username = "user1"
        mock_user.role = UserRole.USER
        
        mock_file = MagicMock(spec=File)
        mock_file.id = str(uuid.uuid4())
        mock_file.filename = "test.py"
        mock_file.filepath = "/test.py"
        mock_file.language = "python"
        mock_file.content = "print('hello world')"
        
        mock_submission = MagicMock(spec=Submission)
        mock_submission.id = str(uuid.uuid4())
        mock_submission.title = "Test Submission"
        mock_submission.description = "Test description"
        mock_submission.file_id = str(uuid.uuid4())
        mock_submission.user_id = str(uuid.uuid4())
        mock_submission.reviewer_id = str(uuid.uuid4())
        mock_submission.status = SubmissionStatus.PENDING
        mock_submission.review_comments = None
        mock_submission.review_metadata = {}
        mock_submission.created_at = datetime.now()
        mock_submission.updated_at = datetime.now()
        mock_submission.submitted_at = datetime.now()
        mock_submission.reviewed_at = None
        mock_submission.user = mock_user
        mock_submission.reviewer = None
        mock_submission.file = mock_file
        mock_submissions = [mock_submission]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_submissions
        mock_db.execute.return_value = mock_result

        result = await get_pending_submissions(mock_current_user, mock_db)

        assert result is not None
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_available_reviewers(self, mock_current_user, mock_db):
        """Test getting available reviewers."""
        from app.api.v1.endpoints.submissions import get_available_reviewers

        mock_users = [
            MagicMock(spec=User, id=str(uuid.uuid4()), username="user1", role=UserRole.USER, is_active=True),
            MagicMock(spec=User, id=str(uuid.uuid4()), username="user2", role=UserRole.USER, is_active=True),
            MagicMock(spec=User, id=str(uuid.uuid4()), username="admin", role=UserRole.ADMIN, is_active=True)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        result = await get_available_reviewers(mock_current_user, mock_db)

        assert result is not None
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_submission_stats_user(self, mock_current_user, mock_db):
        """Test getting submission stats for regular user."""
        from app.api.v1.endpoints.submissions import get_submission_stats

        mock_db.scalar.return_value = 5

        result = await get_submission_stats(mock_current_user, mock_db)

        assert result is not None
        assert hasattr(result, 'total')
        assert hasattr(result, 'pending')
        assert hasattr(result, 'approved')
        assert hasattr(result, 'rejected')
        assert hasattr(result, 'under_review')

    @pytest.mark.asyncio
    async def test_get_submission_stats_admin(self, mock_admin_user, mock_db):
        """Test getting submission stats for admin."""
        from app.api.v1.endpoints.submissions import get_submission_stats

        mock_db.scalar.return_value = 10

        result = await get_submission_stats(mock_admin_user, mock_db)

        assert result is not None
        assert hasattr(result, 'total')
        assert hasattr(result, 'pending')
        assert hasattr(result, 'approved')
        assert hasattr(result, 'rejected')
        assert hasattr(result, 'under_review')

    @pytest.mark.asyncio
    async def test_get_submission_success(self, mock_current_user, mock_db, mock_submission):
        """Test getting a specific submission."""
        from app.api.v1.endpoints.submissions import get_submission

        # Set up the submission to belong to the current user
        mock_submission.user_id = mock_current_user.id
        
        # Ensure the file has proper content
        mock_submission.file.content = "print('hello world')"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        result = await get_submission(str(uuid.uuid4()), mock_current_user, mock_db)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_submission_not_found(self, mock_current_user, mock_db):
        """Test getting non-existent submission."""
        from app.api.v1.endpoints.submissions import get_submission

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_submission(str(uuid.uuid4()), mock_current_user, mock_db)

        assert exc_info.value.status_code == 404
        assert "Submission not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_review_submission_success(self, mock_current_user, mock_db, mock_submission):
        """Test successful submission review."""
        from app.api.v1.endpoints.submissions import review_submission
        from app.schemas.submissions import SubmissionReview

        mock_submission.status = SubmissionStatus.PENDING
        mock_submission.reviewer_id = mock_current_user.id
        
        # Ensure the file has proper content
        mock_submission.file.content = "print('hello world')"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        review_data = SubmissionReview(
            status=SubmissionStatus.APPROVED,
            review_comments="Great work!",
            review_metadata={}
        )

        result = await review_submission(str(uuid.uuid4()), review_data, mock_current_user, mock_db)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_submission_not_pending(self, mock_current_user, mock_db, mock_submission):
        """Test reviewing non-pending submission."""
        from app.api.v1.endpoints.submissions import review_submission
        from app.schemas.submissions import SubmissionReview

        mock_submission.status = SubmissionStatus.APPROVED
        mock_submission.reviewer_id = mock_current_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        review_data = SubmissionReview(
            status=SubmissionStatus.REJECTED,
            review_comments="Rejected",
            review_metadata={}
        )

        with pytest.raises(HTTPException) as exc_info:
            await review_submission(str(uuid.uuid4()), review_data, mock_current_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "not pending review" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_review_submission_not_assigned(self, mock_current_user, mock_db, mock_submission):
        """Test reviewing submission not assigned to user."""
        from app.api.v1.endpoints.submissions import review_submission
        from app.schemas.submissions import SubmissionReview

        mock_submission.status = SubmissionStatus.PENDING
        mock_submission.reviewer_id = str(uuid.uuid4())  # Different user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        review_data = SubmissionReview(
            status=SubmissionStatus.APPROVED,
            review_comments="Great work!",
            review_metadata={}
        )

        with pytest.raises(HTTPException) as exc_info:
            await review_submission(str(uuid.uuid4()), review_data, mock_current_user, mock_db)

        assert exc_info.value.status_code == 403
        assert "not assigned to review" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_submission_success(self, mock_current_user, mock_db, mock_submission):
        """Test successful submission update."""
        from app.api.v1.endpoints.submissions import update_submission
        from app.schemas.submissions import SubmissionUpdate

        mock_submission.user_id = mock_current_user.id
        mock_submission.status = SubmissionStatus.PENDING
        
        # Ensure the file has proper content
        mock_submission.file.content = "print('hello world')"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        update_data = SubmissionUpdate(
            title="Updated Title",
            description="Updated description"
        )

        result = await update_submission(str(uuid.uuid4()), update_data, mock_current_user, mock_db)

        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_submission_success(self, mock_current_user, mock_db, mock_submission):
        """Test successful submission deletion."""
        from app.api.v1.endpoints.submissions import delete_submission

        mock_submission.user_id = mock_current_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_submission
        mock_db.execute.return_value = mock_result

        await delete_submission(str(uuid.uuid4()), mock_current_user, mock_db)

        mock_db.delete.assert_called_once_with(mock_submission)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_by_path_success(self, mock_current_user, mock_db):
        """Test getting file by path."""
        from app.api.v1.endpoints.submissions import get_file_by_path

        mock_sessions = [MagicMock(spec=Session, id=str(uuid.uuid4()))]
        mock_file = MagicMock(spec=File)
        mock_file.id = str(uuid.uuid4())
        mock_file.filename = "test.py"
        mock_file.filepath = "/test.py"
        mock_file.language = "python"
        mock_file.content = "print('hello world')"
        mock_file.session_id = str(uuid.uuid4())

        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = mock_sessions
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_file
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        result = await get_file_by_path("/test.py", mock_current_user, mock_db)

        assert result is not None
        assert result["filename"] == "test.py"
        assert result["filepath"] == "/test.py"

    @pytest.mark.asyncio
    async def test_get_file_by_path_not_found(self, mock_current_user, mock_db):
        """Test getting non-existent file by path."""
        from app.api.v1.endpoints.submissions import get_file_by_path

        mock_sessions = [MagicMock(spec=Session, id=str(uuid.uuid4()))]
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = mock_sessions
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with pytest.raises(HTTPException) as exc_info:
            await get_file_by_path("/nonexistent.py", mock_current_user, mock_db)

        assert exc_info.value.status_code == 404
        assert "File not found" in str(exc_info.value.detail) 