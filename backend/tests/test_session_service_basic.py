"""
Basic tests for the session service.

Tests core session management functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.services.session import SessionService
from app.models.session import Session, SessionStatus


class TestSessionServiceBasic:
    """Basic test cases for SessionService."""

    @pytest.fixture
    def session_service(self):
        """Create a SessionService instance with mock database."""
        mock_db = AsyncMock()
        return SessionService(mock_db)

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
        session.max_memory_mb = 512
        session.max_cpu_cores = 1
        session.max_execution_time = 30
        session.created_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.last_activity = datetime.utcnow()
        return session

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, mock_session):
        """Test successful session creation."""
        session_data = {
            "user_id": "test-user-id",
            "name": "Test Session",
            "description": "Test Description",
            "config": {"language": "python"}
        }
        
        with patch.object(session_service.db, 'add') as mock_add:
            with patch.object(session_service.db, 'commit') as mock_commit:
                with patch.object(session_service.db, 'refresh') as mock_refresh:
                    # The refresh method modifies the session object in place
                    mock_refresh.side_effect = lambda session: setattr(session, 'id', 'test-session-id')
                    
                    result = await session_service.create_session(
                        session_data["user_id"],
                        session_data["name"],
                        session_data["description"],
                        session_data["config"]
                    )
                    
                    # Should return a Session object with the expected attributes
                    assert result is not None
                    assert hasattr(result, 'id')
                    assert hasattr(result, 'name')
                    assert hasattr(result, 'status')
                    mock_add.assert_called_once()
                    mock_commit.assert_called_once()
                    mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_success(self, session_service, mock_session):
        """Test successful session retrieval."""
        session_id = "test-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result
            
            result = await session_service.get_session(session_id)
            
            assert result == mock_session
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service):
        """Test session retrieval when session not found."""
        session_id = "nonexistent-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await session_service.get_session(session_id)
            
            assert result is None
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions_success(self, session_service, mock_session):
        """Test successful session listing."""
        user_id = "test-user-id"
        mock_sessions = [mock_session]
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_sessions
            mock_execute.return_value = mock_result
            
            result = await session_service.get_user_sessions(user_id)
            
            assert result == mock_sessions
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, session_service):
        """Test session listing when no sessions exist."""
        user_id = "test-user-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_execute.return_value = mock_result
            
            result = await session_service.get_user_sessions(user_id)
            
            assert result == []
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_success(self, session_service, mock_session):
        """Test successful session update."""
        session_id = "test-session-id"
        updates = {"name": "Updated Session"}
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result
            
            with patch.object(session_service.db, 'commit') as mock_commit:
                with patch.object(session_service.db, 'refresh') as mock_refresh:
                    result = await session_service.update_session(session_id, updates)
                    
                    assert result == mock_session
                    mock_execute.assert_called()
                    # get_session calls commit once, update_session calls commit once
                    assert mock_commit.call_count == 2
                    mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, session_service):
        """Test session update when session not found."""
        session_id = "nonexistent-session-id"
        updates = {"name": "Updated Session"}
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await session_service.update_session(session_id, updates)
            
            assert result is None
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_success(self, session_service, mock_session):
        """Test successful session deletion."""
        session_id = "test-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result
            
            with patch.object(session_service.db, 'delete') as mock_delete:
                with patch.object(session_service.db, 'commit') as mock_commit:
                    result = await session_service.delete_session(session_id)
                    
                    assert result is True
                    mock_execute.assert_called()
                    mock_delete.assert_called_once_with(mock_session)
                    # get_session calls commit once, delete_session calls commit once
                    assert mock_commit.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_service):
        """Test session deletion when session not found."""
        session_id = "nonexistent-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await session_service.delete_session(session_id)
            
            assert result is False
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_session_success(self, session_service, mock_session):
        """Test successful session termination."""
        session_id = "test-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result
            
            with patch.object(session_service.db, 'commit') as mock_commit:
                result = await session_service.terminate_session(session_id)
                
                assert result is True
                mock_execute.assert_called()
                # get_session calls commit once, terminate_session calls commit once
                assert mock_commit.call_count == 2

    @pytest.mark.asyncio
    async def test_terminate_session_not_found(self, session_service):
        """Test session termination when session not found."""
        session_id = "nonexistent-session-id"
        
        with patch.object(session_service.db, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await session_service.terminate_session(session_id)
            
            assert result is False
            mock_execute.assert_called_once()

    def test_session_service_methods_exist(self, session_service):
        """Test that all expected SessionService methods exist."""
        expected_methods = [
            'create_session',
            'get_session',
            'get_user_sessions',
            'update_session',
            'delete_session',
            'terminate_session',
            'extend_session',
            'cleanup_expired_sessions'
        ]
        
        for method in expected_methods:
            assert hasattr(session_service, method) 