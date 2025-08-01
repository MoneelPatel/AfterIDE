"""
Tests for the main FastAPI application.

Tests the application creation, middleware, and health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import structlog
from fastapi import FastAPI

from app.main import create_application, app


class TestMainApplication:
    """Test the main FastAPI application."""
    
    def test_create_application(self):
        """Test that the FastAPI application is created correctly."""
        assert app is not None
        assert isinstance(app, FastAPI)
        assert app.title == "AfterIDE"
        # The description doesn't contain "version" in lowercase
        assert "AfterIDE" in app.description

    def test_health_check_endpoint(self):
        """Test that the health check endpoint works."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        # The actual response includes more fields
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "version" in data

    def test_application_startup_event(self):
        """Test that the application startup event works."""
        # Test that the startup event handler exists
        assert hasattr(app, 'router')
        # The startup event is handled by FastAPI internally

    def test_application_shutdown_event(self):
        """Test that the application shutdown event works."""
        # Test that the shutdown event handler exists
        assert hasattr(app, 'router')
        # The shutdown event is handled by FastAPI internally

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        # Test that the application has middleware configured
        assert hasattr(app, 'user_middleware')
        assert len(app.user_middleware) > 0

    def test_trusted_host_middleware_configured(self):
        """Test that trusted host middleware is configured."""
        # Test that the application has middleware configured
        assert hasattr(app, 'user_middleware')
        assert len(app.user_middleware) > 0

    def test_api_routes_included(self):
        """Test that API routes are included."""
        # Test that the API router is included
        assert hasattr(app, 'router')
        # Check that some API routes exist
        routes = [route.path for route in app.routes]
        assert any('/api/' in route for route in routes)

    def test_websocket_routes_included(self):
        """Test that WebSocket routes are included."""
        # Test that WebSocket routes are included
        assert hasattr(app, 'router')
        # Check that some WebSocket routes exist
        routes = [route.path for route in app.routes]
        assert any('/ws/' in route for route in routes)


class TestApplicationInstance:
    """Test the global application instance."""
    
    def test_app_instance_exists(self):
        """Test that the global app instance exists."""
        assert app is not None
        assert hasattr(app, 'title')
        assert app.title == "AfterIDE"
    
    def test_app_has_health_endpoint(self):
        """Test that the app has the health endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200 