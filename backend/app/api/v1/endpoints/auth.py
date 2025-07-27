"""
AfterIDE - Authentication API Endpoints

REST API endpoints for user authentication and authorization.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from app.models.user import User
from app.schemas.auth import UserLogin, UserResponse, TokenResponse
from app.services.auth import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """
    Authenticate user and return access token.
    
    Args:
        user_credentials: User login credentials
        
    Returns:
        TokenResponse with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    token_response = await AuthService.login_user(user_credentials)
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_response


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and invalidate token.
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        Success message
    """
    # TODO: Implement token invalidation (add to blacklist)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user information.
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        UserResponse with user information
        
    Raises:
        HTTPException: If token is invalid
    """
    user = await AuthService.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse(
        id=str(user["id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"]
    )


@router.post("/register", response_model=UserResponse)
async def register_user(user_credentials: UserLogin):
    """
    Register a new user.
    
    Args:
        user_credentials: User registration credentials
        
    Returns:
        UserResponse with created user information
        
    Raises:
        HTTPException: If registration fails
    """
    # TODO: Implement user registration with database
    # For now, return a mock response
    return UserResponse(
        id="new-user-id",
        username=user_credentials.username,
        email=f"{user_credentials.username}@afteride.com",
        role="user"
    )


# Dependency for protected endpoints
async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        User dictionary
        
    Raises:
        HTTPException: If token is invalid
    """
    user = await AuthService.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user 