"""
AfterIDE - Security Module

Comprehensive security features including rate limiting, input validation,
security headers, and protection against various attacks.
"""

import time
import hashlib
import re
import json
import structlog
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from pydantic import BaseModel, validator
import html
import urllib.parse

logger = structlog.get_logger(__name__)


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size: int = 60  # seconds
    
    @validator('requests_per_minute')
    def validate_requests_per_minute(cls, v):
        if v < 1:
            raise ValueError('requests_per_minute must be at least 1')
        return v


class SecurityConfig(BaseModel):
    """Configuration for security features."""
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_config: RateLimitConfig = RateLimitConfig()
    
    # Input validation
    max_input_length: int = 10000
    max_file_size_mb: int = 10
    allowed_file_extensions: List[str] = [
        '.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt',
        '.yml', '.yaml', '.xml', '.sql', '.sh', '.bash', '.zsh'
    ]
    
    # Code execution security
    blocked_commands: List[str] = [
        'sudo', 'su', 'rm -rf /', 'dd', 'mkfs', 'fdisk', 'shutdown',
        'reboot', 'halt', 'poweroff', 'chmod 777', 'chown root', 'passwd',
        'useradd', 'userdel', 'groupadd', 'groupdel', 'visudo', 'crontab'
    ]
    
    blocked_patterns: List[str] = [
        r'sudo\s+', r'su\s+', r'rm\s+-rf\s+/', r'dd\s+if=',
        r'mkfs\s+', r'fdisk\s+', r'shutdown\s+', r'reboot\s+',
        r'halt\s+', r'poweroff\s+', r'chmod\s+777', r'chown\s+root',
        r'passwd\s+', r'useradd\s+', r'userdel\s+', r'groupadd\s+',
        r'groupdel\s+', r'visudo\s+', r'crontab\s+'
    ]
    
    # Path traversal protection
    blocked_path_patterns: List[str] = [
        r'\.\./', r'\.\.\\', r'\.\.$', r'^/', r'^\\',
        r'/etc/', r'/var/', r'/usr/', r'/bin/', r'/sbin/',
        r'/proc/', r'/sys/', r'/dev/', r'/boot/', r'/root/'
    ]


class RateLimiter:
    """Rate limiting implementation using Redis or in-memory storage."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_storage: Dict[str, List[float]] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_rate_limited(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited."""
        current_time = time.time()
        
        if self.redis_client:
            return await self._redis_rate_limit(key, limit, window, current_time)
        else:
            return await self._memory_rate_limit(key, limit, window, current_time)
    
    async def _redis_rate_limit(self, key: str, limit: int, window: int, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting using Redis."""
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            is_limited = current_count >= limit
            remaining = max(0, limit - current_count)
            
            return is_limited, {
                'limit': limit,
                'remaining': remaining,
                'reset_time': current_time + window,
                'current_count': current_count
            }
            
        except Exception as e:
            logger.error("Redis rate limiting error", error=str(e))
            # Fallback to memory storage
            return await self._memory_rate_limit(key, limit, window, current_time)
    
    async def _memory_rate_limit(self, key: str, limit: int, window: int, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """Rate limiting using in-memory storage."""
        async with self.lock:
            # Remove old entries
            self.memory_storage[key] = [
                timestamp for timestamp in self.memory_storage[key]
                if current_time - timestamp < window
            ]
            
            current_count = len(self.memory_storage[key])
            is_limited = current_count >= limit
            
            if not is_limited:
                self.memory_storage[key].append(current_time)
            
            remaining = max(0, limit - current_count)
            
            return is_limited, {
                'limit': limit,
                'remaining': remaining,
                'reset_time': current_time + window,
                'current_count': current_count
            }


class InputValidator:
    """Input validation and sanitization."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.blocked_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in config.blocked_patterns]
        self.blocked_path_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in config.blocked_path_patterns]
    
    def validate_and_sanitize_input(self, input_data: str, input_type: str = "general") -> Tuple[bool, str, str]:
        """
        Validate and sanitize input data.
        
        Returns:
            Tuple of (is_valid, sanitized_input, error_message)
        """
        # Check length
        if len(input_data) > self.config.max_input_length:
            return False, "", f"Input too long (max {self.config.max_input_length} characters)"
        
        # Check for null bytes
        if '\x00' in input_data:
            return False, "", "Null bytes not allowed"
        
        # Type-specific validation
        if input_type == "command":
            return self._validate_command(input_data)
        elif input_type == "filepath":
            return self._validate_filepath(input_data)
        elif input_type == "code":
            return self._validate_code(input_data)
        else:
            return self._validate_general(input_data)
    
    def _validate_command(self, command: str) -> Tuple[bool, str, str]:
        """Validate command input."""
        # Check for blocked commands
        for blocked_cmd in self.config.blocked_commands:
            if blocked_cmd.lower() in command.lower():
                return False, "", f"Command '{blocked_cmd}' is not allowed"
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(command):
                return False, "", "Command pattern is not allowed"
        
        # Special handling for cd .. command - allow it
        if command.strip().lower() == "cd ..":
            sanitized = self._sanitize_command(command)
            return True, sanitized, ""
        
        # Check for path traversal (but allow cd ..)
        for pattern in self.blocked_path_patterns:
            if pattern.search(command):
                return False, "", "Path traversal is not allowed"
        
        # Sanitize command
        sanitized = self._sanitize_command(command)
        return True, sanitized, ""
    
    def _validate_filepath(self, filepath: str) -> Tuple[bool, str, str]:
        """Validate file path."""
        # Check for path traversal
        for pattern in self.blocked_path_patterns:
            if pattern.search(filepath):
                return False, "", "Path traversal is not allowed"
        
        # Check file extension
        if '.' in filepath:
            ext = filepath[filepath.rfind('.'):].lower()
            if ext not in self.config.allowed_file_extensions:
                return False, "", f"File extension '{ext}' is not allowed"
        
        # Sanitize path
        sanitized = self._sanitize_path(filepath)
        return True, sanitized, ""
    
    def _validate_code(self, code: str) -> Tuple[bool, str, str]:
        """Validate code input."""
        # Check for potentially dangerous imports
        dangerous_imports = [
            'import os', 'import sys', 'import subprocess', 'import multiprocessing',
            'from os import', 'from sys import', 'from subprocess import',
            '__import__', 'eval(', 'exec(', 'compile('
        ]
        
        for dangerous in dangerous_imports:
            if dangerous.lower() in code.lower():
                return False, "", f"Dangerous import/function '{dangerous}' is not allowed"
        
        # Sanitize code (basic HTML escaping for display)
        sanitized = html.escape(code)
        return True, sanitized, ""
    
    def _validate_general(self, input_data: str) -> Tuple[bool, str, str]:
        """Validate general input."""
        # Basic sanitization
        sanitized = html.escape(input_data)
        return True, sanitized, ""
    
    def _sanitize_command(self, command: str) -> str:
        """Sanitize command input."""
        # Remove null bytes
        command = command.replace('\x00', '')
        
        # Basic command sanitization
        command = command.strip()
        
        return command
    
    def _sanitize_path(self, filepath: str) -> str:
        """Sanitize file path."""
        # Remove null bytes
        filepath = filepath.replace('\x00', '')
        
        # Normalize path
        filepath = filepath.replace('\\', '/')
        
        # Remove multiple slashes
        filepath = re.sub(r'/+', '/', filepath)
        
        return filepath


