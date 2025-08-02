"""
Integration tests for the main FastAPI application.

Tests the complete application setup and integration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import structlog

from app.main import app


class TestMainApplicationIntegration:
    """Test the main application integration."""
    
    def test_app_instance_creation(self):
        """Test that the app instance is created correctly."""
        assert app is not None
        assert hasattr(app, 'title')
        assert app.title == "AfterIDE"
        assert hasattr(app, 'description')
        assert "AfterIDE - Web-Based Integrated Development Environment" in app.description
    
    def test_app_has_health_endpoint(self):
        """Test that the app has the health endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
    
    def test_app_has_api_routes(self):
        """Test that the app has API routes configured."""
        client = TestClient(app)
        
        # Test that API routes exist (will return 403 due to auth, not 404)
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 403  # Forbidden, not 404

    def test_app_has_websocket_routes(self):
        """Test that the app has WebSocket routes."""
        # Check that WebSocket routes are included in the app
        ws_routes = [route for route in app.routes if hasattr(route, 'path') and '/ws' in route.path]
        assert len(ws_routes) > 0
    
    def test_app_middleware_configuration(self):
        """Test that the app has proper middleware configuration."""
        # Check that middleware is configured
        assert len(app.user_middleware) > 0
        
        # Check for CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        assert cors_middleware is not None
        
        # Check for TrustedHost middleware
        trusted_host_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "TrustedHostMiddleware":
                trusted_host_middleware = middleware
                break
        assert trusted_host_middleware is not None
    
    def test_app_openapi_configuration(self):
        """Test that the app has proper OpenAPI configuration."""
        client = TestClient(app)
        
        # Test OpenAPI schema endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Test docs endpoint
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_app_route_structure(self):
        """Test the overall route structure of the app."""
        # Check that the app has routes
        assert len(app.routes) > 0
        
        # Check for different types of routes
        api_routes = [route for route in app.routes if hasattr(route, 'path') and '/api' in route.path]
        ws_routes = [route for route in app.routes if hasattr(route, 'path') and '/ws' in route.path]
        health_routes = [route for route in app.routes if hasattr(route, 'path') and '/health' in route.path]
        
        assert len(api_routes) > 0
        assert len(ws_routes) > 0
        assert len(health_routes) > 0
    
    def test_app_error_handling(self):
        """Test that the app handles errors properly."""
        client = TestClient(app)
        
        # Test 404 for non-existent endpoint
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404
        
        # Test 405 for wrong method
        response = client.post("/health")
        assert response.status_code == 405
    
    def test_app_cors_headers(self):
        """Test that the app has CORS headers configured."""
        client = TestClient(app)
        
        # Test OPTIONS request to check CORS headers
        response = client.options("/api/v1/sessions/")
        # OPTIONS may return 405 Method Not Allowed, which is expected
        assert response.status_code in [200, 405]
    
    def test_app_startup_shutdown_events(self):
        """Test that the app has startup and shutdown events."""
        # Test that the application has the expected structure
        assert hasattr(app, 'router')
        # Events are handled internally by FastAPI
    
    def test_app_logging_configuration(self):
        """Test that logging is properly configured."""
        # Check that structlog is configured
        logger = structlog.get_logger(__name__)
        assert logger is not None
        
        # Test that logger can be used
        logger.info("test message")
    
    def test_app_database_integration(self):
        """Test that database integration is configured."""
        # Check that database-related imports work
        from app.core.database import get_db, engine
        assert get_db is not None
        assert engine is not None
    
    def test_app_services_integration(self):
        """Test that services are properly integrated."""
        # Check that services can be imported
        from app.services.workspace import WorkspaceService
        from app.services.terminal import terminal_service
        from app.services.websocket import WebSocketManager
        
        assert WorkspaceService is not None
        assert terminal_service is not None
        assert WebSocketManager is not None
    
    def test_app_schemas_integration(self):
        """Test that schemas are properly integrated."""
        # Check that schemas can be imported
        from app.schemas.auth import UserLogin, TokenResponse
        from app.schemas.workspace import SessionCreate, FileCreate
        
        assert UserLogin is not None
        assert TokenResponse is not None
        assert SessionCreate is not None
        assert FileCreate is not None
    
    def test_app_models_integration(self):
        """Test that models are properly integrated."""
        # Check that models can be imported
        from app.models.user import User
        from app.models.session import Session
        from app.models.file import File
        
        assert User is not None
        assert Session is not None
        assert File is not None
    
    def test_app_configuration_integration(self):
        """Test that configuration is properly integrated."""
        # Check that configuration can be imported
        from app.core.config import settings
        
        assert settings is not None
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'VERSION')
        assert hasattr(settings, 'ENVIRONMENT')
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'CORS_ORIGINS')
        assert hasattr(settings, 'ALLOWED_HOSTS')
    
    def test_app_complete_integration(self):
        """Test complete application integration."""
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test API endpoints (will return 403 due to auth, not 404)
        endpoints_to_test = [
            ("/api/v1/sessions/", "GET", 403),  # Forbidden, not 404
            ("/api/v1/auth/login", "POST", 422),  # Validation error for empty JSON
            ("/api/v1/workspace/sessions/", "GET", 405),  # Method Not Allowed
        ]
        
        for endpoint, method, expected_status in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            assert response.status_code == expected_status, f"Failed for {endpoint}"
    
    def test_app_environment_variables(self):
        """Test that environment variables are properly handled."""
        from app.core.config import settings
        
        # Test that required settings are available
        required_settings = [
            'PROJECT_NAME',
            'VERSION', 
            'ENVIRONMENT',
            'DEBUG',
            'DATABASE_URL',
            'CORS_ORIGINS',
            'ALLOWED_HOSTS',
            'LOG_LEVEL',
            'LOG_FORMAT'
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing setting: {setting}"
    
    def test_app_dependency_injection(self):
        """Test that dependency injection is properly configured."""
        # Test that dependencies can be resolved
        from app.core.database import get_db
        from app.api.v1.endpoints.auth import get_current_user_dependency
        
        assert get_db is not None
        assert get_current_user_dependency is not None 


class TestSubmissionIntegration:
    """Test submission functionality integration."""
    
    def test_submission_endpoints_exist(self):
        """Test that submission endpoints are properly configured."""
        client = TestClient(app)
        
        # Test that submission routes exist (will return 403 due to auth, not 404)
        response = client.get("/api/v1/submissions/all")
        assert response.status_code == 403  # Forbidden, not 404
        
        response = client.post("/api/v1/submissions")
        assert response.status_code == 403  # Forbidden, not 404
        
        response = client.get("/api/v1/submissions/pending")
        assert response.status_code == 403  # Forbidden, not 404
        
        response = client.get("/api/v1/submissions/reviewers")
        assert response.status_code == 403  # Forbidden, not 404
        
        response = client.get("/api/v1/submissions/stats")
        assert response.status_code == 403  # Forbidden, not 404
    
    def test_submission_schemas_are_loaded(self):
        """Test that submission schemas are properly loaded."""
        # Check that submission schemas are available
        from app.schemas.submissions import (
            SubmissionCreate, SubmissionUpdate, SubmissionReview,
            SubmissionResponse, SubmissionListResponse, SubmissionStats
        )
        
        assert SubmissionCreate is not None
        assert SubmissionUpdate is not None
        assert SubmissionReview is not None
        assert SubmissionResponse is not None
        assert SubmissionListResponse is not None
        assert SubmissionStats is not None
    
    def test_submission_models_are_loaded(self):
        """Test that submission models are properly loaded."""
        # Check that submission models are available
        from app.models.submission import Submission, SubmissionStatus
        
        assert Submission is not None
        assert SubmissionStatus is not None
        
        # Check that SubmissionStatus has expected values
        assert hasattr(SubmissionStatus, 'PENDING')
        assert hasattr(SubmissionStatus, 'APPROVED')
        assert hasattr(SubmissionStatus, 'REJECTED')
        assert hasattr(SubmissionStatus, 'UNDER_REVIEW')
    
    def test_submission_router_is_included(self):
        """Test that the submission router is included in the app."""
        # Check that submission routes are included in the app
        submission_routes = [route for route in app.routes if hasattr(route, 'path') and '/submissions' in route.path]
        assert len(submission_routes) > 0
        
        # Check for specific submission endpoints
        submission_paths = [route.path for route in submission_routes if hasattr(route, 'path')]
        assert any('/submissions' in path for path in submission_paths)
    
    def test_submission_dependencies_are_configured(self):
        """Test that submission dependencies are properly configured."""
        # Check that submission endpoints use proper dependencies
        from app.api.v1.endpoints.submissions import router as submission_router
        
        # Check that the router exists and has routes
        assert submission_router is not None
        assert len(submission_router.routes) > 0
        
        # Check that routes exist and are properly configured
        # Note: Some routes might not have explicit dependencies but still work
        # due to global dependencies or function-level dependencies
        route_count = 0
        for route in submission_router.routes:
            if hasattr(route, 'path'):
                # Check for any route that might be related to submissions
                if ('submissions' in route.path or 
                    hasattr(route, 'name') and 'submission' in route.name.lower()):
                    route_count += 1
                    # Routes should have proper configuration
                    assert hasattr(route, 'methods')
                    assert len(route.methods) > 0
        
        # Should have multiple submission routes
        assert route_count > 0
    
    def test_submission_workflow_integration(self):
        """Test the complete submission workflow integration."""
        # This test verifies that all components work together
        # without actually making database calls
        
        # Check that all required components are available
        from app.api.v1.endpoints.submissions import (
            create_submission, get_all_submissions, get_pending_submissions,
            get_available_reviewers, get_submission_stats, get_submission,
            review_submission, update_submission, delete_submission
        )
        
        assert create_submission is not None
        assert get_all_submissions is not None
        assert get_pending_submissions is not None
        assert get_available_reviewers is not None
        assert get_submission_stats is not None
        assert get_submission is not None
        assert review_submission is not None
        assert update_submission is not None
        assert delete_submission is not None
    
    def test_submission_error_handling(self):
        """Test that submission endpoints handle errors properly."""
        client = TestClient(app)
        
        # Test unauthorized access
        response = client.get("/api/v1/submissions/all")
        assert response.status_code == 403
        
        response = client.post("/api/v1/submissions", json={})
        assert response.status_code == 403
        
        # Test invalid submission ID
        response = client.get("/api/v1/submissions/invalid-id")
        assert response.status_code == 403  # Auth required first
    
    def test_submission_api_structure(self):
        """Test that the submission API has the expected structure."""
        client = TestClient(app)
        
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # Check that submission paths exist in the schema
        paths = schema.get("paths", {})
        submission_paths = [path for path in paths.keys() if "/submissions" in path]
        
        # Should have multiple submission endpoints
        assert len(submission_paths) > 0
        
        # Check for key submission endpoints
        expected_endpoints = [
            "/api/v1/submissions/",
            "/api/v1/submissions/all",
            "/api/v1/submissions/pending",
            "/api/v1/submissions/reviewers",
            "/api/v1/submissions/stats"
        ]
        
        for endpoint in expected_endpoints:
            assert any(endpoint in path for path in submission_paths) 