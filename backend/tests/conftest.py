"""
Pytest configuration and fixtures for backend tests.

This file provides common fixtures used across all backend tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.core.database import Base
from app.models.user import User, UserRole
from app.models.session import Session, SessionStatus
from app.models.file import File
from app.models.submission import Submission, SubmissionStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest.fixture
async def test_db_session_factory(test_db_engine):
    """Create a test database session factory."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return async_session


@pytest.fixture
async def db_session(test_db_session_factory):
    """Create a test database session."""
    async with test_db_session_factory() as session:
        yield session
        # Clean up any changes
        await session.rollback()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """Create a test admin user."""
    admin = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_reviewer(db_session: AsyncSession):
    """Create a test reviewer user."""
    reviewer = User(
        id=str(uuid.uuid4()),
        username="reviewer",
        email="reviewer@example.com",
        hashed_password="hashed_password",
        role=UserRole.REVIEWER
    )
    db_session.add(reviewer)
    await db_session.commit()
    await db_session.refresh(reviewer)
    return reviewer


@pytest.fixture
async def test_session(db_session: AsyncSession, test_user: User):
    """Create a test session."""
    session = Session(
        id=str(uuid.uuid4()),
        name="Test Session",
        user_id=str(test_user.id),
        status=SessionStatus.ACTIVE
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_file(db_session: AsyncSession, test_session: Session):
    """Create a test file."""
    file = File(
        id=str(uuid.uuid4()),
        filename="test.py",
        filepath="/test.py",
        language="python",
        content="print('hello world')",
        session_id=str(test_session.id)
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file


@pytest.fixture
async def test_submission(db_session: AsyncSession, test_user: User, test_file: File, test_admin: User):
    """Create a test submission."""
    submission = Submission(
        id=str(uuid.uuid4()),
        title="Test Submission",
        description="Test description",
        file_id=str(test_file.id),
        user_id=str(test_user.id),
        reviewer_id=str(test_admin.id),
        status=SubmissionStatus.PENDING
    )
    db_session.add(submission)
    await db_session.commit()
    await db_session.refresh(submission)
    return submission


@pytest.fixture
def mock_db():
    """Create a mock database session for unit tests."""
    return AsyncMock(spec=AsyncSession)


# Override the get_db dependency for testing
@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency to use test database."""
    async def _override_get_db():
        yield db_session
    
    return _override_get_db 