"""
Backend Integration Tests Configuration

Shared fixtures and configuration for backend integration tests.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
import sys
import json
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_application
from app.core.database import get_db, Base
from app.core.config import settings
from app.services.auth import AuthService
from app.services.session import SessionService
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing with async support
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_db_session_factory(test_db_engine):
    """Create a test database session factory."""
    TestingSessionLocal = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return TestingSessionLocal


@pytest_asyncio.fixture
async def test_db_session(test_db_engine, test_db_session_factory):
    """Create a test database session."""
    # Create tables
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with test_db_session_factory() as session:
        yield session
        
        # Cleanup
        await session.rollback()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "email": "test@example.com"
    }


@pytest_asyncio.fixture
async def test_user(test_db_session, test_user_data):
    """Create a test user in the database."""
    from sqlalchemy import select
    
    # Check if user already exists
    stmt = select(User).where(User.username == test_user_data["username"])
    result = await test_db_session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return existing_user
    
    # Create new user
    hashed_password = AuthService.get_password_hash(test_user_data["password"])
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=hashed_password,
        is_active=True,
        preferences=json.dumps({})  # Convert dict to JSON string for SQLite
    )
    
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    
    return user


@pytest.fixture
def app(test_db_engine):
    """Create a test FastAPI application."""
    async def override_get_db():
        # Create a new session for each request
        TestingSessionLocal = sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with TestingSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app = create_application()
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client(app) -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app):
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def authenticated_user(client, test_user, test_user_data):
    """Create and authenticate a test user."""
    # Login to get token using mock admin credentials
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "password"
        }
    )
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        return {
            "user": {"username": "admin", "email": "admin@afteride.com", "role": "admin"},
            "token": token_data["access_token"],
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
        }
    else:
        # If login fails, raise an error with details
        pytest.fail(f"Login failed with status {login_response.status_code}: {login_response.text}")


@pytest_asyncio.fixture
async def test_session(authenticated_user, test_db_session):
    """Create a test development session."""
    session_service = SessionService(test_db_session)
    session = await session_service.create_session(
        user_id="mock-user-id",
        name="Test Session",
        description="Integration test session",
        config={"test": True}
    )
    return session


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_websocket_manager():
    """Create a mock WebSocket manager."""
    mock_manager = AsyncMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.send_message = AsyncMock()
    return mock_manager


@pytest.fixture
def mock_workspace_service():
    """Create a mock workspace service."""
    mock_service = AsyncMock()
    mock_service.get_workspace_files = AsyncMock(return_value=[])
    mock_service.get_file_content = AsyncMock(return_value="")
    mock_service.save_file = AsyncMock(return_value={"id": 1, "filepath": "/test.py"})
    mock_service.delete_file = AsyncMock(return_value=True)
    mock_service.create_folder = AsyncMock(return_value="/test-folder")
    return mock_service 