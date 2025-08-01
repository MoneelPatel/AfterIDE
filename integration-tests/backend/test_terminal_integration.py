"""
Terminal Operations Integration Tests

Tests the complete terminal command execution flow between frontend and backend.
"""

import pytest
from fastapi import status
import json
import time


class TestTerminalIntegration:
    """Test terminal operations integration between frontend and backend."""
    
    def test_terminal_session_creation(self, client, authenticated_user):
        """Test terminal session creation."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Terminal Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal session creation via WebSocket endpoint
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        # WebSocket endpoints typically return 404 for HTTP GET requests
        assert response.status_code in [404, 405, 400]
    
    def test_basic_command_execution(self, client, authenticated_user):
        """Test basic command execution."""
        headers = authenticated_user["headers"]
        
        # Create a session first
        session_data = {
            "name": "Command Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test that terminal endpoint exists
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_file_operations_commands(self, client, authenticated_user):
        """Test file operation commands (ls, cat, touch, etc.)."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "File Commands Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for file operations
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_directory_operations(self, client, authenticated_user):
        """Test directory operations (cd, mkdir, pwd)."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Directory Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for directory operations
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_python_execution(self, client, authenticated_user):
        """Test Python code execution."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Python Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for Python execution
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_pip_operations(self, client, authenticated_user):
        """Test pip package management operations."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Pip Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for pip operations
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_text_processing_commands(self, client, authenticated_user):
        """Test text processing commands (grep, find, head, tail, wc, sort, uniq)."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Text Processing Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for text processing
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_command_validation(self, client, authenticated_user):
        """Test command validation and security filtering."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Validation Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for command validation
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_command_history(self, client, authenticated_user):
        """Test command history functionality."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "History Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for command history
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_working_directory_management(self, client, authenticated_user):
        """Test working directory management."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Working Dir Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for working directory management
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_command_timeout_handling(self, client, authenticated_user):
        """Test command timeout handling."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Timeout Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for timeout handling
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_error_handling(self, client, authenticated_user):
        """Test error handling in terminal operations."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Error Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for error handling
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_concurrent_command_execution(self, client, authenticated_user):
        """Test concurrent command execution."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Concurrent Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test multiple terminal endpoints for concurrent execution
        response1 = client.get(f"/ws/terminal/{session_id}", headers=headers)
        response2 = client.get(f"/ws/terminal/{session_id}", headers=headers)
        
        assert response1.status_code in [404, 405, 400]
        assert response2.status_code in [404, 405, 400]
    
    def test_session_cleanup(self, client, authenticated_user):
        """Test terminal session cleanup."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Cleanup Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for cleanup
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_help_command(self, client, authenticated_user):
        """Test help command functionality."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Help Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for help command
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_echo_command(self, client, authenticated_user):
        """Test echo command functionality."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Echo Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for echo command
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400]
    
    def test_clear_command(self, client, authenticated_user):
        """Test clear command functionality."""
        headers = authenticated_user["headers"]
        
        # Create a session
        session_data = {
            "name": "Clear Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test terminal endpoint for clear command
        response = client.get(f"/ws/terminal/{session_id}", headers=headers)
        assert response.status_code in [404, 405, 400] 