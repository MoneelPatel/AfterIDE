"""
AfterIDE - Comprehensive Security Tests

Tests for all security features including rate limiting, input validation,
authentication, and code execution security.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.core.security import (
    SecurityConfig, RateLimiter, InputValidator, SecurityHeaders,
    CSRFProtection, SecurityMiddleware, security_config, rate_limiter,
    input_validator, security_middleware
)
from app.services.security_monitor import (
    SecurityMonitor, SecurityEvent, SecurityEventType, SecurityLevel,
    SecurityAlert, security_monitor
)
from app.services.auth import (
    AuthService, PasswordValidator, AccountSecurity, SessionManager,
    password_validator, account_security, session_manager
)
from app.services.terminal import TerminalService, ResourceLimits, CommandSandbox


class TestSecurityConfig:
    """Test security configuration."""
    
    def test_security_config_defaults(self):
        """Test security configuration default values."""
        config = SecurityConfig()
        
        assert config.rate_limit_enabled is True
        assert config.rate_limit_config.requests_per_minute == 60
        assert config.max_input_length == 10000
        assert len(config.blocked_commands) > 0
        assert len(config.blocked_patterns) > 0
        assert len(config.blocked_path_patterns) > 0
    
    def test_rate_limit_config_validation(self):
        """Test rate limit configuration validation."""
        # Test valid configuration
        config = SecurityConfig()
        config.rate_limit_config.requests_per_minute = 100
        assert config.rate_limit_config.requests_per_minute == 100
        
        # Test invalid configuration
        with pytest.raises(ValueError):
            config.rate_limit_config.requests_per_minute = 0


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest_asyncio.fixture
    async def rate_limiter(self):
        """Create a rate limiter instance."""
        return RateLimiter()
    
    @pytest.mark.asyncio
    async def test_memory_rate_limiting(self, rate_limiter):
        """Test in-memory rate limiting."""
        client_id = "test_client"
        limit = 5
        window = 60
        
        # Test normal requests
        for i in range(5):
            is_limited, info = await rate_limiter.is_rate_limited(client_id, limit, window)
            assert is_limited is False
            assert info['remaining'] == 4 - i
        
        # Test rate limit exceeded
        is_limited, info = await rate_limiter.is_rate_limited(client_id, limit, window)
        assert is_limited is True
        assert info['remaining'] == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_expiry(self, rate_limiter):
        """Test rate limit window expiry."""
        client_id = "test_client"
        limit = 2
        window = 1  # 1 second window
        
        # Make requests
        await rate_limiter.is_rate_limited(client_id, limit, window)
        await rate_limiter.is_rate_limited(client_id, limit, window)
        
        # Should be limited
        is_limited, _ = await rate_limiter.is_rate_limited(client_id, limit, window)
        assert is_limited is True
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should not be limited anymore
        is_limited, _ = await rate_limiter.is_rate_limited(client_id, limit, window)
        assert is_limited is False


class TestInputValidator:
    """Test input validation and sanitization."""
    
    @pytest.fixture
    def validator(self):
        """Create an input validator instance."""
        config = SecurityConfig()
        return InputValidator(config)
    
    def test_command_validation(self, validator):
        """Test command input validation."""
        # Test valid commands
        valid_commands = [
            "ls -la",
            "cat file.txt",
            "echo 'hello world'",
            "python script.py"
        ]
        
        for command in valid_commands:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(command, "command")
            assert is_valid is True, f"Command '{command}' should be valid: {error}"
        
        # Test blocked commands
        blocked_commands = [
            "sudo ls",
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown -h now"
        ]
        
        for command in blocked_commands:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(command, "command")
            assert is_valid is False, f"Command '{command}' should be blocked"
            assert "not allowed" in error
    
    def test_command_injection_detection(self, validator):
        """Test command injection detection."""
        injection_attempts = [
            "ls; rm -rf /",
            "cat file.txt | rm -rf /",
            "echo $(rm -rf /)",
            "ls `rm -rf /`"
        ]
        
        for attempt in injection_attempts:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(attempt, "command")
            assert is_valid is False, f"Injection attempt '{attempt}' should be blocked"
            assert "injection" in error.lower() or "not allowed" in error
    
    def test_path_traversal_detection(self, validator):
        """Test path traversal detection."""
        traversal_attempts = [
            "cat ../../../etc/passwd",
            "ls ../../../etc",
            "cd ../../../etc"
        ]
        
        for attempt in traversal_attempts:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(attempt, "command")
            assert is_valid is False, f"Path traversal '{attempt}' should be blocked"
            assert "traversal" in error.lower() or "not allowed" in error
    
    def test_filepath_validation(self, validator):
        """Test file path validation."""
        # Test valid file paths
        valid_paths = [
            "file.txt",
            "folder/file.py",
            "src/main.js"
        ]
        
        for path in valid_paths:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(path, "filepath")
            assert is_valid is True, f"Path '{path}' should be valid: {error}"
        
        # Test blocked file paths
        blocked_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for path in blocked_paths:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(path, "filepath")
            assert is_valid is False, f"Path '{path}' should be blocked"
    
    def test_code_validation(self, validator):
        """Test code input validation."""
        # Test valid code
        valid_code = """
        def hello():
            print("Hello, World!")
        
        hello()
        """
        
        is_valid, sanitized, error = validator.validate_and_sanitize_input(valid_code, "code")
        assert is_valid is True, f"Code should be valid: {error}"
        
        # Test dangerous code
        dangerous_code = [
            "import os; os.system('rm -rf /')",
            "import subprocess; subprocess.call(['rm', '-rf', '/'])",
            "eval('os.system(\"rm -rf /\")')",
            "__import__('os').system('rm -rf /')"
        ]
        
        for code in dangerous_code:
            is_valid, sanitized, error = validator.validate_and_sanitize_input(code, "code")
            assert is_valid is False, f"Dangerous code should be blocked: {code}"
            assert "not allowed" in error
    
    def test_input_length_limits(self, validator):
        """Test input length limits."""
        # Test input that's too long
        long_input = "x" * (validator.config.max_input_length + 1)
        is_valid, sanitized, error = validator.validate_and_sanitize_input(long_input, "general")
        assert is_valid is False
        assert "too long" in error
    
    def test_null_byte_detection(self, validator):
        """Test null byte detection."""
        input_with_null = "hello\x00world"
        is_valid, sanitized, error = validator.validate_and_sanitize_input(input_with_null, "general")
        assert is_valid is False
        assert "null bytes" in error


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_security_headers(self):
        """Test security headers generation."""
        headers = SecurityHeaders.get_security_headers()
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        for header in required_headers:
            assert header in headers
            assert headers[header] is not None
            assert len(headers[header]) > 0


class TestCSRFProtection:
    """Test CSRF protection."""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        csrf = CSRFProtection()
        session_id = "test_session"
        
        token1 = csrf.generate_token(session_id)
        token2 = csrf.generate_token(session_id)
        
        assert token1 != token2  # Tokens should be different
        assert len(token1) == 64  # SHA256 hash length
        assert len(token2) == 64
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation."""
        csrf = CSRFProtection()
        session_id = "test_session"
        
        token = csrf.generate_token(session_id)
        
        # Valid token
        assert csrf.validate_token(session_id, token) is True
        
        # Invalid token
        assert csrf.validate_token(session_id, "invalid_token") is False
        
        # Invalid session
        assert csrf.validate_token("invalid_session", token) is False
    
    def test_csrf_token_removal(self):
        """Test CSRF token removal."""
        csrf = CSRFProtection()
        session_id = "test_session"
        
        token = csrf.generate_token(session_id)
        assert csrf.validate_token(session_id, token) is True
        
        csrf.remove_token(session_id)
        assert csrf.validate_token(session_id, token) is False


