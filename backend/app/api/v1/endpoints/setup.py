"""
AfterIDE - Setup API Endpoints

One-time setup endpoints for initializing the application.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.auth import AuthService
from app.models.session import Session, SessionStatus
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/create-admin")
async def create_admin_user(db: AsyncSession = get_db):
    """
    Create a default admin user for the application.
    This endpoint should only be called once during initial setup.
    """
    try:
        # Check if admin user already exists
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return {
                "message": "Admin user already exists",
                "username": "admin",
                "email": existing_user.email,
                "role": existing_user.role.value
            }
        
        # Create admin user
        hashed_password = AuthService.get_password_hash("password")
        admin_user = User(
            username="admin",
            email="admin@afteride.com",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            preferences={}
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        # Create default session for admin
        admin_session = Session(
            user_id=admin_user.id,
            name="Admin Workspace",
            description="Administrator development workspace",
            status=SessionStatus.ACTIVE.value,
            config={
                "python_version": "3.11",
                "packages": ["requests", "pandas", "numpy", "fastapi"],
                "environment_vars": {}
            },
            max_memory_mb=1024,
            max_cpu_cores=2,
            max_execution_time=60,
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        
        db.add(admin_session)
        await db.commit()
        
        logger.info("Admin user created successfully", 
                   user_id=str(admin_user.id), 
                   username=admin_user.username)
        
        return {
            "message": "Admin user created successfully",
            "username": "admin",
            "password": "password",
            "email": "admin@afteride.com",
            "role": admin_user.role.value,
            "session": admin_session.name
        }
        
    except Exception as e:
        logger.error("Failed to create admin user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}"
        ) 