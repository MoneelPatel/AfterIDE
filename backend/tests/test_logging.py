"""
Tests for the logging module.

Tests structured logging configuration and utility functions.
"""

import pytest
from unittest.mock import patch, MagicMock
import structlog
import logging
import sys

from app.core.logging import (
    setup_logging, get_logger, log_execution_event, 
    log_security_event, log_performance_metric
)


class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    def test_setup_logging_called(self):
        """Test that setup_logging can be called without errors."""
        with patch('app.core.logging.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_FORMAT = "console"
            
            # Should not raise any exceptions
            setup_logging()
    
    def test_setup_logging_json_format(self):
        """Test logging setup with JSON format."""
        with patch('app.core.logging.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_FORMAT = "json"
            
            with patch('structlog.configure') as mock_configure:
                setup_logging()
                
                # Verify structlog.configure was called
                mock_configure.assert_called_once()
                
                # Check that JSONRenderer is used
                call_args = mock_configure.call_args
                processors = call_args[1]['processors']
                json_processor_found = any(
                    'JSONRenderer' in str(processor) for processor in processors
                )
                assert json_processor_found
    
    def test_setup_logging_console_format(self):
        """Test logging setup with console format."""
        with patch('app.core.logging.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_FORMAT = "console"
            
            with patch('structlog.configure') as mock_configure:
                setup_logging()
                
                # Verify structlog.configure was called
                mock_configure.assert_called_once()
                
                # Check that ConsoleRenderer is used
                call_args = mock_configure.call_args
                processors = call_args[1]['processors']
                console_processor_found = any(
                    'ConsoleRenderer' in str(processor) for processor in processors
                )
                assert console_processor_found
    
    def test_setup_logging_different_levels(self):
        """Test logging setup with different log levels."""
        test_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in test_levels:
            with patch('app.core.logging.settings') as mock_settings:
                mock_settings.LOG_LEVEL = level
                mock_settings.LOG_FORMAT = "console"
                
                with patch('logging.basicConfig') as mock_basic_config:
                    setup_logging()
                    
                    # Verify basicConfig was called with correct level
                    mock_basic_config.assert_called_once()
                    call_args = mock_basic_config.call_args
                    assert call_args[1]['level'] == getattr(logging, level)


class TestLoggerFunctions:
    """Test logger utility functions."""
    
    def test_get_logger(self):
        """Test getting a logger."""
        from app.core.logging import get_logger
        
        logger = get_logger("test.module")
        
        # structlog returns a BoundLoggerLazyProxy, not a BoundLogger directly
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')

    def test_get_logger_different_names(self):
        """Test getting loggers with different names."""
        from app.core.logging import get_logger
        
        logger1 = get_logger("app.main")
        logger2 = get_logger("app.services")
        
        # Both should be valid loggers
        assert logger1 is not None
        assert logger2 is not None
        assert hasattr(logger1, 'info')
        assert hasattr(logger2, 'info')


class TestLoggingUtilities:
    """Test logging utility functions."""
    
    def test_log_execution_event(self):
        """Test logging execution events."""
        mock_logger = MagicMock()
        
        log_execution_event(
            logger=mock_logger,
            session_id="test-session",
            command="python script.py",
            success=True,
            execution_time_ms=150.5,
            memory_usage_mb=25.3,
            output_size_bytes=1024
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert call_args[0][0] == "code_execution_completed"
        assert call_args[1]['session_id'] == "test-session"
        assert call_args[1]['command'] == "python script.py"
        assert call_args[1]['success'] is True
        assert call_args[1]['execution_time_ms'] == 150.5
        assert call_args[1]['memory_usage_mb'] == 25.3
        assert call_args[1]['output_size_bytes'] == 1024
    
    def test_log_execution_event_with_kwargs(self):
        """Test logging execution events with additional kwargs."""
        mock_logger = MagicMock()
        
        log_execution_event(
            logger=mock_logger,
            session_id="test-session",
            command="python script.py",
            success=False,
            execution_time_ms=100.0,
            error_message="Syntax error",
            exit_code=1
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert call_args[1]['error_message'] == "Syntax error"
        assert call_args[1]['exit_code'] == 1
    
    def test_log_security_event(self):
        """Test logging security events."""
        mock_logger = MagicMock()
        
        log_security_event(
            logger=mock_logger,
            event_type="unauthorized_access",
            session_id="test-session",
            user_id="user123",
            details={"ip": "192.168.1.1", "attempt": 3}
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        assert call_args[0][0] == "security_event"
        assert call_args[1]['event_type'] == "unauthorized_access"
        assert call_args[1]['session_id'] == "test-session"
        assert call_args[1]['user_id'] == "user123"
        assert call_args[1]['details']['ip'] == "192.168.1.1"
        assert call_args[1]['details']['attempt'] == 3
    
    def test_log_security_event_no_user_id(self):
        """Test logging security events without user_id."""
        mock_logger = MagicMock()
        
        log_security_event(
            logger=mock_logger,
            event_type="invalid_token",
            session_id="test-session"
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        assert call_args[1]['user_id'] is None
        assert call_args[1]['details'] == {}
    
    def test_log_performance_metric(self):
        """Test logging performance metrics."""
        mock_logger = MagicMock()
        
        log_performance_metric(
            logger=mock_logger,
            metric_name="response_time",
            value=45.2,
            unit="ms",
            session_id="test-session"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert call_args[0][0] == "performance_metric"
        assert call_args[1]['metric_name'] == "response_time"
        assert call_args[1]['value'] == 45.2
        assert call_args[1]['unit'] == "ms"
        assert call_args[1]['session_id'] == "test-session"
    
    def test_log_performance_metric_no_session(self):
        """Test logging performance metrics without session_id."""
        mock_logger = MagicMock()
        
        log_performance_metric(
            logger=mock_logger,
            metric_name="cpu_usage",
            value=75.5,
            unit="percent"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert call_args[1]['session_id'] is None
        assert call_args[1]['unit'] == "percent"
    
    def test_log_performance_metric_with_kwargs(self):
        """Test logging performance metrics with additional kwargs."""
        mock_logger = MagicMock()
        
        log_performance_metric(
            logger=mock_logger,
            metric_name="memory_usage",
            value=512.0,
            unit="MB",
            session_id="test-session",
            peak_usage=True,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        assert call_args[1]['peak_usage'] is True
        assert call_args[1]['timestamp'] == "2023-01-01T00:00:00Z"


class TestLoggingIntegration:
    """Test logging integration with structlog."""
    
    def test_logger_chain(self):
        """Test that logger chain works correctly."""
        # Setup logging
        with patch('app.core.logging.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_FORMAT = "console"
            
            setup_logging()
            
            # Get logger and test basic functionality
            logger = get_logger("test.integration")
            
            # Test that logger can be called without errors
            # (we can't easily test the output without complex mocking)
            assert logger is not None
            assert hasattr(logger, 'info')
            assert hasattr(logger, 'warning')
            assert hasattr(logger, 'error') 