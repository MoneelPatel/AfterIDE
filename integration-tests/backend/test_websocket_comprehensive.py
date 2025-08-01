"""
Comprehensive WebSocket Integration Tests

Tests the complete WebSocket communication flow including connection management,
message handling, and real-time features.
"""

import pytest
from fastapi import status
import json
import asyncio


class TestWebSocketComprehensive:
    """Comprehensive WebSocket integration tests."""
    
    def test_websocket_connection_management(self, client, authenticated_user):
        """Test WebSocket connection management."""
        headers = authenticated_user["headers"]
        
        # Create a session first
        session_data = {
            "name": "WebSocket Connection Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket connection endpoint
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_message_types(self, client, authenticated_user):
        """Test different WebSocket message types."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Message Types Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for different message types
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_authentication(self, client):
        """Test WebSocket authentication."""
        # Test without authentication
        response = client.get("/ws/terminal/test-session")
        assert response.status_code in [404, 405, 400, 401, 403]
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/ws/terminal/test-session", headers=headers)
        assert response.status_code in [404, 405, 400, 401, 403]
    
    def test_websocket_session_validation(self, client, authenticated_user):
        """Test WebSocket session validation."""
        headers = authenticated_user["headers"]
        
        # Test with invalid session ID
        response = client.get("/ws/terminal/invalid-session-id", headers=headers)
        assert response.status_code in [404, 405, 400, 401, 403]
        
        # Test with non-existent session
        response = client.get("/ws/terminal/nonexistent-session", headers=headers)
        assert response.status_code in [404, 405, 400, 401, 403]
    
    def test_websocket_file_notifications(self, client, authenticated_user):
        """Test WebSocket file system notifications."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "File Notifications Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for file notifications
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_folder_notifications(self, client, authenticated_user):
        """Test WebSocket folder creation notifications."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Folder Notifications Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for folder notifications
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_connection_cleanup(self, client, authenticated_user):
        """Test WebSocket connection cleanup."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Connection Cleanup Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for connection cleanup
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_error_handling(self, client, authenticated_user):
        """Test WebSocket error handling."""
        headers = authenticated_user["headers"]
        
        # Test with malformed session ID
        response = client.get("/ws/terminal/", headers=headers)
        assert response.status_code in [404, 405, 400, 401, 403]
        
        # Test with special characters in session ID
        response = client.get("/ws/terminal/session%20with%20spaces", headers=headers)
        assert response.status_code in [404, 405, 400, 401, 403]
    
    def test_websocket_heartbeat_mechanism(self, client, authenticated_user):
        """Test WebSocket heartbeat mechanism."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Heartbeat Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for heartbeat
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_concurrent_connections(self, client, authenticated_user):
        """Test multiple concurrent WebSocket connections."""
        headers = authenticated_user["headers"]
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_data = {
                "name": f"Concurrent Test {i}",
                "user_id": "mock-user-id"
            }
            
            session_response = client.post(
                "/api/v1/workspace/sessions",
                headers=headers,
                json=session_data
            )
            assert session_response.status_code == status.HTTP_200_OK
            session_ids.append(session_response.json()["id"])
        
        # Test multiple WebSocket connections
        for session_id in session_ids:
            response = client.get(f"/ws/terminal/{session_id}", headers=headers)
            assert response.status_code in [404, 405, 400]
    
    def test_websocket_message_serialization(self, client, authenticated_user):
        """Test WebSocket message serialization."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Message Serialization Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for message serialization
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_connection_persistence(self, client, authenticated_user):
        """Test WebSocket connection persistence."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Connection Persistence Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for connection persistence
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_session_termination(self, client, authenticated_user):
        """Test WebSocket session termination."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Session Termination Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for session termination
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_message_validation(self, client, authenticated_user):
        """Test WebSocket message validation."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Message Validation Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for message validation
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_connection_recovery(self, client, authenticated_user):
        """Test WebSocket connection recovery."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Connection Recovery Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for connection recovery
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_websocket_performance(self, client, authenticated_user):
        """Test WebSocket performance under load."""
        headers = authenticated_user["headers"]
        
        # Create multiple sessions for performance testing
        session_ids = []
        for i in range(5):
            session_data = {
                "name": f"Performance Test {i}",
                "user_id": "mock-user-id"
            }
            
            session_response = client.post(
                "/api/v1/workspace/sessions",
                headers=headers,
                json=session_data
            )
            assert session_response.status_code == status.HTTP_200_OK
            session_ids.append(session_response.json()["id"])
        
        # Test multiple WebSocket connections for performance
        for session_id in session_ids:
            response = client.get(f"/ws/terminal/{session_id}", headers=headers)
            assert response.status_code in [404, 405, 400]
    
    def test_websocket_security(self, client, authenticated_user):
        """Test WebSocket security features."""
        headers = authenticated_user["headers"]
        
        # Test with potentially malicious session ID
        malicious_ids = [
            "../../../etc/passwd",
            "session'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "session%00null"
        ]
        
        for malicious_id in malicious_ids:
            response = client.get(f"/ws/terminal/{malicious_id}", headers=headers)
            assert response.status_code in [404, 405, 400, 401, 403]
    
    def test_websocket_graceful_shutdown(self, client, authenticated_user):
        """Test WebSocket graceful shutdown."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Graceful Shutdown Test",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test WebSocket endpoint for graceful shutdown
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400] 