"""
AfterIDE - API v1 Router

Main API router that includes all endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, sessions, files, executions, submissions

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"]) 