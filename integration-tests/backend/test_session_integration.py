"""
Session Management Integration Tests

Tests the complete session management flow between frontend and backend.
"""

import pytest
from fastapi import status
import json


class TestSessionIntegration:
    """Test session management integration between frontend and backend."""
    
    def test_create_session_success(self, client, authenticated_user):
        """Test successful session creation."""
        headers = authenticated_user["headers"]
        
        session_data = {
            "name": "Test Integration Session",
            "description": "Session created during integration tests",
            "config": {
                "language": "python",
                "framework": "fastapi",
                "test_mode": True
            }
        }
        
        response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=session_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data
        assert "config" in data
        assert "expires_at" in data
        assert data["name"] == session_data["name"]
        assert data["description"] == session_data["description"]
    
    def test_create_session_without_auth(self, client):
        """Test session creation without authentication."""
        session_data = {
            "name": "Test Session",
            "description": "Test description"
        }
        
        response = client.post(
            "/api/v1/sessions/",
            params=session_data
        )
        
        assert response.status_code in [401, 403]
    
    def test_list_sessions(self, client, authenticated_user):
        """Test listing user sessions."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/sessions/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        # If there are sessions, verify their structure
        if data:
            session = data[0]
            assert "id" in session
            assert "name" in session
            assert "status" in session
            assert "created_at" in session
    
    def test_get_session_by_id(self, client, authenticated_user):
        """Test retrieving a specific session by ID."""
        headers = authenticated_user["headers"]
        
        # First create a session
        session_data = {
            "name": "Get By ID Test Session",
            "description": "Session for get by ID testing"
        }
        
        create_response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=session_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        session_id = create_response.json()["id"]
        
        # Get the session by ID
        response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == session_id
        assert "name" in data
        assert "status" in data
        assert "config" in data
    
    def test_get_nonexistent_session(self, client, authenticated_user):
        """Test retrieving a session that doesn't exist."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/sessions/nonexistent-id", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_session(self, client, authenticated_user):
        """Test updating session information."""
        headers = authenticated_user["headers"]
        
        # First create a session
        session_data = {
            "name": "Update Test Session",
            "description": "Session for update testing"
        }
        
        create_response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=session_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        session_id = create_response.json()["id"]
        
        update_data = {
            "name": "Updated Session Name",
            "description": "Updated description",
            "config": {
                "language": "javascript",
                "framework": "react",
                "updated": True
            }
        }
        
        response = client.put(
            f"/api/v1/sessions/{session_id}",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["config"]["language"] == update_data["config"]["language"]
    
    def test_delete_session(self, client, authenticated_user):
        """Test deleting a session."""
        headers = authenticated_user["headers"]
        
        # First create a session
        session_data = {
            "name": "Delete Test Session",
            "description": "Session for delete testing"
        }
        
        create_response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=session_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        session_id = create_response.json()["id"]
        
        # Delete the session
        response = client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify session is deleted
        get_response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_session_lifecycle(self, client, authenticated_user):
        """Test complete session lifecycle: create, read, update, delete."""
        headers = authenticated_user["headers"]
        
        # Step 1: Create session
        create_data = {
            "name": "Lifecycle Test Session",
            "description": "Testing complete lifecycle",
            "config": {"test": True}
        }
        
        create_response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=create_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        session_data = create_response.json()
        session_id = session_data["id"]
        
        # Step 2: Read session
        read_response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["id"] == session_id
        
        # Step 3: Update session
        update_data = {
            "name": "Updated Lifecycle Session",
            "description": "Updated description"
        }
        
        update_response = client.put(
            f"/api/v1/sessions/{session_id}",
            headers=headers,
            json=update_data
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == update_data["name"]
        
        # Step 4: Delete session
        delete_response = client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Step 5: Verify deletion
        verify_response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_session_status_transitions(self, client, authenticated_user):
        """Test session status transitions."""
        headers = authenticated_user["headers"]
        
        # First create a session
        session_data = {
            "name": "Status Test Session",
            "description": "Session for status testing"
        }
        
        create_response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=session_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        session_id = create_response.json()["id"]
        
        # Test starting session
        start_response = client.post(
            f"/api/v1/sessions/{session_id}/start",
            headers=headers
        )
        assert start_response.status_code == status.HTTP_200_OK
        
        # Test pausing session
        pause_response = client.post(
            f"/api/v1/sessions/{session_id}/pause",
            headers=headers
        )
        assert pause_response.status_code == status.HTTP_200_OK
        
        # Test resuming session
        resume_response = client.post(
            f"/api/v1/sessions/{session_id}/resume",
            headers=headers
        )
        assert resume_response.status_code == status.HTTP_200_OK
    
    def test_session_config_validation(self, client, authenticated_user):
        """Test session configuration validation."""
        headers = authenticated_user["headers"]
        
        # Test with invalid config
        invalid_data = {
            "name": "Invalid Config Session",
            "config": {
                "invalid_field": "invalid_value",
                "max_memory_mb": "not_a_number"  # Should be number
            }
        }
        
        response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            params=invalid_data
        )
        
        # Should either validate and accept or return validation error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_session_pagination(self, client, authenticated_user):
        """Test session listing with pagination."""
        headers = authenticated_user["headers"]
        
        # Test with pagination parameters
        response = client.get(
            "/api/v1/sessions/",
            headers=headers,
            params={"page": 1, "size": 10}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure (could be list or paginated response)
        assert isinstance(data, list) or ("items" in data and "total" in data) 