class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers to add to responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' ws: wss:;",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }


class CSRFProtection:
    """CSRF protection implementation."""
    
    def __init__(self):
        self.tokens: Dict[str, str] = {}
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        token = hashlib.sha256(f"{session_id}{time.time()}".encode()).hexdigest()
        self.tokens[session_id] = token
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token."""
        return self.tokens.get(session_id) == token
    
    def remove_token(self, session_id: str):
        """Remove CSRF token."""
        self.tokens.pop(session_id, None)


class SecurityMiddleware:
    """Comprehensive security middleware."""
    
    def __init__(self, config: SecurityConfig, rate_limiter: RateLimiter, input_validator: InputValidator):
        self.config = config
        self.rate_limiter = rate_limiter
        self.input_validator = input_validator
        self.csrf_protection = CSRFProtection()
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process request through security middleware."""
        start_time = time.time()
        
        # TEMPORARILY SKIP SECURITY MIDDLEWARE FOR LOGIN ENDPOINTS
        if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/register"]:
            response = await call_next(request)
            # Still add security headers
            for header, value in SecurityHeaders.get_security_headers().items():
                response.headers[header] = value
            return response
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Rate limiting
        if self.config.rate_limit_enabled:
            is_limited, rate_info = await self.rate_limiter.is_rate_limited(
                f"rate_limit:{client_id}",
                self.config.rate_limit_config.requests_per_minute,
                self.config.rate_limit_config.window_size
            )
            
            if is_limited:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": int(rate_info['reset_time'] - time.time())
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info['limit']),
                        "X-RateLimit-Remaining": str(rate_info['remaining']),
                        "X-RateLimit-Reset": str(int(rate_info['reset_time']))
                    }
                )
        
        # Input validation for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Validate JSON input
                    try:
                        json_data = json.loads(body.decode())
                        is_valid, sanitized, error = self.input_validator.validate_and_sanitize_input(
                            json.dumps(json_data), "general"
                        )
                        if not is_valid:
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": f"Invalid input: {error}"}
                            )
                    except json.JSONDecodeError:
                        # Not JSON, validate as string
                        is_valid, sanitized, error = self.input_validator.validate_and_sanitize_input(
                            body.decode(), "general"
                        )
                        if not is_valid:
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": f"Invalid input: {error}"}
                            )
            except Exception as e:
                logger.warning("Input validation error", error=str(e))
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        
        # Add rate limit headers
        if self.config.rate_limit_enabled:
            response.headers["X-RateLimit-Limit"] = str(self.config.rate_limit_config.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
            response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_time']))
        
        # Log security events
        processing_time = time.time() - start_time
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            client_id=client_id,
            processing_time=processing_time,
            status_code=response.status_code
        )
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get from X-Forwarded-For header (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"


# Global security instances
security_config = SecurityConfig()
rate_limiter = RateLimiter()
input_validator = InputValidator(security_config)
security_middleware = SecurityMiddleware(security_config, rate_limiter, input_validator) 