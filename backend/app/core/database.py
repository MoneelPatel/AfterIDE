"""
AfterIDE - Database Configuration

SQLAlchemy database configuration and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Determine the appropriate database URL based on the database type
def get_database_url():
    """Get the appropriate database URL with correct driver."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # For SQLite, use aiosqlite for async support
        return settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif settings.DATABASE_URL.startswith("postgresql"):
        # For PostgreSQL, use asyncpg for async support
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        return settings.DATABASE_URL

# Create async engine with appropriate configuration
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support connection pooling, use NullPool
    engine = create_async_engine(
        get_database_url(),
        poolclass=NullPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL supports connection pooling
    engine = create_async_engine(
        get_database_url(),
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import user, session, file, execution, submission
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed") 