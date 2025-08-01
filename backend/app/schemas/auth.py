"""
AfterIDE - Authentication Schemas

Pydantic schemas for authentication requests and responses.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserLogin(BaseModel):
    """User login request schema."""
    username: str
    password: str

class UserRegister(BaseModel):
    """User registration request schema."""
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

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