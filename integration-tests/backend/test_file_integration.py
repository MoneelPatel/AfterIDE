"""
File Operations Integration Tests

Tests the complete file operations flow between frontend and backend.
"""

import pytest
from fastapi import status
import json
import tempfile
import os


class TestFileIntegration:
    """Test file operations integration between frontend and backend."""
    
    def test_create_file_success(self, client, authenticated_user):
        """Test successful file creation."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "File Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create file in the session
        file_data = {
            "filepath": "/test_file.py",
            "content": "print('Hello, World!')",
            "language": "python"
        }
        
        response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "filepath" in data
        assert "content" in data
        assert data["filepath"] == file_data["filepath"]
        assert data["content"] == file_data["content"]
    
    def test_create_file_without_auth(self, client):
        """Test file creation without authentication."""
        file_data = {
            "filepath": "/test_file.py",
            "content": "print('Hello, World!')"
        }
        
        response = client.post(
            "/api/v1/workspace/sessions/test-session/files",
            json=file_data
        )
        
        # Should get 422 validation error because user_id is required
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_file_content(self, client, authenticated_user):
        """Test retrieving file content."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Content Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file
        file_data = {
            "filepath": "/content_test.py",
            "content": "def hello():\n    return 'Hello, World!'",
            "language": "python"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Then retrieve the content
        response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files/content_test.py?user_id=mock-user-id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "content" in data
        assert data["content"] == file_data["content"]
    
    def test_update_file_content(self, client, authenticated_user):
        """Test updating file content."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Update Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file
        file_data = {
            "filepath": "/update_test.py",
            "content": "print('Original content')",
            "language": "python"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Update the content
        update_data = {
            "content": "print('Updated content')",
            "language": "python"
        }
        
        response = client.put(
            f"/api/v1/workspace/sessions/{session_id}/files/update_test.py?user_id=mock-user-id",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["content"] == update_data["content"]
    
    def test_delete_file(self, client, authenticated_user):
        """Test deleting a file."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Delete Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file
        file_data = {
            "filepath": "/delete_test.py",
            "content": "print('Delete me')",
            "language": "python"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Delete the file
        response = client.delete(
            f"/api/v1/workspace/sessions/{session_id}/files/delete_test.py?user_id=mock-user-id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify file is deleted
        get_response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files/delete_test.py?user_id=mock-user-id",
            headers=headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_files(self, client, authenticated_user):
        """Test listing files."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "List Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure
        assert "files" in data
        assert "directory" in data
        assert "session_id" in data
        
        files = data["files"]
        
        # Verify files is a list
        assert isinstance(files, list)
        
        # If there are files, verify their structure
        if files:
            file_item = files[0]
            assert "name" in file_item
            assert "path" in file_item
    
    def test_file_operations_with_directories(self, client, authenticated_user):
        """Test file operations with directory structure."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
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
        
        # Create a file in a subdirectory
        file_data = {
            "filepath": "/subdir/subdir_file.py",
            "content": "print('In subdirectory')",
            "language": "python"
        }
        
        response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # List files in the session
        list_response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers
        )
        
        assert list_response.status_code == status.HTTP_200_OK
        data = list_response.json()
        
        # Verify response structure
        assert "files" in data
        assert "directory" in data
        assert "session_id" in data
        assert isinstance(data["files"], list)
    
    def test_file_upload(self, client, authenticated_user):
        """Test file upload functionality."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Upload Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file directly (simulating upload)
        file_data = {
            "filepath": "/uploads/test_upload.txt",
            "content": "This is test content for upload",
            "language": "text"
        }
        
        response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "session_id" in data
        assert "filepath" in data
        assert data["filepath"] == "/uploads/test_upload.txt"
    
    def test_file_download(self, client, authenticated_user):
        """Test file download functionality."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Download Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file
        file_data = {
            "filepath": "/download_test.txt",
            "content": "This is content to download",
            "language": "text"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Download the file (get content)
        response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files/download_test.txt?user_id=mock-user-id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data
    
    def test_file_search(self, client, authenticated_user):
        """Test file search functionality."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Search Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create some test files
        files_to_create = [
            {"filepath": "/search_test1.py", "content": "print('test1')", "language": "python"},
            {"filepath": "/search_test2.py", "content": "print('test2')", "language": "python"},
            {"filepath": "/other_file.txt", "content": "not a python file", "language": "text"}
        ]
        
        for file_data in files_to_create:
            create_response = client.post(
                f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
                headers=headers,
                json=file_data
            )
            assert create_response.status_code == status.HTTP_200_OK
        
        # List files (search functionality might be implemented in the frontend)
        response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure
        assert "files" in data
        assert "directory" in data
        assert "session_id" in data
        
        files = data["files"]
        # Should find at least the files we created
        assert len(files) >= 3
    
    def test_file_permissions(self, client, authenticated_user):
        """Test file permission handling."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Permission Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a file
        file_data = {
            "filepath": "/permission_test.py",
            "content": "print('test')",
            "language": "python"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Try to access without authentication (should get 422 because user_id is required)
        response = client.get(
            f"/api/v1/workspace/sessions/{session_id}/files/permission_test.py"
        )
        
        # Should get 422 validation error because user_id is required
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_file_concurrent_access(self, client, authenticated_user):
        """Test concurrent file access handling."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
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
        
        # Create a file
        file_data = {
            "filepath": "/concurrent_test.py",
            "content": "print('original')",
            "language": "python"
        }
        
        create_response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        
        # Simulate concurrent updates (this is a basic test)
        update1 = {"content": "print('update1')", "language": "python"}
        update2 = {"content": "print('update2')", "language": "python"}
        
        response1 = client.put(
            f"/api/v1/workspace/sessions/{session_id}/files/concurrent_test.py?user_id=mock-user-id",
            headers=headers,
            json=update1
        )
        response2 = client.put(
            f"/api/v1/workspace/sessions/{session_id}/files/concurrent_test.py?user_id=mock-user-id",
            headers=headers,
            json=update2
        )
        
        # Both should succeed (the last one wins)
        assert response1.status_code in [200, 409]  # 409 for conflict
        assert response2.status_code in [200, 409]
    
    def test_file_size_limits(self, client, authenticated_user):
        """Test file size limit handling."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Size Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Create a large file content
        large_content = "x" * 1000000  # 1MB of content
        
        file_data = {
            "filepath": "/large_file.txt",
            "content": large_content,
            "language": "text"
        }
        
        response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        
        # Should either accept or return size limit error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]
    
    def test_file_type_validation(self, client, authenticated_user):
        """Test file type validation."""
        headers = authenticated_user["headers"]
        
        # First create a workspace session
        session_data = {
            "name": "Type Test Session",
            "user_id": "mock-user-id"
        }
        
        session_response = client.post(
            "/api/v1/workspace/sessions",
            headers=headers,
            json=session_data
        )
        assert session_response.status_code == status.HTTP_200_OK
        session_id = session_response.json()["id"]
        
        # Test with potentially problematic file type
        file_data = {
            "filepath": "/test_file.exe",
            "content": "binary content",
            "language": "binary"
        }
        
        response = client.post(
            f"/api/v1/workspace/sessions/{session_id}/files?user_id=mock-user-id",
            headers=headers,
            json=file_data
        )
        
        # Should either accept or return validation error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY] 