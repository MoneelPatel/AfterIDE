#!/usr/bin/env python3
"""
AfterIDE - Create Reviewer User

Script to create a reviewer user for testing the reviewer assignment feature.
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

async def create_reviewer_user():
    """Create a reviewer user."""
    try:
        # Initialize database
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # Check if reviewer user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "reviewer")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("Reviewer user already exists", username="reviewer")
                return
            
            # Create reviewer user
            hashed_password = AuthService.get_password_hash("password")
            reviewer_user = User(
                username="reviewer",
                email="reviewer@afteride.com",
                hashed_password=hashed_password,
                role=UserRole.REVIEWER,
                is_active=1,  # Use integer for SQLite compatibility
                preferences=json.dumps({})  # Convert dict to JSON string for SQLite
            )
            
            session.add(reviewer_user)
            await session.commit()
            await session.refresh(reviewer_user)
            
            # Create default session for reviewer
            reviewer_session = Session(
                user_id=reviewer_user.id,
                name="Reviewer Workspace",
                description="Reviewer development workspace",
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
            
            session.add(reviewer_session)
            await session.commit()
            
            logger.info("Reviewer user created successfully", 
                       user_id=str(reviewer_user.id), 
                       username=reviewer_user.username,
                       session_id=str(reviewer_session.id))
            
            print("✅ Reviewer user created successfully!")
            print(f"   Username: reviewer")
            print(f"   Password: password")
            print(f"   Email: reviewer@afteride.com")
            print(f"   Role: {reviewer_user.role.value}")
            print(f"   Session: {reviewer_session.name}")
            
    except Exception as e:
        logger.error("Failed to create reviewer user", error=str(e))
        print(f"❌ Failed to create reviewer user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_reviewer_user()) 