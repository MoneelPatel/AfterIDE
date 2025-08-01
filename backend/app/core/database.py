"""
AfterIDE - Database Configuration

Database connection and session management for SQLAlchemy with async support.
"""

import os
import uuid

# Try to import SQLAlchemy, fallback if not available
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy import Column, String, Text, Integer
    SQLALCHEMY_AVAILABLE = True
except ImportError as e:
    SQLALCHEMY_AVAILABLE = False
    print(f"⚠️  SQLAlchemy not available: {e}")
    print("⚠️  Database functionality will be limited")

# Try to import structlog, fallback to basic logging
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Try to import settings, fallback to basic settings
try:
    from app.core.config import settings
except ImportError:
    # Fallback settings
    class FallbackSettings:
        DATABASE_URL = "sqlite:///./afteride.db"
        DEBUG = False
        DATABASE_POOL_SIZE = 20
        DATABASE_MAX_OVERFLOW = 30
        DATABASE_POOL_RECYCLE = 3600
    settings = FallbackSettings()

if SQLALCHEMY_AVAILABLE:
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
    try:
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

    except Exception as e:
        print(f"⚠️  Database engine creation failed: {e}")
        # Create fallback objects
        engine = None
        AsyncSessionLocal = None
        Base = None

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
            # For SQLite, convert UUID to string
            return lambda: str(uuid.uuid4())
        else:
            # For PostgreSQL, use UUID directly
            return uuid.uuid4

    def get_json_column():
        """Get appropriate JSON column type based on database."""
        if settings.DATABASE_URL.startswith("sqlite"):
            return Text  # SQLite uses TEXT for JSON
        else:
            from sqlalchemy.dialects.postgresql import JSONB
            return JSONB

    def get_boolean_column():
        """Get appropriate boolean column type based on database."""
        if settings.DATABASE_URL.startswith("sqlite"):
            # For SQLite, use Integer for boolean (0/1)
            return Integer
        else:
            from sqlalchemy import Boolean
            return Boolean

    async def get_db() -> AsyncSession:
        """
        Dependency to get database session.
        
        Yields:
            AsyncSession: Database session
        """
        if AsyncSessionLocal is None:
            raise RuntimeError("Database not available")
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    async def init_db() -> None:
        """Initialize database tables."""
        if engine is None or Base is None:
            logger.warning("Database not available, skipping initialization")
            return
        
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    async def close_db() -> None:
        """Close database connections."""
        if engine is not None:
            await engine.dispose()
            logger.info("Database connections closed")

else:
    # Fallback implementations when SQLAlchemy is not available
    print("⚠️  Using fallback database implementation")
    
    # Create dummy objects
    engine = None
    AsyncSessionLocal = None
    Base = None
    
    def get_uuid_column():
        return None
    
    def get_uuid_default():
        return lambda: str(uuid.uuid4())
    
    def get_json_column():
        return None
    
    def get_boolean_column():
        return None
    
    async def get_db():
        """Fallback database session."""
        logger.warning("Database not available, using fallback")
        yield None
    
    async def init_db() -> None:
        """Fallback database initialization."""
        logger.warning("Database not available, skipping initialization")
    
    async def close_db() -> None:
        """Fallback database cleanup."""
        logger.warning("Database not available, no cleanup needed") 