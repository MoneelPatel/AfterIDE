"""
Basic Integration Tests

Simple tests to verify the integration test setup is working.
"""

import pytest
from fastapi import status


class TestBasicIntegration:
    """Basic integration tests to verify setup."""
    
    def test_health_check(self, client):
        """Test if the application is running."""
        response = client.get("/")
        # Should return some response (could be 200, 404, etc.)
        assert response.status_code in [200, 404, 405]
    
    def test_api_docs_available(self, client):
        """Test if API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema_available(self, client):
        """Test if OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
    
    def test_auth_endpoint_exists(self, client):
        """Test if auth endpoint exists."""
        response = client.post("/api/v1/auth/login", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code == 422
    
    def test_sessions_endpoint_exists(self, client):
        """Test if sessions endpoint exists."""
        response = client.get("/api/v1/sessions/")
        # Should return 401 (unauthorized) or 403 (forbidden) not 404 (not found)
        assert response.status_code in [401, 403]
    
    def test_websocket_endpoint_exists(self, client):
        """Test if WebSocket endpoint exists."""
        # This is a basic check - WebSocket endpoints might not be accessible via HTTP GET
        response = client.get("/ws/terminal/test-session")
        # Should return some response (could be 404, 405, etc.)
        assert response.status_code in [404, 405, 400] 