class TestPasswordValidator:
    """Test password validation."""
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Test valid passwords
        valid_passwords = [
            "StrongPass123!",
            "MySecureP@ssw0rd",
            "Complex#Password1"
        ]
        
        for password in valid_passwords:
            is_valid, error = PasswordValidator.validate_password_strength(password)
            assert is_valid is True, f"Password should be valid: {error}"
        
        # Test weak passwords
        weak_passwords = [
            ("short", "Password must be at least 8 characters long"),
            ("password", "Password is too common"),
            ("123456", "Password is too common"),
            ("NoSpecialChar1", "Password must contain at least one special character"),
            ("nouppercase123!", "Password must contain uppercase, lowercase, and numeric characters"),
            ("NOLOWERCASE123!", "Password must contain uppercase, lowercase, and numeric characters"),
            ("NoNumbers!", "Password must contain uppercase, lowercase, and numeric characters"),
            ("abc123!", "Password contains sequential characters"),
            ("123abc!", "Password contains sequential numbers")
        ]
        
        for password, expected_error in weak_passwords:
            is_valid, error = PasswordValidator.validate_password_strength(password)
            assert is_valid is False, f"Password '{password}' should be invalid"
            assert expected_error in error
    
    def test_password_sanitization(self):
        """Test password sanitization."""
        # Test password with null bytes
        password_with_null = "pass\x00word"
        sanitized = PasswordValidator.sanitize_password(password_with_null)
        assert sanitized == "password"
        
        # Test password with control characters
        password_with_control = "pass\x01word"
        sanitized = PasswordValidator.sanitize_password(password_with_control)
        assert sanitized == "password"


