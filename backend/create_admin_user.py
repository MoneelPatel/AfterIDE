#!/usr/bin/env python3
"""
AfterIDE - Create Default Admin User

Script to create a default admin user for development and testing.
"""

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.services.auth import AuthService
from app.models.session import Session, SessionStatus
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

async def create_admin_user():
    """Create a default admin user."""
    try:
        # Initialize database
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # Check if admin user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("Admin user already exists", username="admin")
                return
            
            # Create admin user
            hashed_password = AuthService.get_password_hash("password")
            admin_user = User(
                username="admin",
                email="admin@afteride.com",
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_active=1,  # Use integer for SQLite compatibility
                preferences=json.dumps({})  # Convert dict to JSON string for SQLite
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            # Create default session for admin
            admin_session = Session(
                user_id=admin_user.id,
                name="Admin Workspace",
                description="Administrator development workspace",
                status=SessionStatus.ACTIVE.value,
                config=json.dumps({
                    "python_version": "3.11",
                    "packages": ["requests", "pandas", "numpy", "fastapi"],
                    "environment_vars": {}
                }),
                max_memory_mb=1024,
                max_cpu_cores=2,
                max_execution_time=60,
                expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
            )
            
            session.add(admin_session)
            await session.commit()
            
            logger.info("Admin user created successfully", 
                       user_id=str(admin_user.id), 
                       username=admin_user.username,
                       session_id=str(admin_session.id))
            
            print("✅ Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: password")
            print(f"   Email: admin@afteride.com")
            print(f"   Role: {admin_user.role.value}")
            print(f"   Session: {admin_session.name}")
            
    except Exception as e:
        logger.error("Failed to create admin user", error=str(e))
        print(f"❌ Failed to create admin user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_admin_user()) 