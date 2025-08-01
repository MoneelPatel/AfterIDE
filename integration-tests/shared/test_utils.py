"""
Shared Test Utilities

Common utilities and helpers for integration tests.
"""

import asyncio
import json
import time
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path


class TestDataManager:
    """Manages test data and temporary files for integration tests."""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_temp_file(self, content: str, suffix: str = ".txt") -> str:
        """Create a temporary file with given content."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_temp_directory(self) -> str:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary files and directories."""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except OSError:
                pass


class WebSocketTestHelper:
    """Helper for WebSocket testing."""
    
    @staticmethod
    async def wait_for_websocket_message(websocket, timeout: float = 5.0) -> Dict[str, Any]:
        """Wait for a WebSocket message with timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                return json.loads(message)
            except asyncio.TimeoutError:
                continue
        raise TimeoutError("No WebSocket message received within timeout")
    
    @staticmethod
    async def send_websocket_message(websocket, message: Dict[str, Any]):
        """Send a JSON message through WebSocket."""
        await websocket.send_text(json.dumps(message))


class APITestHelper:
    """Helper for API testing."""
    
    @staticmethod
    def create_auth_headers(token: str) -> Dict[str, str]:
        """Create authentication headers."""
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def assert_response_structure(response_data: Dict[str, Any], required_fields: list):
        """Assert that response has required fields."""
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], expected_status: int = None):
        """Assert that response is an error response."""
        assert "detail" in response_data or "error" in response_data, "Error response should contain detail or error field"


class FileTestHelper:
    """Helper for file operation testing."""
    
    @staticmethod
    def create_test_file_structure(base_path: str) -> Dict[str, str]:
        """Create a test file structure."""
        files = {}
        
        # Create some test files
        test_files = {
            "main.py": 'print("Hello, World!")\n',
            "config.json": '{"test": true, "version": "1.0.0"}\n',
            "README.md": '# Test Project\n\nThis is a test project.\n',
            "data/sample.txt": "Sample data file\n",
            "src/utils.py": 'def helper():\n    return "helper function"\n'
        }
        
        for file_path, content in test_files.items():
            full_path = os.path.join(base_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            files[file_path] = full_path
        
        return files
    
    @staticmethod
    def cleanup_test_files(files: Dict[str, str]):
        """Clean up test files."""
        for file_path in files.values():
            try:
                os.unlink(file_path)
            except OSError:
                pass


class SessionTestHelper:
    """Helper for session testing."""
    
    @staticmethod
    def create_test_session_data(name: str = "Test Session", 
                                description: str = "Test session for integration tests",
                                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create test session data."""
        if config is None:
            config = {
                "language": "python",
                "framework": "fastapi",
                "test_mode": True
            }
        
        return {
            "name": name,
            "description": description,
            "config": config
        }


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    @staticmethod
    async def measure_response_time(coroutine, timeout: float = 30.0) -> float:
        """Measure the time taken by a coroutine."""
        start_time = time.time()
        await asyncio.wait_for(coroutine, timeout=timeout)
        end_time = time.time()
        return end_time - start_time
    
    @staticmethod
    def assert_response_time(actual_time: float, expected_max_time: float):
        """Assert that response time is within acceptable limits."""
        assert actual_time <= expected_max_time, f"Response time {actual_time}s exceeded maximum {expected_max_time}s"


class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def generate_user_data(username: str = "testuser") -> Dict[str, str]:
        """Generate mock user data."""
        return {
            "username": username,
            "password": "testpassword123",
            "email": f"{username}@example.com"
        }
    
    @staticmethod
    def generate_file_data(filename: str = "test.py", content: str = "print('test')") -> Dict[str, str]:
        """Generate mock file data."""
        return {
            "filename": filename,
            "content": content,
            "language": "python"
        }
    
    @staticmethod
    def generate_terminal_command(command: str = "echo 'test'") -> Dict[str, str]:
        """Generate mock terminal command."""
        return {
            "command": command,
            "type": "command"
        }


class TestEnvironment:
    """Manage test environment configuration."""
    
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3004")
        self.test_user = os.getenv("TEST_USER", "testuser")
        self.test_password = os.getenv("TEST_PASSWORD", "testpassword123")
        self.test_timeout = float(os.getenv("TEST_TIMEOUT", "30"))
    
    def get_backend_api_url(self, endpoint: str) -> str:
        """Get full backend API URL."""
        return f"{self.backend_url}/api/v1{endpoint}"
    
    def get_frontend_url(self, path: str = "") -> str:
        """Get full frontend URL."""
        return f"{self.frontend_url}{path}"


# Global test environment instance
test_env = TestEnvironment() 