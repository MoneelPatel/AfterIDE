"""
AfterIDE - Database Configuration

Database connection and session management for SQLAlchemy with async support.
"""

import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text, Integer
import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Determine the appropriate database URL based on the database type
def get_database_url():
    """Get the appropriate database URL based on the database type."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # For SQLite, use aiosqlite for async support
        return settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif settings.DATABASE_URL.startswith("postgresql"):
        # For PostgreSQL, use asyncpg for async support
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        return settings.DATABASE_URL

# Create async engine based on database type
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL supports connection pooling
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Database compatibility layer
def get_uuid_column():
    """Get appropriate UUID column type based on database."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # For SQLite, use String with UUID conversion
        from sqlalchemy import String
        return String(36)
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)

def get_uuid_default():
    """Get appropriate UUID default function based on database."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # For SQLite, use string UUID
        return lambda: str(uuid.uuid4())
    else:
        # For PostgreSQL, use native UUID
        return uuid.uuid4

def get_json_column():
    """Get appropriate JSON column type based on database."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # For SQLite, use Text with JSON validation
        return Text
    else:
        from sqlalchemy.dialects.postgresql import JSONB
        return JSONB

def get_boolean_column():
    """Get appropriate boolean column type based on database."""
    from sqlalchemy import Boolean
    return Boolean

async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed") 