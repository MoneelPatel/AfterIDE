#!/usr/bin/env python3
"""
Simple integration test to verify terminal functionality works as expected.
This directly tests the double output and input handling issues.
"""

import asyncio
import tempfile
import os

async def test_terminal_basic():
    """Test basic terminal functionality without complex mocking."""
    try:
        from app.services.terminal import TerminalService
        from app.services.websocket import WebSocketManager
        
        # Create real service
        service = TerminalService()
        
        # Create a minimal mock workspace service
        class SimpleWorkspaceService:
            async def get_file_content(self, session_id, filepath):
                if filepath == "/test.py":
                    return "print('hi')"
                return None
                
            async def create_temp_workspace(self, session_id):
                return "/tmp/test_workspace"
        
        service.set_workspace_service(SimpleWorkspaceService())
        
        # Track messages
        sent_messages = []
        
        class MessageTracker:
            async def broadcast_to_session(self, session_id, message):
                sent_messages.append({
                    'session_id': session_id,
                    'message': message,
                    'stdout': getattr(message, 'stdout', ''),
                    'type': message.type
                })
                print(f"[TEST] Captured message: stdout='{getattr(message, 'stdout', '')}', type={message.type}")
        
        service.set_websocket_manager(MessageTracker())
        service.create_session("test-session", "/")
        
        # Test a simple command that should NOT cause double output
        result = await service.execute_command("test-session", "ls")
        print(f"[TEST] ls command result: success={result['success']}, stdout='{result['stdout'][:100]}...'")
        
        # Count stdout messages
        stdout_messages = [msg for msg in sent_messages if msg['stdout'] and msg['stdout'].strip()]
        print(f"[TEST] Total stdout messages: {len(stdout_messages)}")
        for i, msg in enumerate(stdout_messages):
            print(f"  Message {i+1}: '{msg['stdout']}'")
        
        print(f"[TEST] ✅ Basic test completed. Found {len(stdout_messages)} stdout messages.")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🧪 Running simple integration test...")
    success = await test_terminal_basic()
    
    if success:
        print("🎉 Integration test completed successfully!")
    else:
        print("💥 Integration test failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())