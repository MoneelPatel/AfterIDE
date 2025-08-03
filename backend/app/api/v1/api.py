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
    from app.api.v1.endpoints import submissions
    # Create a separate code-reviews router that includes the code-review endpoints
    code_reviews_router = APIRouter()
    # Add trailing slashes to prevent Railway redirects
    code_reviews_router.post("/")(submissions.create_code_review)
    code_reviews_router.post("")(submissions.create_code_review)  # Alternative without slash
    code_reviews_router.get("/file-by-path/{filepath:path}")(submissions.get_file_by_path_code_review)
    api_router.include_router(code_reviews_router, prefix="/code-reviews", tags=["code-reviews"])
    print("✅ Code Reviews router included")
except Exception as e:
    print(f"⚠️  Code Reviews router not available: {e}")

try:
    from app.api.v1.endpoints import workspace
    api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
    print("✅ Workspace router included")
except Exception as e:
    print(f"⚠️  Workspace router not available: {e}")

try:
    from app.api.v1.endpoints import setup
    api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
    print("✅ Setup router included")
except Exception as e:
    print(f"⚠️  Setup router not available: {e}")

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