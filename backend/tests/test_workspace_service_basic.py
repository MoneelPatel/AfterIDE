"""
Basic tests for the workspace service.

Tests core workspace management functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.services.workspace import WorkspaceService
from app.models.session import Session, SessionStatus
from app.models.file import File


class TestWorkspaceServiceBasic:
    """Basic test cases for WorkspaceService."""

    @pytest.fixture
    def workspace_service(self):
        """Create a WorkspaceService instance with mock database."""
        mock_db = AsyncMock()
        return WorkspaceService(mock_db)

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = MagicMock(spec=Session)
        session.id = "test-session-id"
        session.user_id = "test-user-id"
        session.name = "Test Session"
        session.description = "Test Description"
        session.status = SessionStatus.ACTIVE.value
        session.config = json.dumps({"language": "python"})
        session.expires_at = datetime.utcnow() + timedelta(hours=1)
        session.created_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.last_activity = datetime.utcnow()
        return session

    @pytest.fixture
    def mock_file(self):
        """Create a mock file for testing."""
        file = MagicMock(spec=File)
        file.id = "test-file-id"
        file.session_id = "test-session-id"
        file.filepath = "/test/file.txt"
        file.filename = "file.txt"
        file.content = "test content"
        file.language = "python"
        file.size = 12
        file.created_at = datetime.utcnow()
        file.updated_at = datetime.utcnow()
        # Add the update_content method
        file.update_content = MagicMock()
        return file

    @pytest.mark.asyncio
    async def test_get_session_success(self, workspace_service, mock_session):
        """Test successful session retrieval."""
        session_id = "test-session-id"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_user_workspace("test-user-id", session_id)
            
            assert result == mock_session
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, workspace_service):
        """Test session retrieval when session not found."""
        session_id = "nonexistent-session-id"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_user_workspace("test-user-id", session_id)
            
            assert result is None
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_success(self, workspace_service, mock_file):
        """Test successful file retrieval."""
        session_id = "test-session-id"
        filepath = "/test/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_file_content(session_id, filepath)
            
            assert result == mock_file.content
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, workspace_service):
        """Test file retrieval when file not found."""
        session_id = "test-session-id"
        filepath = "/nonexistent/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_file_content(session_id, filepath)
            
            assert result is None
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workspace_files_success(self, workspace_service, mock_file):
        """Test successful workspace files listing."""
        session_id = "test-session-id"
        directory = "/"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            # First call returns file objects, second call returns string paths
            mock_result.scalars.return_value.all.side_effect = [
                [mock_file],  # First call for files
                ["/test/file.txt"]  # Second call for paths (strings)
            ]
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_workspace_files(session_id, directory)
            
            # Expect 2 items: the file and the directory created from the path
            assert len(result) == 2
            # Check that we have the file entry
            file_entry = next((item for item in result if item.get("type") == "file"), None)
            assert file_entry is not None
            assert file_entry["path"] == mock_file.filepath  # Use "path" instead of "filepath"
            mock_execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_workspace_files_empty(self, workspace_service):
        """Test workspace files listing when no files exist."""
        session_id = "test-session-id"
        directory = "/"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            # Both calls return empty lists
            mock_result.scalars.return_value.all.side_effect = [
                [],  # First call for files
                []   # Second call for paths
            ]
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_workspace_files(session_id, directory)
            
            assert result == []
            mock_execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_file_content_success(self, workspace_service, mock_file):
        """Test successful file content retrieval."""
        session_id = "test-session-id"
        filepath = "/test/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_file_content(session_id, filepath)
            
            assert result == mock_file.content
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_content_not_found(self, workspace_service):
        """Test file content retrieval when file not found."""
        session_id = "test-session-id"
        filepath = "/nonexistent/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await workspace_service.get_file_content(session_id, filepath)
            
            assert result is None
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_file_new_file(self, workspace_service, mock_session):
        """Test saving a new file."""
        session_id = "test-session-id"
        filepath = "/test/newfile.txt"
        content = "new content"
        language = "python"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            # First call returns session, second call returns None (file doesn't exist)
            mock_result.scalar_one_or_none.side_effect = [mock_session, None]
            mock_execute.return_value = mock_result
            
            with patch.object(workspace_service.db, 'add') as mock_add:
                with patch.object(workspace_service.db, 'commit') as mock_commit:
                    with patch.object(workspace_service.db, 'refresh') as mock_refresh:
                        result = await workspace_service.save_file(session_id, filepath, content, language)
                        
                        assert result is not None
                        mock_execute.assert_called()
                        mock_add.assert_called_once()
                        mock_commit.assert_called_once()
                        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_file_existing_file(self, workspace_service, mock_session, mock_file):
        """Test saving an existing file."""
        session_id = "test-session-id"
        filepath = "/test/existing.txt"
        content = "updated content"
        language = "python"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            # First call returns session, second call returns existing file
            mock_result.scalar_one_or_none.side_effect = [mock_session, mock_file]
            mock_execute.return_value = mock_result
            
            with patch.object(workspace_service.db, 'commit') as mock_commit:
                with patch.object(workspace_service.db, 'refresh') as mock_refresh:
                    result = await workspace_service.save_file(session_id, filepath, content, language)
                    
                    assert result == mock_file
                    mock_execute.assert_called()
                    mock_commit.assert_called_once()
                    mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_file_session_not_found(self, workspace_service):
        """Test saving file when session not found."""
        session_id = "nonexistent-session-id"
        filepath = "/test/file.txt"
        content = "content"
        language = "python"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            # The workspace service creates a default session when none exists
            # So we need to mock the session creation as well
            with patch.object(workspace_service.db, 'add') as mock_add:
                with patch.object(workspace_service.db, 'commit') as mock_commit:
                    with patch.object(workspace_service.db, 'refresh') as mock_refresh:
                        result = await workspace_service.save_file(session_id, filepath, content, language)
                        
                        # Should create a file even when session doesn't exist initially
                        assert result is not None
                        mock_execute.assert_called()
                        mock_add.assert_called()

    @pytest.mark.asyncio
    async def test_delete_file_success(self, workspace_service, mock_file):
        """Test successful file deletion."""
        session_id = "test-session-id"
        filepath = "/test/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_file
            mock_execute.return_value = mock_result
            
            with patch.object(workspace_service.db, 'delete') as mock_delete:
                with patch.object(workspace_service.db, 'commit') as mock_commit:
                    result = await workspace_service.delete_file(session_id, filepath)
                    
                    assert result is True
                    mock_execute.assert_called_once()
                    mock_delete.assert_called_once_with(mock_file)
                    mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, workspace_service):
        """Test file deletion when file not found."""
        session_id = "test-session-id"
        filepath = "/nonexistent/file.txt"
        
        with patch.object(workspace_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await workspace_service.delete_file(session_id, filepath)
            
            assert result is False
            # The delete_file method calls execute twice: once for session check, once for file check
            assert mock_execute.call_count == 2

    def test_workspace_service_methods_exist(self, workspace_service):
        """Test that all expected WorkspaceService methods exist."""
        expected_methods = [
            'create_user_workspace',
            'get_user_workspace',
            'get_user_sessions',
            'terminate_session',
            'get_workspace_files',
            'get_file_content',
            'save_file',
            'delete_file',
            'rename_file',
            'create_folder',
            'create_temp_workspace',
            'cleanup_temp_workspace'
        ]
        
        for method in expected_methods:
            assert hasattr(workspace_service, method) 