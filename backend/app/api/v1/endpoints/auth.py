"""
AfterIDE - Authentication API Endpoints

REST API endpoints for user authentication and authorization.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister, UserResponse, TokenResponse
from app.services.auth import AuthService
from app.core.database import get_db

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Args:
        user_credentials: User login credentials
        db: Database session
        
    Returns:
        TokenResponse with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    token_response = await AuthService.login_user(db, user_credentials)
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_response

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and create their default workspace.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse with created user information
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Register the user
        user = await AuthService.register_user(db, user_data)
        
        # Create default session for the user
        await AuthService.create_user_session(db, user)
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and invalidate token.
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        Success message
    """
    try:
        await AuthService.logout_user(credentials.credentials)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.
    
    Args:
        credentials: HTTP Bearer token
        db: Database session
        
    Returns:
        UserResponse with current user information
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        user = await AuthService.get_current_user(credentials.credentials, db)
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current user for other endpoints.
    
    Args:
        credentials: HTTP Bearer token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        return await AuthService.get_current_user(credentials.credentials, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.get("/status")
async def auth_status():
    """Get authentication service status."""
    return {
        "message": "Authentication service is running",
        "status": "active"
    } 