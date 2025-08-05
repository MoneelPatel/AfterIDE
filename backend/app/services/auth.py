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
import re
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.session import Session, SessionStatus
from app.schemas.auth import UserLogin, UserRegister, TokenResponse, UserResponse

logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Password validation and security."""
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            return False, "Password is too common"
        
        # Check for character variety
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numeric characters"
        
        if not has_special:
            return False, "Password must contain at least one special character"
        
        # Check for sequential characters
        if any(password[i:i+3] in 'abcdefghijklmnopqrstuvwxyz' for i in range(len(password)-2)):
            return False, "Password contains sequential characters"
        
        if any(password[i:i+3] in '0123456789' for i in range(len(password)-2)):
            return False, "Password contains sequential numbers"
        
        return True, ""
    
    @staticmethod
    def sanitize_password(password: str) -> str:
        """Sanitize password input."""
        # Remove null bytes and control characters
        password = ''.join(c for c in password if c.isprintable())
        return password.strip()


class AccountSecurity:
    """Account security and lockout management."""
    
    def __init__(self):
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
        self.lockout_duration = 300  # 5 minutes
        self.max_failed_attempts = 5
    
    def record_failed_attempt(self, username: str, ip_address: str) -> bool:
        """Record a failed login attempt."""
        key = f"{username}:{ip_address}"
        current_time = time.time()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time
            }
        
        self.failed_attempts[key]['count'] += 1
        self.failed_attempts[key]['last_attempt'] = current_time
        
        # Check if account should be locked
        if self.failed_attempts[key]['count'] >= self.max_failed_attempts:
            return True  # Account should be locked
        
        return False
    
    def is_account_locked(self, username: str, ip_address: str) -> bool:
        """Check if account is locked due to failed attempts."""
        key = f"{username}:{ip_address}"
        
        if key not in self.failed_attempts:
            return False
        
        current_time = time.time()
        last_attempt = self.failed_attempts[key]['last_attempt']
        
        # Check if lockout period has expired
        if current_time - last_attempt > self.lockout_duration:
            # Reset failed attempts
            del self.failed_attempts[key]
            return False
        
        # Check if account is locked
        return self.failed_attempts[key]['count'] >= self.max_failed_attempts
    
    def reset_failed_attempts(self, username: str, ip_address: str):
        """Reset failed attempts for successful login."""
        key = f"{username}:{ip_address}"
        self.failed_attempts.pop(key, None)
    
    def get_lockout_remaining(self, username: str, ip_address: str) -> int:
        """Get remaining lockout time in seconds."""
        key = f"{username}:{ip_address}"
        
        if key not in self.failed_attempts:
            return 0
        
        current_time = time.time()
        last_attempt = self.failed_attempts[key]['last_attempt']
        remaining = self.lockout_duration - (current_time - last_attempt)
        
        return max(0, int(remaining))


class SessionManager:
    """Session management and security."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour
    
    def create_session(self, user_id: str, token: str, ip_address: str) -> str:
        """Create a new session."""
        session_id = f"{user_id}_{int(time.time())}"
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'token': token,
            'ip_address': ip_address,
            'created_at': time.time(),
            'last_activity': time.time(),
            'is_active': True
        }
        
        return session_id
    
    def validate_session(self, session_id: str, token: str) -> bool:
        """Validate session and update activity."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Check if session is active
        if not session['is_active']:
            return False
        
        # Check if session has expired
        if time.time() - session['last_activity'] > self.session_timeout:
            session['is_active'] = False
            return False
        
        # Check if token matches
        if session['token'] != token:
            return False
        
        # Update last activity
        session['last_activity'] = time.time()
        
        return True
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['is_active'] = False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session['last_activity'] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]


# Global instances
password_validator = PasswordValidator()
account_security = AccountSecurity()
session_manager = SessionManager()


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
        """Create JWT access token with enhanced security."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add additional security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.PROJECT_NAME,
            "aud": "afteride-users"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token with enhanced validation."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM],
                issuer=settings.PROJECT_NAME,
                audience="afteride-users"
            )
            
            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                return None
            
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
        # Query user from database (case-insensitive)
        result = await db.execute(
            select(User).where(User.username.ilike(username))
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
    async def register_user(db: AsyncSession, user_data: UserRegister) -> User:
        """
        Register a new user with enhanced security validation.
        """
        # Validate password strength
        is_valid, error_message = password_validator.validate_password_strength(user_data.password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {error_message}")
        
        # Sanitize password
        sanitized_password = password_validator.sanitize_password(user_data.password)
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                (User.username == user_data.username) | (User.email == user_data.email)
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError("Username already registered")
            else:
                raise ValueError("Email already registered")
        
        # Create new user
        hashed_password = AuthService.get_password_hash(sanitized_password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("New user registered", username=user_data.username, email=user_data.email)
        
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
    async def login_user(db: AsyncSession, user_credentials: UserLogin, ip_address: str = None) -> Optional[TokenResponse]:
        """
        Authenticate user and return access token with enhanced security.
        """
        try:
            # Check for account lockout
            if account_security.is_account_locked(user_credentials.username, ip_address or "unknown"):
                remaining_time = account_security.get_lockout_remaining(user_credentials.username, ip_address or "unknown")
                logger.warning("Login attempt on locked account", 
                             username=user_credentials.username, ip_address=ip_address)
                raise ValueError(f"Account is temporarily locked. Try again in {remaining_time} seconds.")
            
            # Get user from database
            result = await db.execute(
                select(User).where(User.username == user_credentials.username)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                # Record failed attempt
                account_security.record_failed_attempt(user_credentials.username, ip_address or "unknown")
                logger.warning("Failed login attempt - invalid credentials", 
                             username=user_credentials.username, ip_address=ip_address)
                return None
            
            # Verify password
            if not AuthService.verify_password(user_credentials.password, user.hashed_password):
                # Record failed attempt
                account_security.record_failed_attempt(user_credentials.username, ip_address or "unknown")
                
                # Check if account should be locked
                if account_security.is_account_locked(user_credentials.username, ip_address or "unknown"):
                    logger.warning("Account locked due to failed attempts", 
                                 username=user_credentials.username, ip_address=ip_address)
                    raise ValueError("Account has been locked due to multiple failed attempts.")
                
                logger.warning("Failed login attempt - invalid password", 
                             username=user_credentials.username, ip_address=ip_address)
                return None
            
            # Reset failed attempts on successful login
            account_security.reset_failed_attempts(user_credentials.username, ip_address or "unknown")
            
            # Update last login
            user.last_login = datetime.utcnow()
            await db.commit()
            
            # Create access token
            access_token = AuthService.create_access_token(
                data={"sub": str(user.id), "username": user.username, "role": user.role.value}
            )
            
            # Create session
            session_id = session_manager.create_session(str(user.id), access_token, ip_address or "unknown")
            
            logger.info("User logged in successfully", 
                       username=user.username, ip_address=ip_address, session_id=session_id)
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                session_id=session_id
            )
            
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error("Login error", error=str(e), username=user_credentials.username)
            return None
    
    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
        """
        Get current user from JWT token with session validation.
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
    
    @staticmethod
    async def logout_user(token: str, session_id: str = None) -> bool:
        """
        Logout user by invalidating token and session.
        """
        try:
            if session_id:
                session_manager.invalidate_session(session_id)
            
            # In a production environment, you might want to add the token to a blacklist
            logger.info("User logged out", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("Logout error", error=str(e))
            return False
    
    @staticmethod
    async def change_password(db: AsyncSession, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password with validation.
        """
        try:
            # Get user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Verify current password
            if not AuthService.verify_password(current_password, user.hashed_password):
                return False
            
            # Validate new password
            is_valid, error_message = password_validator.validate_password_strength(new_password)
            if not is_valid:
                raise ValueError(f"Password validation failed: {error_message}")
            
            # Sanitize new password
            sanitized_password = password_validator.sanitize_password(new_password)
            
            # Hash new password
            new_hashed_password = AuthService.get_password_hash(sanitized_password)
            
            # Update password
            user.hashed_password = new_hashed_password
            await db.commit()
            
            logger.info("Password changed successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Password change error", error=str(e), user_id=user_id)
            return False
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions."""
        session_manager.cleanup_expired_sessions()