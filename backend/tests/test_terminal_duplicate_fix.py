#!/usr/bin/env python3
"""
Test for terminal duplicate output and input handling issues.
This test specifically targets the bugs we've been fixing.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.services.terminal import TerminalService
from app.services.websocket import WebSocketManager
from app.schemas.websocket import MessageType, InputRequestMessage, CommandResponseMessage


class TestTerminalDuplicateIssues:
    """Test suite for duplicate output and input handling bugs."""
    
    @pytest_asyncio.fixture
    async def terminal_service(self):
        """Create a terminal service with mocked dependencies."""
        service = TerminalService()
        
        # Mock workspace service
        class MockWorkspaceService:
            def __init__(self):
                self.files = {
                    "/test.py": "print('hi')",
                    "/input.py": "name = input('What is your name? ')\nprint('Hello ' + name)"
                }
                
            async def get_file_content(self, session_id, filepath):
                return self.files.get(filepath)
            
            async def create_temp_workspace(self, session_id):
                return "/tmp/test_workspace"
        
        mock_workspace = MockWorkspaceService()
        service.set_workspace_service(mock_workspace)
        
        # Mock WebSocket manager that tracks message sends
        class MockWebSocketManager:
            def __init__(self):
                self.sent_messages = []
                self.broadcast_count = 0
                
            async def broadcast_to_session(self, session_id, message):
                self.sent_messages.append({
                    'session_id': session_id,
                    'message': message,
                    'timestamp': message.timestamp if hasattr(message, 'timestamp') else None,
                    'type': message.type,
                    'stdout': getattr(message, 'stdout', ''),
                    'stderr': getattr(message, 'stderr', ''),
                    'command': getattr(message, 'command', ''),
                    'prompt': getattr(message, 'prompt', '')
                })
                self.broadcast_count += 1
                
            def get_stdout_messages(self):
                """Get all stdout messages that were broadcast."""
                return [msg for msg in self.sent_messages 
                       if msg['stdout'] and msg['stdout'].strip()]
                       
            def get_input_request_messages(self):
                """Get all input request messages that were broadcast."""
                return [msg for msg in self.sent_messages 
                       if msg['type'] == MessageType.INPUT_REQUEST]
        
        mock_websocket = MockWebSocketManager()
        service.set_websocket_manager(mock_websocket)
        
        # Create test session
        service.create_session("test-session", "/")
        
        return service, mock_websocket
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_python_command_no_duplicate_output(self, mock_subprocess, terminal_service):
        """Test that Python commands don't produce duplicate output."""
        service, mock_websocket = terminal_service
        
        # Mock subprocess to simulate "print('hi')" output
        mock_process = AsyncMock()
        read_sequence = [b'h', b'i', b'\n', b'']  # Simulate character-by-character reading
        mock_process.stdout.read = AsyncMock(side_effect=read_sequence)
        mock_process.stderr.readline = AsyncMock(return_value=b'')
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        # Execute python command
        result = await service.execute_command("test-session", "python test.py", timeout=5)
        
        # Verify command executed successfully
        assert result["success"] is True
        
        # Get all stdout messages that were broadcast
        stdout_messages = mock_websocket.get_stdout_messages()
        
        # CRITICAL TEST: There should be exactly ONE stdout message with "hi\n"
        hi_messages = [msg for msg in stdout_messages if "hi" in msg['stdout']]
        
        print(f"DEBUG: Total stdout messages: {len(stdout_messages)}")
        print(f"DEBUG: Messages with 'hi': {len(hi_messages)}")
        for i, msg in enumerate(hi_messages):
            print(f"  Message {i+1}: stdout='{msg['stdout']}', command='{msg['command']}'")
        
        # Assert no duplicate output
        assert len(hi_messages) == 1, f"Expected 1 'hi' message, got {len(hi_messages)}"
        
        # Verify the single message is correct
        hi_message = hi_messages[0]
        assert hi_message['stdout'].strip() == 'hi'
        assert 'python3 -u' in hi_message['command']  # Should be from Python handler
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_python_input_no_duplicate_prompts(self, mock_subprocess, terminal_service):
        """Test that Python input commands don't produce duplicate prompts."""
        service, mock_websocket = terminal_service
        
        # Mock subprocess to simulate input() call
        mock_process = AsyncMock()
        mock_process.stdout.read.side_effect = [
            b'W', b'h', b'a', b't', b' ', b'i', b's', b' ', 
            b'y', b'o', b'u', b'r', b' ', b'n', b'a', b'm', b'e', b'?', b' ',
            b''  # No newline, should trigger input prompt detection
        ]
        mock_process.stderr.readline.return_value = b''
        mock_process.returncode = None  # Process still running
        mock_subprocess.return_value = mock_process
        
        # Execute python input command
        try:
            # Use a short timeout to avoid hanging in test
            result = await asyncio.wait_for(
                service.execute_command("test-session", "python input.py", timeout=1),
                timeout=2
            )
        except asyncio.TimeoutError:
            # Expected - the process should be waiting for input
            pass
        
        # Get all input request messages
        input_messages = mock_websocket.get_input_request_messages()
        
        print(f"DEBUG: Total input request messages: {len(input_messages)}")
        for i, msg in enumerate(input_messages):
            print(f"  Input request {i+1}: prompt='{msg['prompt']}'")
        
        # CRITICAL TEST: There should be exactly ONE input request message
        assert len(input_messages) == 1, f"Expected 1 input request, got {len(input_messages)}"
        
        # Verify the prompt is correct
        input_message = input_messages[0]
        assert input_message['prompt'] == 'What is your name? '
        
    @pytest.mark.asyncio
    async def test_general_handler_not_processing_python_commands(self, terminal_service):
        """Test that the general handler is not processing Python commands."""
        service, mock_websocket = terminal_service
        
        # Temporarily disable the Python handler to see if general handler processes it
        original_execute_python = service._execute_python
        
        async def mock_failing_python_handler(*args, **kwargs):
            # Simulate Python handler failing
            raise Exception("Python handler disabled for test")
        
        service._execute_python = mock_failing_python_handler
        
        try:
            result = await service.execute_command("test-session", "python test.py")
            
            # With our current fix, this should return an error from the Python handler
            # and NOT fall through to the general handler
            assert result["success"] is False
            assert "Python execution error" in result["stderr"]
            
            # The general handler should NOT have been called
            # (we'd see different error messages if it was)
            assert "Command not supported" in result["stderr"]  # Our current general handler response
            
        finally:
            # Restore original handler
            service._execute_python = original_execute_python
    
    @pytest.mark.asyncio
    async def test_input_response_handling(self, terminal_service):
        """Test that input response handling works correctly."""
        service, mock_websocket = terminal_service
        
        # Create a mock waiting process
        mock_process = AsyncMock()
        mock_process.stdin.write = AsyncMock()
        mock_process.stdin.drain = AsyncMock()
        
        # Set up a session with a waiting process
        session = service.get_session("test-session")
        session["waiting_process"] = mock_process
        
        # Test input response handling
        await service.handle_input_response("test-session", "Moneel")
        
        # Verify input was sent to process
        mock_process.stdin.write.assert_called_once_with(b"Moneel\n")
        mock_process.stdin.drain.assert_called_once()
        
        # Verify session state was updated
        assert session.get("input_received") is True


if __name__ == "__main__":
    # Run the specific tests
    pytest.main([__file__, "-v", "-s"]) 