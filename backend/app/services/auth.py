"""
AfterIDE - Authentication Service

Handles user authentication, JWT token management, and password operations.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.session import Session, SessionStatus
from app.schemas.auth import UserLogin, UserRegister, TokenResponse, UserResponse

logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT operations."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning("JWT token verification failed", error=str(e))
            return None
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Query user from database
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> Optional[User]:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            User object if registration successful, None otherwise
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("Username already exists")
        
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already exists")
        
        # Create new user
        hashed_password = AuthService.get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=1,  # Use integer for SQLite compatibility
            preferences=json.dumps({})  # Convert dict to JSON string for SQLite
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("New user registered", user_id=str(user.id), username=user.username)
        
        return user
    
    @staticmethod
    async def create_user_session(db: AsyncSession, user: User) -> Session:
        """
        Create a default session for a new user.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            Session object
        """
        # Create default session
        session = Session(
            user_id=user.id,
            name="Default Workspace",
            description="Your personal development workspace",
            status=SessionStatus.ACTIVE.value,
            config=json.dumps({
                "python_version": "3.11",
                "packages": ["requests", "pandas", "numpy"],
                "environment_vars": {}
            }),
            max_memory_mb=512,
            max_cpu_cores=1,
            max_execution_time=30,
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30 day expiry
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info("Default session created for user", user_id=str(user.id), session_id=str(session.id))
        
        return session
    
    @staticmethod
    async def login_user(db: AsyncSession, user_credentials: UserLogin) -> Optional[TokenResponse]:
        """
        Authenticate user and return access token.
        
        Args:
            db: Database session
            user_credentials: User login credentials
            
        Returns:
            TokenResponse with access token if successful, None otherwise
        """
        user = await AuthService.authenticate_user(db, user_credentials.username, user_credentials.password)
        
        if not user:
            return None
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        logger.info("User logged in successfully", user_id=str(user.id), username=user.username)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role.value,
                is_active=bool(user.is_active)  # Convert integer back to boolean
            )
        )
    
    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            User object if token valid, None otherwise
        """
        payload = AuthService.verify_token(token)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Query user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user 