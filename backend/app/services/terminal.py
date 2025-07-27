"""
AfterIDE - Terminal Service

Handles terminal command execution, security filtering, and terminal management.
"""

import asyncio
import subprocess
import shlex
import os
import structlog
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tempfile
import json
from pathlib import Path

logger = structlog.get_logger(__name__)


class TerminalService:
    """Manages terminal sessions and command execution."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.command_history: Dict[str, List[str]] = {}
        self.working_directories: Dict[str, str] = {}
        
        # Get the workspace directory (relative to the backend)
        self.base_workspace = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'workspace')
        
        # Security: Allowed commands
        self.allowed_commands = {
            'ls', 'cat', 'pwd', 'echo', 'clear', 'python', 'python3', 'help',
            'head', 'tail', 'grep', 'find', 'wc', 'sort', 'uniq',
            'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'rm',
            'cd', 'whoami', 'date', 'ps', 'top', 'htop',
            'git', 'npm', 'node', 'pip', 'pip3'
        }
        
        # Security: Dangerous commands to block
        self.blocked_commands = {
            'sudo', 'su', 'rm -rf /', 'dd', 'mkfs', 'fdisk',
            'shutdown', 'reboot', 'halt', 'poweroff',
            'chmod 777', 'chown root', 'passwd'
        }
        
        # Security: Blocked patterns
        self.blocked_patterns = [
            r'sudo\s+',
            r'su\s+',
            r'rm\s+-rf\s+/',
            r'dd\s+if=',
            r'mkfs\s+',
            r'fdisk\s+',
            r'shutdown\s+',
            r'reboot\s+',
            r'halt\s+',
            r'poweroff\s+',
            r'chmod\s+777',
            r'chown\s+root',
            r'passwd\s+'
        ]
    
    def create_session(self, session_id: str, working_directory: str = None) -> Dict[str, Any]:
        """Create a new terminal session."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Use default workspace if not specified
        if working_directory is None:
            working_directory = self.base_workspace
        
        # Ensure working directory exists
        os.makedirs(working_directory, exist_ok=True)
        
        session = {
            "id": session_id,
            "working_directory": working_directory,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "command_count": 0,
            "is_active": True
        }
        
        self.sessions[session_id] = session
        self.command_history[session_id] = []
        self.working_directories[session_id] = working_directory
        
        logger.info(
            "Terminal session created",
            session_id=session_id,
            working_directory=working_directory
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get terminal session information."""
        return self.sessions.get(session_id)
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate command for security.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for empty command
        if not command.strip():
            return False, "Empty command"
        
        # Split command into parts
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Invalid command format"
            
            base_command = parts[0].lower()
            
            # Check blocked commands
            if base_command in self.blocked_commands:
                return False, f"Command '{base_command}' is not allowed"
            
            # Check blocked patterns
            import re
            for pattern in self.blocked_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Command pattern is not allowed"
            
            # Check if command is in allowed list (for basic commands)
            if base_command not in self.allowed_commands:
                # Allow some commands that might not be in the basic list
                # but are generally safe
                if base_command.startswith('./') or base_command.startswith('/'):
                    return False, f"Executing files is not allowed"
                
                # For now, allow unknown commands but log them
                logger.warning(
                    "Unknown command executed",
                    command=command,
                    base_command=base_command
                )
            
            return True, ""
            
        except Exception as e:
            return False, f"Command parsing error: {str(e)}"
    
    async def execute_command(
        self, 
        session_id: str, 
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a command in the terminal session.
        
        Args:
            session_id: Session identifier
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        start_time = datetime.utcnow()
        
        # Validate command
        is_valid, error_msg = self.validate_command(command)
        if not is_valid:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Security error: {error_msg}",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
        
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        # Update session activity
        session["last_activity"] = datetime.utcnow()
        session["command_count"] += 1
        
        # Add to command history
        if session_id not in self.command_history:
            self.command_history[session_id] = []
        self.command_history[session_id].append(command)
        
        # Limit history to last 100 commands
        if len(self.command_history[session_id]) > 100:
            self.command_history[session_id] = self.command_history[session_id][-100:]
        
        working_dir = self.working_directories.get(session_id, self.base_workspace)
        
        try:
            # Handle special commands
            if command.strip() == "clear":
                return {
                    "success": True,
                    "stdout": "\033[2J\033[H",  # Clear screen ANSI code
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
            
            elif command.strip() == "help":
                help_text = """Available commands:

File Operations:
  ls       - List files and directories
  cat      - Display file contents
  mkdir    - Create directory
  touch    - Create empty file
  cp       - Copy files
  mv       - Move/rename files
  rm       - Remove files

Navigation:
  pwd      - Show current working directory
  cd       - Change directory

Code Execution:
  python   - Run Python code

Text Processing:
  grep     - Search text patterns
  find     - Find files
  head     - Display first lines of file
  tail     - Display last lines of file
  wc       - Word count
  sort     - Sort lines
  uniq     - Remove duplicate lines

System Information:
  date     - Show current date/time
  whoami   - Show current user
  ps       - Show processes

Development Tools:
  git      - Git version control
  npm      - Node.js package manager
  node     - Node.js runtime
  pip      - Python package manager

Terminal:
  clear    - Clear terminal screen
  echo     - Display a line of text
  help     - Show this help message

For more information about a command, try: command --help
"""
                return {
                    "success": True,
                    "stdout": help_text,
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
            
            elif command.strip() == "pwd":
                return {
                    "success": True,
                    "stdout": f"{working_dir}\n",
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
            
            elif command.strip() == "ls":
                return await self._execute_ls(working_dir, command)
            
            elif command.strip().startswith("ls "):
                return await self._execute_ls(working_dir, command)
            
            elif command.strip().startswith("cat "):
                return await self._execute_cat(working_dir, command)
            
            elif command.strip().startswith("python ") or command.strip().startswith("python3 "):
                return await self._execute_python(working_dir, command, timeout)
            
            elif command.strip().startswith("cd "):
                return await self._execute_cd(session_id, command)
            
            else:
                # Execute general command
                return await self._execute_general_command(working_dir, command, timeout)
                
        except Exception as e:
            logger.error(
                "Command execution error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "return_code": 1,
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "command": command
            }
    
    async def _execute_ls(self, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute ls command."""
        try:
            # Parse ls command
            parts = shlex.split(command)
            if len(parts) > 1:
                target_path = os.path.join(working_dir, parts[1])
            else:
                target_path = working_dir
            
            if not os.path.exists(target_path):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"ls: cannot access '{parts[1] if len(parts) > 1 else '.'}': No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            items = os.listdir(target_path)
            output = []
            
            for item in sorted(items):
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    output.append(f"\033[34m{item}/\033[0m")  # Blue for directories
                elif os.path.islink(item_path):
                    output.append(f"\033[36m{item}@\033[0m")  # Cyan for links
                elif os.access(item_path, os.X_OK):
                    output.append(f"\033[32m{item}*\033[0m")  # Green for executables
                else:
                    output.append(item)
            
            return {
                "success": True,
                "stdout": "  ".join(output) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"ls error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_cat(self, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute cat command."""
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cat: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            file_path = os.path.join(working_dir, parts[1])
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cat: {parts[1]}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            if not os.path.isfile(file_path):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cat: {parts[1]}: Is a directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "stdout": content,
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"cat error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_python(self, working_dir: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute Python command."""
        try:
            # Create temporary file for Python code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=working_dir) as f:
                # Extract Python code from command
                if command.startswith('python '):
                    python_code = command[7:]  # Remove 'python ' prefix
                elif command.startswith('python3 '):
                    python_code = command[8:]  # Remove 'python3 ' prefix
                else:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": "python: invalid command format\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
                
                if not python_code.strip():
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": "python: missing code\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
                
                # Remove outer quotes if present
                if (python_code.startswith('"') and python_code.endswith('"')) or \
                   (python_code.startswith("'") and python_code.endswith("'")):
                    python_code = python_code[1:-1]
                
                f.write(python_code)
                temp_file = f.name
            
            try:
                # Execute Python code
                process = await asyncio.create_subprocess_exec(
                    "python3", temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8'),
                    "return_code": process.returncode,
                    "execution_time": 0.0,
                    "command": command
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except asyncio.TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds\n",
                "return_code": 1,
                "execution_time": timeout,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Python execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_cd(self, session_id: str, command: str) -> Dict[str, Any]:
        """Execute cd command."""
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cd: missing directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            current_dir = self.working_directories.get(session_id, self.base_workspace)
            target_dir = parts[1]
            
            if target_dir == "~":
                target_dir = self.base_workspace
            elif not target_dir.startswith("/"):
                target_dir = os.path.join(current_dir, target_dir)
            
            # Resolve path
            target_dir = os.path.abspath(target_dir)
            
            # Security: Ensure we stay within workspace
            if not target_dir.startswith(self.base_workspace):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cd: Access denied - cannot navigate outside workspace\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            if not os.path.exists(target_dir):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cd: {parts[1]}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            if not os.path.isdir(target_dir):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cd: {parts[1]}: Not a directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Update working directory
            self.working_directories[session_id] = target_dir
            
            return {
                "success": True,
                "stdout": "",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"cd error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_general_command(self, working_dir: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute general command using subprocess."""
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "return_code": process.returncode,
                "execution_time": 0.0,
                "command": command
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds\n",
                "return_code": 1,
                "execution_time": timeout,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    def get_command_history(self, session_id: str, limit: int = 50) -> List[str]:
        """Get command history for a session."""
        history = self.command_history.get(session_id, [])
        return history[-limit:] if limit > 0 else history
    
    def get_working_directory(self, session_id: str) -> str:
        """Get current working directory for a session."""
        return self.working_directories.get(session_id, self.base_workspace)
    
    def cleanup_session(self, session_id: str):
        """Clean up a terminal session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.command_history:
            del self.command_history[session_id]
        if session_id in self.working_directories:
            del self.working_directories[session_id]
        
        logger.info("Terminal session cleaned up", session_id=session_id)


# Global terminal service instance
terminal_service = TerminalService() 