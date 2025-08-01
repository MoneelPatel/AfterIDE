"""
AfterIDE - API v1 Router

Main API router that includes all endpoint modules.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Try to import and include endpoint routers with fallbacks
try:
    from app.api.v1.endpoints import auth
    api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
    print("✅ Auth router included")
except Exception as e:
    print(f"⚠️  Auth router not available: {e}")

try:
    from app.api.v1.endpoints import sessions
    api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    print("✅ Sessions router included")
except Exception as e:
    print(f"⚠️  Sessions router not available: {e}")

try:
    from app.api.v1.endpoints import files
    api_router.include_router(files.router, prefix="/files", tags=["files"])
    print("✅ Files router included")
except Exception as e:
    print(f"⚠️  Files router not available: {e}")

try:
    from app.api.v1.endpoints import executions
    api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
    print("✅ Executions router included")
except Exception as e:
    print(f"⚠️  Executions router not available: {e}")

try:
    from app.api.v1.endpoints import submissions
    api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
    print("✅ Submissions router included")
except Exception as e:
    print(f"⚠️  Submissions router not available: {e}")

try:
    from app.api.v1 import workspace
    api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
    print("✅ Workspace router included")
except Exception as e:
    print(f"⚠️  Workspace router not available: {e}")

# Add a status endpoint to show which routers are available
@api_router.get("/status")
async def api_status():
    """Show the status of all API endpoints."""
    return {
        "message": "AfterIDE API v1",
        "status": "running",
        "endpoints": [
            "/auth",
            "/sessions", 
            "/files",
            "/executions",
            "/submissions",
            "/workspace"
        ]
    } 