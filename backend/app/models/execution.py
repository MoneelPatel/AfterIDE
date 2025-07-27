"""
AfterIDE - Execution Model

Execution tracking for code commands and their results.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


class Execution(Base):
    """Execution model for tracking code execution history and results."""
    
    __tablename__ = "executions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Execution information
    command = Column(Text, nullable=False)
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    
    # Execution results
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    memory_usage_mb = Column(Integer, nullable=True)  # Peak memory usage in MB
    cpu_usage_percent = Column(Integer, nullable=True)  # Peak CPU usage percentage
    
    # Security and monitoring
    security_events = Column(JSONB, default=list, nullable=False)  # Security violations, warnings
    resource_limits_exceeded = Column(Boolean, default=False, nullable=False)
    
    # Container information
    container_id = Column(String(100), nullable=True)  # Docker container used for execution
    process_id = Column(Integer, nullable=True)  # Process ID within container
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="executions")
    
    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, command='{self.command[:50]}...', status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if execution has completed (success or failure)."""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT, ExecutionStatus.KILLED]
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED and self.return_code == 0
    
    @property
    def output_size_bytes(self) -> int:
        """Calculate total output size in bytes."""
        stdout_size = len(self.stdout.encode('utf-8')) if self.stdout else 0
        stderr_size = len(self.stderr.encode('utf-8')) if self.stderr else 0
        return stdout_size + stderr_size 