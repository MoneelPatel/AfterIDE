"""
AfterIDE - Terminal Service

Handles terminal command execution, security filtering, and terminal management.
"""

import asyncio
import subprocess
import shlex
import os
import time
import structlog
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tempfile
import json
from pathlib import Path
from sqlalchemy import select, and_
from app.models.file import File

# WebSocket imports for file system notifications
from app.schemas.websocket import FolderCreatedMessage, MessageType, FileUpdatedMessage, FileDeletedMessage

logger = structlog.get_logger(__name__)


class TerminalService:
    """Manages terminal sessions and command execution."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.command_history: Dict[str, List[str]] = {}
        self.working_directories: Dict[str, str] = {}
        self.workspace_service = None  # Will be set by dependency injection
        self.websocket_manager = None  # Will be set by dependency injection
        
    def set_workspace_service(self, workspace_service):
        """Set the workspace service for database operations."""
        self.workspace_service = workspace_service
    
    def set_websocket_manager(self, websocket_manager):
        """Set the WebSocket manager for file system notifications."""
        self.websocket_manager = websocket_manager
        
    def create_session(self, session_id: str, working_directory: str = None) -> Dict[str, Any]:
        """Create a new terminal session."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Use session root as default working directory
        if working_directory is None:
            working_directory = "/"
        
        session = {
            "id": session_id,
            "working_directory": working_directory,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "command_count": 0,
            "is_active": True,
            "command_history": [] # Initialize command history
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
            return False, "Invalid command format"
        
        # Check for whitespace-only command (this is redundant with the above, but let's be explicit)
        if command.strip() == "":
            return False, "Invalid command format"
        
        # Split command into parts
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Invalid command format"
            
            base_command = parts[0].lower()
            
            # Check for missing arguments for specific commands
            if base_command == "cd" and len(parts) < 2:
                return False, "cd: missing directory"
            elif base_command == "cat" and len(parts) < 2:
                return False, "cat: missing file operand"
            elif base_command == "mkdir" and len(parts) < 2:
                return False, "mkdir: missing operand"
            elif base_command == "touch" and len(parts) < 2:
                return False, "touch: missing file operand"
            elif base_command == "cp" and len(parts) < 3:
                return False, "cp: missing file operand"
            elif base_command == "mv" and len(parts) < 3:
                return False, "mv: missing file operand"
            elif base_command == "rm" and len(parts) < 2:
                return False, "rm: missing file operand"
            elif base_command == "grep" and len(parts) < 2:
                return False, "grep: missing pattern"
            elif base_command == "find" and len(parts) < 2:
                return False, "find: missing path"
            elif base_command == "head" and len(parts) < 2:
                return False, "head: missing file operand"
            elif base_command == "tail" and len(parts) < 2:
                return False, "tail: missing file operand"
            elif base_command == "wc" and len(parts) < 2:
                return False, "wc: missing file operand"
            elif base_command == "sort" and len(parts) < 2:
                return False, "sort: missing file operand"
            elif base_command == "uniq" and len(parts) < 2:
                return False, "uniq: missing file operand"
            
            # Security: Dangerous commands to block
            blocked_commands = {
                'sudo', 'su', 'rm -rf /', 'dd', 'mkfs', 'fdisk',
                'shutdown', 'reboot', 'halt', 'poweroff',
                'chmod 777', 'chown root', 'passwd'
            }
            
            # Security: Blocked patterns
            blocked_patterns = [
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
            
            # Check blocked commands
            if base_command in blocked_commands:
                return False, f"Command '{base_command}' is not allowed"
            
            # Check blocked patterns
            import re
            for pattern in blocked_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Command pattern is not allowed"
            
            # Additional security checks for specific dangerous commands
            if base_command.startswith('mkfs') or base_command.startswith('fdisk') or base_command.startswith('dd'):
                return False, f"Command '{base_command}' is not allowed"
            
            # Security: Block path traversal attempts
            for part in parts[1:]:
                if ".." in part or part.startswith("../"):
                    # Allow 'cd ..' command specifically
                    if base_command == "cd" and part == "..":
                        continue
                    return False, f"Path traversal is not allowed"
            
            # Security: Block file system access outside workspace
            if base_command.startswith('./') or base_command.startswith('/'):
                if not base_command.startswith('/workspace') and base_command != '/':
                    return False, f"Access to files outside workspace is not allowed"
            
            return True, ""
            
        except Exception as e:
            return False, f"Command parsing error: {str(e)}"
    
    async def execute_command(
        self, 
        session_id: str, 
        command: str,
        timeout: int = 30,
        working_directory: str = None
    ) -> Dict[str, Any]:
        """Execute a terminal command."""
        start_time = time.time()
        
        try:
            # Check for simple pipeline (commands connected by |)
            if "|" in command:
                return await self._execute_simple_pipeline(session_id, command, timeout, working_directory)
            
            # Validate command
            is_valid, error_msg = self.validate_command(command)
            if not is_valid:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": error_msg,
                    "return_code": 1,
                    "execution_time": time.time() - start_time,
                    "command": command
                }
            
            # Get or create session
            session = self.get_session(session_id)
            if not session:
                session = self.create_session(session_id, working_directory)
            
            working_dir = working_directory or session.get("working_directory", "/")
            
            # Add to command history
            session["command_history"].append(command)
            if len(session["command_history"]) > 100:
                session["command_history"] = session["command_history"][-100:]
            
            # Also update the global command history
            if session_id not in self.command_history:
                self.command_history[session_id] = []
            self.command_history[session_id].append(command)
            if len(self.command_history[session_id]) > 100:
                self.command_history[session_id] = self.command_history[session_id][-100:]
            
            logger.info("Executing command", session_id=session_id, command=command, working_dir=working_dir)
            
            # Route to appropriate handler
            if command.strip() == "help":
                return await self._execute_help()
            elif command.strip() == "pwd":
                return await self._execute_pwd(session_id, working_dir)
            elif command.strip().startswith("cd "):
                return await self._execute_cd(session_id, command)
            elif command.strip() == "ls" or command.strip().startswith("ls "):
                return await self._execute_ls(session_id, working_dir, command)
            elif command.strip().startswith("cat "):
                return await self._execute_cat(session_id, working_dir, command)
            elif command.strip().startswith("python "):
                return await self._execute_python(session_id, working_dir, command, timeout)
            elif command.strip().startswith("pip "):
                return await self._execute_pip(session_id, working_dir, command, timeout)
            elif command.strip() == "clear":
                return await self._execute_clear()
            elif command.strip().startswith("echo "):
                return await self._execute_echo(command, session_id)
            elif command.strip().startswith("mkdir "):
                return await self._execute_mkdir(session_id, working_dir, command)
            elif command.strip().startswith("touch "):
                return await self._execute_touch(session_id, working_dir, command)
            elif command.strip().startswith("cp "):
                return await self._execute_cp(session_id, working_dir, command)
            elif command.strip().startswith("mv "):
                return await self._execute_mv(session_id, working_dir, command)
            elif command.strip().startswith("rm "):
                return await self._execute_rm(session_id, working_dir, command)
            elif command.strip().startswith("grep "):
                return await self._execute_grep(session_id, working_dir, command)
            elif command.strip().startswith("find "):
                return await self._execute_find(session_id, working_dir, command)
            elif command.strip().startswith("head "):
                return await self._execute_head(session_id, working_dir, command)
            elif command.strip().startswith("tail "):
                return await self._execute_tail(session_id, working_dir, command)
            elif command.strip().startswith("wc "):
                return await self._execute_wc(session_id, working_dir, command)
            elif command.strip().startswith("sort "):
                return await self._execute_sort(session_id, working_dir, command)
            elif command.strip().startswith("uniq "):
                return await self._execute_uniq(session_id, working_dir, command)
            else:
                return await self._execute_general_command(session_id, working_dir, command, timeout)
                
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
                "stderr": f"Command execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": time.time() - start_time,
                "command": command
            }
    
    async def _execute_simple_pipeline(self, session_id: str, command: str, timeout: int, working_directory: str) -> Dict[str, Any]:
        """Execute a simple pipeline like 'sort file | uniq'."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Split by pipe
            parts = command.split('|')
            if len(parts) != 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Only simple pipelines with one pipe are supported\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            cmd1 = parts[0].strip()
            cmd2 = parts[1].strip()
            
            # Execute first command
            result1 = await self.execute_command(session_id, cmd1, timeout, working_directory)
            if not result1["success"]:
                return result1
            
            # Execute second command with stdin from first command
            if cmd2.startswith("uniq"):
                # Handle uniq with stdin
                return await self._execute_uniq_with_stdin(session_id, working_directory, result1["stdout"])
            elif cmd2.startswith("sort"):
                # Handle sort with stdin
                return await self._execute_sort_with_stdin(session_id, working_directory, result1["stdout"])
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Pipeline command '{cmd2}' not supported\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "Pipeline execution error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Pipeline execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_uniq_with_stdin(self, session_id: str, working_dir: str, stdin_data: str) -> Dict[str, Any]:
        """Execute uniq command with stdin data."""
        try:
            # Remove duplicate consecutive lines
            lines = stdin_data.split('\n')
            unique_lines = []
            prev_line = None
            
            for line in lines:
                if line != prev_line:
                    unique_lines.append(line)
                    prev_line = line
            
            return {
                "success": True,
                "stdout": "\n".join(unique_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": "uniq (from pipeline)"
            }
            
        except Exception as e:
            logger.error(
                "uniq with stdin error",
                session_id=session_id,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"uniq: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": "uniq (from pipeline)"
            }
    
    async def _execute_sort_with_stdin(self, session_id: str, working_dir: str, stdin_data: str) -> Dict[str, Any]:
        """Execute sort command with stdin data."""
        try:
            # Sort lines
            lines = stdin_data.split('\n')
            sorted_lines = sorted(lines)
            
            return {
                "success": True,
                "stdout": "\n".join(sorted_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": "sort (from pipeline)"
            }
            
        except Exception as e:
            logger.error(
                "sort with stdin error",
                session_id=session_id,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"sort: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": "sort (from pipeline)"
            }
    
    async def _execute_ls(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute ls command using workspace files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Parse ls command
            parts = shlex.split(command)
            if len(parts) > 1:
                target_path = parts[1]
            else:
                target_path = working_dir
            
            # Get files from workspace
            files = await self.workspace_service.get_workspace_files(session_id, target_path)
            
            # Don't auto-create default files here - let the workspace service handle this
            # This prevents overwriting user files when ls doesn't find files due to timing issues
            
            if not files:
                return {
                    "success": True,
                    "stdout": "\n",
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Format output
            output = []
            for file_info in files:
                if file_info["type"] == "directory":
                    output.append(f"\033[34m{file_info['name']}/\033[0m")  # Blue for directories
                else:
                    output.append(file_info["name"])
            
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
    
    async def _execute_cat(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute cat command using workspace files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
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
            
            # Resolve file path
            filepath = parts[1]
            if not filepath.startswith("/"):
                filepath = os.path.join(working_dir, filepath).replace("\\", "/")
            
            # Get file content from workspace
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cat: {parts[1]}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
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
    
    async def _execute_python(self, session_id: str, working_dir: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute Python command using workspace files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Create temporary workspace for execution
            temp_workspace = await self.workspace_service.create_temp_workspace(session_id)
            
            # Ensure the temp workspace directory exists
            os.makedirs(temp_workspace, exist_ok=True)
            
            # Extract Python code/filename from command
            if command.startswith('python '):
                python_arg = command[7:].strip()  # Remove 'python ' prefix
            elif command.startswith('python3 '):
                python_arg = command[8:].strip()  # Remove 'python3 ' prefix
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "python: invalid command format\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            if not python_arg:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "python: missing code or filename\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Check if argument is a filename that exists in the workspace
            # Handle relative paths based on current working directory
            if python_arg.startswith('/'):
                # Absolute path
                potential_filepath = python_arg
            else:
                # Relative path - join with current working directory
                if working_dir == "/":
                    potential_filepath = f"/{python_arg}"
                else:
                    potential_filepath = f"{working_dir.rstrip('/')}/{python_arg}"
            
            file_content = await self.workspace_service.get_file_content(session_id, potential_filepath)
            
            if file_content is not None:
                # This is a file execution - run the existing file
                # Use the relative path for the temp workspace file
                if python_arg.startswith('/'):
                    file_path = os.path.join(temp_workspace, python_arg.lstrip("/"))
                else:
                    # For relative paths, create the file in the temp workspace maintaining the relative structure
                    if working_dir == "/":
                        file_path = os.path.join(temp_workspace, python_arg)
                    else:
                        # Create the directory structure in temp workspace
                        relative_dir = working_dir.lstrip("/")
                        temp_dir = os.path.join(temp_workspace, relative_dir)
                        os.makedirs(temp_dir, exist_ok=True)
                        file_path = os.path.join(temp_dir, python_arg)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write the file content to the temp workspace
                with open(file_path, 'w') as f:
                    f.write(file_content)
                
                # Execute the Python file
                process = await asyncio.create_subprocess_exec(
                    "python3", file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
                    cwd=temp_workspace
                )
                
                # TODO: Implement proper interactive input handling
                # For now, provide some default input to handle basic input() calls
                # This is a simple workaround - in a full implementation, this would be interactive
                # A proper solution would require:
                # 1. Detecting when the process is waiting for input
                # 2. Sending input_request messages to the frontend
                # 3. Receiving input_response messages from the frontend
                # 4. Sending the input to the process
                default_input = "Test User\n25\nyes\n"  # Name, age, likes Python
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=default_input.encode('utf-8')),
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
            else:
                # This is inline code execution - create temporary file with the code
                # Create temporary file for Python code
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=temp_workspace) as f:
                    # Remove outer quotes if present
                    if (python_arg.startswith('"') and python_arg.endswith('"')) or \
                       (python_arg.startswith("'") and python_arg.endswith("'")):
                        python_arg = python_arg[1:-1]
                    
                    f.write(python_arg)
                    temp_file = f.name
                
                try:
                    # Execute Python code
                    process = await asyncio.create_subprocess_exec(
                        "python3", temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=temp_workspace
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
                "stderr": f"Command execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_cd(self, session_id: str, command: str) -> Dict[str, Any]:
        """Execute cd command."""
        logger.info("CD command received", session_id=session_id, command=command)
        
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                logger.error("CD command missing directory", session_id=session_id)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cd: missing directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            current_dir = self.working_directories.get(session_id, "/")
            target_dir = parts[1]
            logger.info("CD command processing", session_id=session_id, current_dir=current_dir, target_dir=target_dir)
            
            # Handle special cases
            if target_dir == "~":
                target_dir = "/"
            elif target_dir == "..":
                # Go up one directory
                if current_dir != "/":
                    target_dir = "/".join(current_dir.rstrip("/").split("/")[:-1]) or "/"
                else:
                    target_dir = "/"
            elif target_dir == ".":
                # Stay in current directory
                target_dir = current_dir
            elif not target_dir.startswith("/"):
                # Relative path - join with current directory
                if current_dir == "/":
                    target_dir = f"/{target_dir}"
                else:
                    target_dir = f"{current_dir.rstrip('/')}/{target_dir}"
            
            # Normalize the path (remove redundant slashes, etc.)
            target_dir = os.path.normpath(target_dir).replace("\\", "/")
            if not target_dir.startswith("/"):
                target_dir = "/" + target_dir
                
            logger.info("CD normalized target", session_id=session_id, normalized_target=target_dir)
                
            # Security: Ensure we stay within workspace root
            if target_dir != "/" and (".." in target_dir or target_dir.startswith("../")):
                logger.error("CD security violation", session_id=session_id, target_dir=target_dir)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cd: Access denied - cannot navigate outside workspace\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Validate that the directory exists in the workspace
            if self.workspace_service and target_dir != "/":
                logger.info("CD validating directory exists", session_id=session_id, target_dir=target_dir)
                try:
                    # Check if directory exists by looking for files in it or a placeholder
                    files_in_dir = await self.workspace_service.get_workspace_files(session_id, target_dir)
                    logger.info("CD files in directory", session_id=session_id, files_count=len(files_in_dir) if files_in_dir else 0)
                    
                    # Also check if this directory path exists as part of any file path
                    
                    stmt = select(File).where(
                        and_(
                            File.session_id == session_id,
                            File.filepath.like(f"{target_dir}%")
                        )
                    ).limit(1)
                    
                    result = await self.workspace_service.db.execute(stmt)
                    directory_exists = result.first() is not None
                    logger.info("CD directory existence check", session_id=session_id, directory_exists=directory_exists)
                    
                    if not directory_exists:
                        logger.error("CD directory does not exist", session_id=session_id, target_dir=target_dir)
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"cd: {target_dir}: No such file or directory\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
                        
                except Exception as e:
                    logger.error(
                        "Error validating directory",
                        session_id=session_id,
                        target_dir=target_dir,
                        error=str(e)
                    )
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"cd: Error accessing directory: {str(e)}\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
            else:
                logger.info("CD skipping validation (root dir or no workspace service)", session_id=session_id, target_dir=target_dir, has_workspace_service=bool(self.workspace_service))
            
            # Update working directory
            self.working_directories[session_id] = target_dir
            
            # Also update the session's working directory
            session = self.sessions.get(session_id)
            if session:
                session["working_directory"] = target_dir
            
            logger.info(
                "Directory changed successfully",
                session_id=session_id,
                from_dir=current_dir,
                to_dir=target_dir
            )
            
            result = {
                "success": True,
                "stdout": "",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command,
                "working_directory": target_dir  # Include new working directory
            }
            
            logger.info("CD command result", session_id=session_id, result=result)
            return result
            
        except Exception as e:
            logger.error(
                "cd command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"cd error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_mkdir(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute mkdir command."""
        logger.info("MKDIR command received", session_id=session_id, command=command)
        
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                logger.error("MKDIR command missing directory", session_id=session_id)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "mkdir: missing operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            dir_name = parts[1]
            logger.info("MKDIR command processing", session_id=session_id, current_dir=working_dir, dir_name=dir_name)
            
            # Handle relative vs absolute paths
            if dir_name.startswith("/"):
                # Absolute path - use as is
                target_path = dir_name
                parent_path = "/".join(target_path.split("/")[:-1]) or "/"
                folder_name = target_path.split("/")[-1]
            else:
                # Relative path - relative to current working directory
                parent_path = working_dir
                folder_name = dir_name
            
            logger.info("MKDIR resolved paths", session_id=session_id, parent_path=parent_path, folder_name=folder_name)
                
            # Security: Ensure we stay within workspace root
            if ".." in folder_name or folder_name.startswith("../"):
                logger.error("MKDIR security violation", session_id=session_id, folder_name=folder_name)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "mkdir: cannot create directory: Access denied\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Create the directory using workspace service
            if self.workspace_service:
                logger.info("MKDIR creating directory", session_id=session_id, folder_name=folder_name, parent_path=parent_path)
                try:
                    folder_path = await self.workspace_service.create_folder(
                        session_id=session_id,
                        folder_name=folder_name,
                        parent_path=parent_path
                    )
                    
                    logger.info("MKDIR directory created successfully", session_id=session_id, folder_path=folder_path)
                    
                    # Send folder creation notification to update file explorer
                    if self.websocket_manager:
                        try:
                            folder_created_msg = FolderCreatedMessage(
                                type=MessageType.FOLDER_CREATED,
                                foldername=folder_name,
                                folderpath=folder_path,
                                parent_path=parent_path
                            )
                            await self.websocket_manager.broadcast_to_session(session_id, folder_created_msg)
                            logger.info("MKDIR folder creation notification sent", session_id=session_id, folder_path=folder_path)
                        except Exception as e:
                            logger.warning("Failed to send folder creation notification", session_id=session_id, error=str(e))
                    
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": "",
                        "return_code": 0,
                        "execution_time": 0.0,
                        "command": command
                    }
                    
                except Exception as e:
                    logger.error(
                        "Error creating directory",
                        session_id=session_id,
                        folder_name=folder_name,
                        parent_path=parent_path,
                        error=str(e)
                    )
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"mkdir: cannot create directory '{folder_name}': {str(e)}\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
            else:
                logger.error("MKDIR no workspace service available", session_id=session_id)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "mkdir: workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "mkdir command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"mkdir: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
    
    async def _execute_pip(self, session_id: str, working_dir: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute pip command with automatic pip upgrade to eliminate warnings."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Create temporary workspace for execution
            temp_workspace = await self.workspace_service.create_temp_workspace(session_id)
            
            # Ensure the temp workspace directory exists
            os.makedirs(temp_workspace, exist_ok=True)
            
            # Check if this is a pip install command and upgrade pip first
            if "pip install" in command.lower() or "pip3 install" in command.lower():
                logger.info("Auto-upgrading pip to prevent warning messages", session_id=session_id)
                
                # First, upgrade pip silently
                upgrade_process = await asyncio.create_subprocess_exec(
                    "python3", "-m", "pip", "install", "--upgrade", "pip", "--quiet",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_workspace
                )
                
                await asyncio.wait_for(upgrade_process.communicate(), timeout=30)
                # Don't fail if pip upgrade fails, just continue with original command
            
            # Make pip uninstall commands non-interactive by adding -y flag
            modified_command = command
            if "pip uninstall" in command.lower() or "pip3 uninstall" in command.lower():
                # Check if -y flag is not already present
                if " -y " not in command.lower() and not command.lower().endswith(" -y"):
                    # Add -y flag to make it non-interactive
                    parts = command.split()
                    if len(parts) >= 3:  # pip uninstall package_name
                        parts.insert(2, "-y")  # Insert -y after "uninstall"
                        modified_command = " ".join(parts)
                        logger.info(f"Made pip uninstall non-interactive: {modified_command}", session_id=session_id)
            
            # Execute the pip command (potentially modified)
            process = await asyncio.create_subprocess_exec(
                *shlex.split(modified_command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_workspace
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout_text = stdout.decode('utf-8')
            stderr_text = stderr.decode('utf-8')
            
            # Filter out pip upgrade warnings from output
            filtered_stderr = []
            for line in stderr_text.split('\n'):
                # Skip pip upgrade warning messages
                if not ("pip version" in line.lower() and "is available" in line.lower()) and \
                   not ("should consider upgrading" in line.lower()) and \
                   not line.strip().startswith("WARNING: You are using pip version"):
                    filtered_stderr.append(line)
            
            filtered_stderr_text = '\n'.join(filtered_stderr).strip()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": filtered_stderr_text,
                "return_code": process.returncode,
                "execution_time": 0.0,
                "command": command  # Return original command in response
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
                "stderr": f"pip command execution error: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }

    async def _execute_touch(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute touch command to create an empty file."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "touch: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            filename = parts[1]
            logger.info("Touch command processing", session_id=session_id, current_dir=working_dir, filename=filename)
            
            # Resolve path
            filepath = filename
            if not filepath.startswith("/"):
                filepath = os.path.join(working_dir, filepath).replace("\\", "/")
            
            # Create the file using workspace service
            if self.workspace_service:
                logger.info("Touch creating file", session_id=session_id, filepath=filepath)
                try:
                    saved_file = await self.workspace_service.save_file(
                        session_id=session_id,
                        filepath=filepath,
                        content="",  # Empty content for touch
                        language="text"  # Default language for touch files
                    )
                    
                    logger.info("Touch file created successfully", session_id=session_id, filepath=filepath)
                    
                    # Send file update notification to update file explorer
                    if self.websocket_manager:
                        try:
                            file_updated_msg = FileUpdatedMessage(
                                type=MessageType.FILE_UPDATED,
                                filename=filepath,
                                content="",  # Empty content for touch
                                updated_by="terminal",
                                language="text"
                            )
                            await self.websocket_manager.broadcast_to_session(session_id, file_updated_msg)
                            logger.info("Touch file update notification sent", session_id=session_id, filepath=filepath)
                        except Exception as e:
                            logger.warning("Failed to send file update notification", session_id=session_id, error=str(e))
                    
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": "",
                        "return_code": 0,
                        "execution_time": 0.0,
                        "command": command
                    }
                    
                except Exception as e:
                    logger.error(
                        "Error creating file",
                        session_id=session_id,
                        filepath=filepath,
                        error=str(e)
                    )
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"touch: cannot create file '{filename}': {str(e)}\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
            else:
                logger.error("Touch no workspace service available", session_id=session_id)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "touch: workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "touch command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"touch: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }

    async def _execute_cp(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute cp command to copy files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 3:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "cp: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            source_path = parts[1]
            dest_path = parts[2]
            logger.info("CP command processing", session_id=session_id, current_dir=working_dir, source_path=source_path, dest_path=dest_path)
            
            # Resolve paths
            if not source_path.startswith("/"):
                source_path = os.path.join(working_dir, source_path).replace("\\", "/")
            if not dest_path.startswith("/"):
                dest_path = os.path.join(working_dir, dest_path).replace("\\", "/")
            
            # Get source file content
            source_content = await self.workspace_service.get_file_content(session_id, source_path)
            if source_content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cp: cannot stat '{parts[1]}': No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Determine language for destination file
            source_ext = os.path.splitext(source_path)[1].lower()
            dest_ext = os.path.splitext(dest_path)[1].lower()
            
            # Map extensions to languages
            ext_to_language = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.jsx': 'javascript',
                '.tsx': 'typescript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json',
                '.md': 'markdown',
                '.txt': 'text',
                '.sql': 'sql',
                '.yaml': 'yaml',
                '.yml': 'yaml'
            }
            
            # Use destination extension if available, otherwise use source extension
            language = ext_to_language.get(dest_ext, ext_to_language.get(source_ext, 'text'))
            
            # Create the destination file
            try:
                saved_file = await self.workspace_service.save_file(
                    session_id=session_id,
                    filepath=dest_path,
                    content=source_content,
                    language=language
                )
                
                logger.info("CP file copied successfully", session_id=session_id, source_path=source_path, dest_path=dest_path)
                
                # Send file update notification to update file explorer
                if self.websocket_manager:
                    try:
                        file_updated_msg = FileUpdatedMessage(
                            type=MessageType.FILE_UPDATED,
                            filename=dest_path,
                            content=source_content,
                            updated_by="terminal",
                            language=language
                        )
                        await self.websocket_manager.broadcast_to_session(session_id, file_updated_msg)
                        logger.info("CP file update notification sent", session_id=session_id, dest_path=dest_path)
                    except Exception as e:
                        logger.warning("Failed to send file update notification", session_id=session_id, error=str(e))
                
                return {
                    "success": True,
                    "stdout": "",
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
                
            except Exception as e:
                logger.error(
                    "Error copying file",
                    session_id=session_id,
                    source_path=source_path,
                    dest_path=dest_path,
                    error=str(e)
                )
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"cp: cannot create regular file '{parts[2]}': {str(e)}\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "cp command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"cp: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }

    async def _execute_mv(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute mv command to move/rename files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 3:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "mv: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            source_path = parts[1]
            dest_path = parts[2]
            logger.info("MV command processing", session_id=session_id, current_dir=working_dir, source_path=source_path, dest_path=dest_path)
            
            # Resolve paths
            if not source_path.startswith("/"):
                source_path = os.path.join(working_dir, source_path).replace("\\", "/")
            if not dest_path.startswith("/"):
                dest_path = os.path.join(working_dir, dest_path).replace("\\", "/")
            
            # Get source file content
            source_content = await self.workspace_service.get_file_content(session_id, source_path)
            if source_content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"mv: cannot stat '{parts[1]}': No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Determine language for destination file
            source_ext = os.path.splitext(source_path)[1].lower()
            dest_ext = os.path.splitext(dest_path)[1].lower()
            
            # Map extensions to languages
            ext_to_language = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.jsx': 'javascript',
                '.tsx': 'typescript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json',
                '.md': 'markdown',
                '.txt': 'text',
                '.sql': 'sql',
                '.yaml': 'yaml',
                '.yml': 'yaml'
            }
            
            # Use destination extension if available, otherwise use source extension
            language = ext_to_language.get(dest_ext, ext_to_language.get(source_ext, 'text'))
            
            # Create the destination file
            try:
                saved_file = await self.workspace_service.save_file(
                    session_id=session_id,
                    filepath=dest_path,
                    content=source_content,
                    language=language
                )
                
                logger.info("MV file moved/renamed successfully", session_id=session_id, source_path=source_path, dest_path=dest_path)
                
                # Send file update notification to update file explorer
                if self.websocket_manager:
                    try:
                        file_updated_msg = FileUpdatedMessage(
                            type=MessageType.FILE_UPDATED,
                            filename=dest_path,
                            content=source_content,
                            updated_by="terminal",
                            language=language
                        )
                        await self.websocket_manager.broadcast_to_session(session_id, file_updated_msg)
                        logger.info("MV file update notification sent", session_id=session_id, dest_path=dest_path)
                    except Exception as e:
                        logger.warning("Failed to send file update notification", session_id=session_id, error=str(e))
                
                # Delete the original file
                if self.workspace_service:
                    try:
                        await self.workspace_service.delete_file(session_id, source_path)
                        logger.info("MV original file deleted", session_id=session_id, source_path=source_path)
                        
                        # Send file deletion notification to update file explorer
                        if self.websocket_manager:
                            try:
                                file_deleted_msg = FileDeletedMessage(
                                    type=MessageType.FILE_DELETED,
                                    filename=source_path,
                                    deleted_by="terminal"
                                )
                                await self.websocket_manager.broadcast_to_session(session_id, file_deleted_msg)
                                logger.info("MV file deletion notification sent", session_id=session_id, source_path=source_path)
                            except Exception as e:
                                logger.warning("Failed to send file deletion notification", session_id=session_id, error=str(e))
                    except Exception as e:
                        logger.warning("Failed to delete original file", session_id=session_id, source_path=source_path, error=str(e))
                
                return {
                    "success": True,
                    "stdout": "",
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
                
            except Exception as e:
                logger.error(
                    "Error moving/renaming file",
                    session_id=session_id,
                    source_path=source_path,
                    dest_path=dest_path,
                    error=str(e)
                )
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"mv: cannot create regular file '{parts[2]}': {str(e)}\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "mv command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"mv: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }

    async def _execute_rm(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute rm command to remove files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "rm: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            filepath = parts[1]
            logger.info("RM command processing", session_id=session_id, current_dir=working_dir, filepath=filepath)
            
            # Resolve path
            if not filepath.startswith("/"):
                filepath = os.path.join(working_dir, filepath).replace("\\", "/")
            
            # Check if the file exists
            if self.workspace_service:
                try:
                    file_exists = await self.workspace_service.get_file_content(session_id, filepath) is not None
                    if not file_exists:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"rm: cannot remove '{filepath}': No such file or directory\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
                    
                    # Delete the file using workspace service
                    await self.workspace_service.delete_file(session_id, filepath)
                    logger.info("RM file deleted", session_id=session_id, filepath=filepath)
                    
                    # Send file deletion notification to update file explorer
                    if self.websocket_manager:
                        try:
                            file_deleted_msg = FileDeletedMessage(
                                type=MessageType.FILE_DELETED,
                                filename=filepath,
                                deleted_by="terminal"
                            )
                            await self.websocket_manager.broadcast_to_session(session_id, file_deleted_msg)
                            logger.info("RM file deletion notification sent", session_id=session_id, filepath=filepath)
                        except Exception as e:
                            logger.warning("Failed to send file deletion notification", session_id=session_id, error=str(e))
                    
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": "",
                        "return_code": 0,
                        "execution_time": 0.0,
                        "command": command
                    }
                    
                except Exception as e:
                    logger.error(
                        "Error deleting file",
                        session_id=session_id,
                        filepath=filepath,
                        error=str(e)
                    )
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"rm: cannot remove '{filepath}': {str(e)}\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
            else:
                logger.error("RM no workspace service available", session_id=session_id)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "rm: workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
                
        except Exception as e:
            logger.error(
                "rm command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"rm: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }

    async def _execute_grep(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute grep command to search for text patterns."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "grep: missing pattern\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            pattern = parts[1]
            filename = parts[2] if len(parts) > 2 else None
            
            logger.info("GREP command processing", session_id=session_id, pattern=pattern, filename=filename)
            
            # Get all files or specific file
            if filename:
                # Search in specific file
                filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
                content = await self.workspace_service.get_file_content(session_id, filepath)
                
                if content is None:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"grep: {filename}: No such file or directory\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
                
                files_to_search = [(filepath, content)]
            else:
                # Search in all files
                stmt = select(File).where(File.session_id == session_id)
                result = await self.workspace_service.db.execute(stmt)
                files = result.scalars().all()
                files_to_search = [(f.filepath, f.content) for f in files if f.content]
            
            # Search for pattern
            import re
            results = []
            
            for filepath, content in files_to_search:
                try:
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            filename_display = os.path.basename(filepath) if not filename else filename
                            results.append(f"{filename_display}:{line_num}:{line}")
                except re.error:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"grep: invalid regular expression '{pattern}'\n",
                        "return_code": 1,
                        "execution_time": 0.0,
                        "command": command
                    }
            
            return {
                "success": True,
                "stdout": "\n".join(results) + ("\n" if results else "\n"),
                "stderr": "",
                "return_code": 0 if results else 1,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "grep command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"grep: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_find(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute find command to search for files."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "find: missing path\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            search_path = parts[1]
            name_pattern = None
            
            # Parse find options
            for i in range(2, len(parts)):
                if parts[i] == "-name" and i + 1 < len(parts):
                    name_pattern = parts[i + 1]
                    break
            
            logger.info("FIND command processing", session_id=session_id, search_path=search_path, name_pattern=name_pattern)
            
            # Get all files
            stmt = select(File).where(File.session_id == session_id)
            result = await self.workspace_service.db.execute(stmt)
            files = result.scalars().all()
            
            results = []
            import fnmatch
            
            for file in files:
                filepath = file.filepath
                filename = os.path.basename(filepath)
                
                # Check if file matches search path
                if not filepath.startswith(search_path):
                    continue
                
                # Check name pattern if specified
                if name_pattern and not fnmatch.fnmatch(filename, name_pattern):
                    continue
                
                results.append(filepath)
            
            return {
                "success": True,
                "stdout": "\n".join(results) + ("\n" if results else ""),
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "find command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"find: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_head(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute head command to display first lines of file."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "head: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Parse options
            num_lines = 10  # Default
            filename = parts[-1]
            
            for i in range(1, len(parts) - 1):
                if parts[i].startswith("-n") and i + 1 < len(parts):
                    try:
                        num_lines = int(parts[i + 1])
                    except ValueError:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"head: invalid number of lines: {parts[i + 1]}\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
                elif parts[i].startswith("-") and parts[i][1:].isdigit():
                    # Handle shorthand like -2, -5, etc.
                    try:
                        num_lines = int(parts[i][1:])
                    except ValueError:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"head: invalid number of lines: {parts[i]}\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
            
            logger.info("HEAD command processing", session_id=session_id, filename=filename, num_lines=num_lines)
            
            # Get file content
            filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"head: cannot open '{filename}' for reading: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Get first n lines
            lines = content.split('\n')
            result_lines = lines[:num_lines]
            
            return {
                "success": True,
                "stdout": "\n".join(result_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "head command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"head: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_tail(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute tail command to display last lines of file."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "tail: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Parse options
            num_lines = 10  # Default
            filename = parts[-1]
            
            for i in range(1, len(parts) - 1):
                if parts[i].startswith("-n") and i + 1 < len(parts):
                    try:
                        num_lines = int(parts[i + 1])
                    except ValueError:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"tail: invalid number of lines: {parts[i + 1]}\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
                elif parts[i].startswith("-") and parts[i][1:].isdigit():
                    # Handle shorthand like -5, -10, etc.
                    try:
                        num_lines = int(parts[i][1:])
                    except ValueError:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"tail: invalid number of lines: {parts[i]}\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
            
            logger.info("TAIL command processing", session_id=session_id, filename=filename, num_lines=num_lines)
            
            # Get file content
            filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"tail: cannot open '{filename}' for reading: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Get last n lines
            lines = content.split('\n')
            result_lines = lines[-num_lines:] if len(lines) > num_lines else lines
            
            return {
                "success": True,
                "stdout": "\n".join(result_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "tail command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"tail: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_wc(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute wc command to count words, lines, and characters."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "wc: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            filename = parts[1]
            
            logger.info("WC command processing", session_id=session_id, filename=filename)
            
            # Get file content
            filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"wc: {filename}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Count lines, words, and characters
            lines = len(content.split('\n'))
            words = len(content.split())
            chars = len(content)
            
            return {
                "success": True,
                "stdout": f" {lines} {words} {chars} {filename}\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "wc command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"wc: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_sort(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute sort command to sort lines."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "sort: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Parse options
            reverse = False
            filename = parts[-1]
            
            for i in range(1, len(parts) - 1):
                if parts[i] == "-r":
                    reverse = True
            
            logger.info("SORT command processing", session_id=session_id, filename=filename, reverse=reverse)
            
            # Get file content
            filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"sort: cannot read: {filename}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Sort lines
            lines = content.split('\n')
            sorted_lines = sorted(lines, reverse=reverse)
            
            return {
                "success": True,
                "stdout": "\n".join(sorted_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "sort command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"sort: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_uniq(self, session_id: str, working_dir: str, command: str) -> Dict[str, Any]:
        """Execute uniq command to remove duplicate lines."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            parts = shlex.split(command)
            if len(parts) < 2:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "uniq: missing file operand\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            filename = parts[1]
            
            logger.info("UNIQ command processing", session_id=session_id, filename=filename)
            
            # Get file content
            filepath = filename if filename.startswith("/") else os.path.join(working_dir, filename).replace("\\", "/")
            content = await self.workspace_service.get_file_content(session_id, filepath)
            
            if content is None:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"uniq: cannot read: {filename}: No such file or directory\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Remove duplicate consecutive lines
            lines = content.split('\n')
            unique_lines = []
            prev_line = None
            
            for line in lines:
                if line != prev_line:
                    unique_lines.append(line)
                    prev_line = line
            
            return {
                "success": True,
                "stdout": "\n".join(unique_lines) + "\n",
                "stderr": "",
                "return_code": 0,
                "execution_time": 0.0,
                "command": command
            }
            
        except Exception as e:
            logger.error(
                "uniq command error",
                session_id=session_id,
                command=command,
                error=str(e)
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"uniq: {str(e)}\n",
                "return_code": 1,
                "execution_time": 0.0,
                "command": command
            }
 
    async def _execute_general_command(self, session_id: str, working_dir: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute general command using subprocess."""
        try:
            if not self.workspace_service:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "Workspace service not available\n",
                    "return_code": 1,
                    "execution_time": 0.0,
                    "command": command
                }
            
            # Create temporary workspace for execution
            temp_workspace = await self.workspace_service.create_temp_workspace(session_id)
            
            # Ensure the temp workspace directory exists
            os.makedirs(temp_workspace, exist_ok=True)
            
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_workspace
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
    
    def _handle_redirection(self, cmd_parts: List[str]) -> List[str]:
        """
        Handles input/output redirection for commands.
        Returns the modified command parts.
        """
        new_cmd_parts = []
        i = 0
        while i < len(cmd_parts):
            part = cmd_parts[i]
            
            if part == ">":
                if i + 1 < len(cmd_parts):
                    output_file = cmd_parts[i + 1]
                    if not output_file.startswith("/"):
                        output_file = os.path.join(os.getcwd(), output_file).replace("\\", "/")
                    new_cmd_parts.append(f"redirect_stdout={output_file}")
                    i += 2
                else:
                    new_cmd_parts.append(part) # Keep the '>'
                    i += 1
            elif part == "<":
                if i + 1 < len(cmd_parts):
                    input_file = cmd_parts[i + 1]
                    if not input_file.startswith("/"):
                        input_file = os.path.join(os.getcwd(), input_file).replace("\\", "/")
                    new_cmd_parts.append(f"redirect_stdin={input_file}")
                    i += 2
                else:
                    new_cmd_parts.append(part) # Keep the '<'
                    i += 1
            else:
                new_cmd_parts.append(part)
                i += 1
        
        return new_cmd_parts
    
    def get_command_history(self, session_id: str, limit: int = 50) -> List[str]:
        """Get command history for a session."""
        history = self.command_history.get(session_id, [])
        return history[-limit:] if limit > 0 else history
    
    def get_working_directory(self, session_id: str) -> str:
        """Get current working directory for a session."""
        return self.working_directories.get(session_id, "/")
    
    def cleanup_session(self, session_id: str):
        """Clean up a terminal session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.command_history:
            del self.command_history[session_id]
        if session_id in self.working_directories:
            del self.working_directories[session_id]
        
        logger.info("Terminal session cleaned up", session_id=session_id)
    
    async def _execute_help(self) -> Dict[str, Any]:
        """Execute help command."""
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
            "command": "help"
        }
    
    async def _execute_pwd(self, session_id: str, working_dir: str) -> Dict[str, Any]:
        """Execute pwd command."""
        return {
            "success": True,
            "stdout": f"{working_dir}\n",
            "stderr": "",
            "return_code": 0,
            "execution_time": 0.0,
            "command": "pwd"
        }
    
    async def _execute_clear(self) -> Dict[str, Any]:
        """Execute clear command."""
        return {
            "success": True,
            "stdout": "__CLEAR_TERMINAL__",  # Special signal for frontend to clear terminal
            "stderr": "",
            "return_code": 0,
            "execution_time": 0.0,
            "command": "clear"
        }
    
    async def _execute_echo(self, command: str, session_id: str = None) -> Dict[str, Any]:
        """Execute echo command."""
        # Extract the text after "echo "
        text = command[5:] if command.startswith("echo ") else ""
        
        # Check for redirection
        if " > " in command:
            parts = command.split(" > ")
            if len(parts) == 2:
                echo_text = parts[0][5:].strip()  # Remove "echo " prefix
                filename = parts[1].strip()
                
                # Remove quotes from filename if present
                if (filename.startswith('"') and filename.endswith('"')) or \
                   (filename.startswith("'") and filename.endswith("'")):
                    filename = filename[1:-1]
                
                # Remove quotes from echo text if present
                if (echo_text.startswith('"') and echo_text.endswith('"')) or \
                   (echo_text.startswith("'") and echo_text.endswith("'")):
                    echo_text = echo_text[1:-1]
                
                # Save the file using workspace service
                if hasattr(self, 'workspace_service') and self.workspace_service and session_id:
                    try:
                        # Resolve file path
                        filepath = filename
                        if not filepath.startswith("/"):
                            filepath = f"/{filepath}"
                        
                        await self.workspace_service.save_file(
                            session_id=session_id,
                            filepath=filepath,
                            content=echo_text,
                            language="text"
                        )
                    except Exception as e:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"echo: cannot write to file '{filename}': {str(e)}\n",
                            "return_code": 1,
                            "execution_time": 0.0,
                            "command": command
                        }
                
                return {
                    "success": True,
                    "stdout": f"{echo_text}\n",
                    "stderr": "",
                    "return_code": 0,
                    "execution_time": 0.0,
                    "command": command
                }
        
        return {
            "success": True,
            "stdout": f"{text}\n",
            "stderr": "",
            "return_code": 0,
            "execution_time": 0.0,
            "command": command
        }


# Global terminal service instance
terminal_service = TerminalService() 