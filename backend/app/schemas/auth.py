"""
AfterIDE - Authentication Schemas

Pydantic schemas for authentication requests and responses.
"""

from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    """User login request schema."""
    username: str
    password: str

class UserResponse(BaseModel):
    """User response schema."""
    id: str
    username: str
    email: str
    role: str
    is_active: Optional[bool] = True
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str
    expires_in: int
    user: Optional[UserResponse] = None 