class TestAccountSecurity:
    """Test account security features."""
    
    def test_failed_attempt_tracking(self):
        """Test failed login attempt tracking."""
        security = AccountSecurity()
        username = "test_user"
        ip_address = "192.168.1.1"
        
        # Record failed attempts
        for i in range(4):
            should_lock = security.record_failed_attempt(username, ip_address)
            assert should_lock is False
        
        # 5th attempt should trigger lockout
        should_lock = security.record_failed_attempt(username, ip_address)
        assert should_lock is True
        
        # Account should be locked
        assert security.is_account_locked(username, ip_address) is True
    
    def test_account_lockout_expiry(self):
        """Test account lockout expiry."""
        security = AccountSecurity()
        username = "test_user"
        ip_address = "192.168.1.1"
        
        # Lock account
        for _ in range(5):
            security.record_failed_attempt(username, ip_address)
        
        assert security.is_account_locked(username, ip_address) is True
        
        # Simulate time passing (in real implementation, this would be handled by cleanup)
        # For testing, we'll manually reset the attempts
        security.failed_attempts[f"{username}:{ip_address}"]["last_attempt"] = time.time() - 301
        
        # Account should no longer be locked
        assert security.is_account_locked(username, ip_address) is False
    
    def test_successful_login_reset(self):
        """Test successful login reset."""
        security = AccountSecurity()
        username = "test_user"
        ip_address = "192.168.1.1"
        
        # Record some failed attempts
        for _ in range(3):
            security.record_failed_attempt(username, ip_address)
        
        # Reset on successful login
        security.reset_failed_attempts(username, ip_address)
        
        # Should not be locked
        assert security.is_account_locked(username, ip_address) is False


class TestSessionManager:
    """Test session management."""
    
    def test_session_creation(self):
        """Test session creation."""
        manager = SessionManager()
        user_id = "test_user"
        token = "test_token"
        ip_address = "192.168.1.1"
        
        session_id = manager.create_session(user_id, token, ip_address)
        
        assert session_id is not None
        assert session_id in manager.active_sessions
        
        session = manager.active_sessions[session_id]
        assert session['user_id'] == user_id
        assert session['token'] == token
        assert session['ip_address'] == ip_address
        assert session['is_active'] is True
    
    def test_session_validation(self):
        """Test session validation."""
        manager = SessionManager()
        user_id = "test_user"
        token = "test_token"
        ip_address = "192.168.1.1"
        
        session_id = manager.create_session(user_id, token, ip_address)
        
        # Valid session
        assert manager.validate_session(session_id, token) is True
        
        # Invalid token
        assert manager.validate_session(session_id, "invalid_token") is False
        
        # Invalid session ID
        assert manager.validate_session("invalid_session", token) is False
    
    def test_session_invalidation(self):
        """Test session invalidation."""
        manager = SessionManager()
        user_id = "test_user"
        token = "test_token"
        ip_address = "192.168.1.1"
        
        session_id = manager.create_session(user_id, token, ip_address)
        assert manager.validate_session(session_id, token) is True
        
        manager.invalidate_session(session_id)
        assert manager.validate_session(session_id, token) is False


