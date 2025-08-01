"""
AfterIDE - Logging Configuration

Structured logging setup using structlog for comprehensive application logging.
"""

import logging
import sys
from typing import Any, Dict

# Try to import structlog, fallback to basic logging if not available
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("⚠️  structlog not available, using basic logging")

# Try to import pythonjsonlogger, but it's not actually used in this code
try:
    from pythonjsonlogger import jsonlogger
    JSONLOGGER_AVAILABLE = True
except ImportError:
    JSONLOGGER_AVAILABLE = False
    print("⚠️  pythonjsonlogger not available, but not needed for basic functionality")

# Import settings with fallback
try:
    from app.core.config import settings
except ImportError:
    # Fallback settings if config import fails
    class FallbackSettings:
        LOG_LEVEL = "INFO"
        LOG_FORMAT = "console"
    settings = FallbackSettings()


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    if STRUCTLOG_AVAILABLE:
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, settings.LOG_LEVEL.upper()),
        )
        
        # Configure structlog
        structlog.configure(
            processors=[
                # Add timestamp and log level
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                
                # JSON formatting for production, console for development
                structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
                else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Fallback to basic logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
            level=getattr(logging, settings.LOG_LEVEL.upper()),
        )
        print("⚠️  Using basic logging (structlog not available)")


def get_logger(name: str):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance (structlog or basic logging)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


# Common logging utilities
def log_execution_event(
    logger,
    session_id: str,
    command: str,
    success: bool,
    execution_time_ms: float,
    memory_usage_mb: float = 0.0,
    output_size_bytes: int = 0,
    **kwargs: Any
) -> None:
    """
    Log code execution events with consistent format.
    
    Args:
        logger: Logger instance
        session_id: Session identifier
        command: Executed command
        success: Whether execution was successful
        execution_time_ms: Execution time in milliseconds
        memory_usage_mb: Peak memory usage in MB
        output_size_bytes: Size of output in bytes
        **kwargs: Additional context data
    """
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "code_execution_completed",
            session_id=session_id,
            command=command,
            success=success,
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            output_size_bytes=output_size_bytes,
            **kwargs
        )
    else:
        logger.info(
            f"Code execution completed - Session: {session_id}, Command: {command}, "
            f"Success: {success}, Time: {execution_time_ms}ms"
        )


def log_security_event(
    logger,
    event_type: str,
    session_id: str,
    user_id: str = None,
    details: Dict[str, Any] = None,
    **kwargs: Any
) -> None:
    """
    Log security events with consistent format.
    
    Args:
        logger: Logger instance
        event_type: Type of security event
        session_id: Session identifier
        user_id: User identifier (if available)
        details: Additional event details
        **kwargs: Additional context data
    """
    if STRUCTLOG_AVAILABLE:
        logger.warning(
            "security_event",
            event_type=event_type,
            session_id=session_id,
            user_id=user_id,
            details=details or {},
            **kwargs
        )
    else:
        logger.warning(
            f"Security event - Type: {event_type}, Session: {session_id}, "
            f"User: {user_id}, Details: {details or {}}"
        )


def log_performance_metric(
    logger,
    metric_name: str,
    value: float,
    unit: str = None,
    session_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log performance metrics with consistent format.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        session_id: Session identifier (if applicable)
        **kwargs: Additional context data
    """
    if STRUCTLOG_AVAILABLE:
        logger.info(
            "performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            session_id=session_id,
            **kwargs
        )
    else:
        logger.info(
            f"Performance metric - {metric_name}: {value}{unit or ''}, "
            f"Session: {session_id or 'N/A'}"
        ) 