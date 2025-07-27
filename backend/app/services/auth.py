"""
AfterIDE - Authentication Service

Handles user authentication, JWT token management, and password operations.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserLogin, TokenResponse

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
    async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            User dictionary if authentication successful, None otherwise
        """
        # TODO: Implement database lookup
        # For now, return a mock user for development
        if username == "admin" and password == "password":
            return {
                "id": "mock-user-id",
                "username": "admin",
                "email": "admin@afteride.com",
                "role": "admin"
            }
        return None
    
    @staticmethod
    async def login_user(user_credentials: UserLogin) -> Optional[TokenResponse]:
        """
        Authenticate user and return access token.
        
        Args:
            user_credentials: User login credentials
            
        Returns:
            TokenResponse with access token if successful, None otherwise
        """
        user = await AuthService.authenticate_user(
            user_credentials.username, 
            user_credentials.password
        )
        
        if not user:
            return None
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": str(user["id"]), "username": user["username"]},
            expires_delta=access_token_expires
        )
        
        logger.info("User logged in successfully", user_id=str(user["id"]), username=user["username"])
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def get_current_user(token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            User dictionary if token valid, None otherwise
        """
        payload = AuthService.verify_token(token)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # TODO: Implement database lookup
        # For now, return a mock user
        return {
            "id": user_id,
            "username": payload.get("username", "unknown"),
            "email": "user@afteride.com",
            "role": "user"
        } 