class TestSecurityMonitor:
    """Test security monitoring."""
    
    @pytest_asyncio.fixture
    async def monitor(self):
        """Create a security monitor instance."""
        monitor = SecurityMonitor()
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    def test_event_recording(self, monitor):
        """Test security event recording."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            level=SecurityLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id="test_user",
            session_id="test_session",
            ip_address="192.168.1.1",
            details={"reason": "invalid_password"},
            source="test"
        )
        
        monitor.record_event(event)
        
        assert len(monitor.events) == 1
        assert monitor.events[0] == event
    
    def test_brute_force_detection(self, monitor):
        """Test brute force detection."""
        # Create multiple failed login events
        for i in range(5):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILED,
                level=SecurityLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                user_id="test_user",
                session_id=f"session_{i}",
                ip_address="192.168.1.1",
                details={"reason": "invalid_password"},
                source="test"
            )
            monitor.record_event(event)
        
        # Should trigger suspicious activity detection
        # This would be tested in the monitoring loop
        assert len(monitor.events) == 5
    
    def test_security_stats(self, monitor):
        """Test security statistics generation."""
        # Add some test events
        for i in range(3):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILED,
                level=SecurityLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                ip_address=f"192.168.1.{i}",
                details={"reason": "test"},
                source="test"
            )
            monitor.record_event(event)
        
        stats = monitor.get_security_stats()
        
        assert stats['total_events'] >= 3
        assert 'event_types' in stats
        assert 'security_levels' in stats


class TestTerminalSecurity:
    """Test terminal security features."""
    
    @pytest_asyncio.fixture
    async def terminal_service(self):
        """Create a terminal service instance."""
        service = TerminalService()
        return service
    
    def test_command_validation(self, terminal_service):
        """Test terminal command validation."""
        # Test valid commands
        valid_commands = [
            "ls -la",
            "cat file.txt",
            "echo 'hello world'",
            "python script.py"
        ]
        
        for command in valid_commands:
            is_valid, error = terminal_service.validate_command(command)
            assert is_valid is True, f"Command '{command}' should be valid: {error}"
        
        # Test blocked commands
        blocked_commands = [
            "sudo ls",
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown -h now"
        ]
        
        for command in blocked_commands:
            is_valid, error = terminal_service.validate_command(command)
            assert is_valid is False, f"Command '{command}' should be blocked"
    
    def test_resource_limits(self):
        """Test resource limits configuration."""
        limits = ResourceLimits()
        
        assert limits.max_cpu_time == 30
        assert limits.max_memory_mb == 512
        assert limits.max_processes == 10
        assert limits.max_file_size_mb == 10
        assert limits.max_open_files == 100


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    @pytest.mark.asyncio
    async def test_security_middleware_integration(self):
        """Test security middleware integration."""
        # This would test the full middleware stack
        # For now, we'll test individual components
        
        # Test rate limiter
        is_limited, info = await rate_limiter.is_rate_limited("test_client", 5, 60)
        assert is_limited is False
        
        # Test input validator
        is_valid, sanitized, error = input_validator.validate_and_sanitize_input("ls -la", "command")
        assert is_valid is True
        
        # Test security headers
        headers = SecurityHeaders.get_security_headers()
        assert "X-Content-Type-Options" in headers
    
    def test_auth_security_integration(self):
        """Test authentication security integration."""
        # Test password validation
        is_valid, error = password_validator.validate_password_strength("StrongPass123!")
        assert is_valid is True
        
        # Test account security
        account_security.record_failed_attempt("test_user", "192.168.1.1")
        assert account_security.is_account_locked("test_user", "192.168.1.1") is False
        
        # Test session management
        session_id = session_manager.create_session("test_user", "test_token", "192.168.1.1")
        assert session_manager.validate_session(session_id, "test_token") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 