"""
AfterIDE - FastAPI Application Entry Point

Main application configuration and startup logic for the AfterIDE backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import structlog
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.api.v1.api import api_router
from app.websocket.router import websocket_router, websocket_manager
from app.services.workspace import WorkspaceService

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AfterIDE - Web-Based Integrated Development Environment",
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint with application information."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AfterIDE - Web-Based IDE</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 2rem;
                    padding: 2rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                }}
                .endpoint {{
                    background: #f8f9fa;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                }}
                .status {{
                    background: #d4edda;
                    color: #155724;
                    padding: 1rem;
                    border-radius: 5px;
                    margin: 1rem 0;
                }}
                .docs-link {{
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 0.5rem 1rem;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 0.5rem;
                }}
                .docs-link:hover {{
                    background: #5a6fd8;
                }}
                .api-link {{
                    color: #667eea;
                    text-decoration: none;
                }}
                .api-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 AfterIDE</h1>
                <p>Web-Based Integrated Development Environment</p>
                <p><strong>Version:</strong> {settings.VERSION} | <strong>Environment:</strong> {settings.ENVIRONMENT}</p>
            </div>
            
            <div class="status">
                ✅ Application is running successfully!
            </div>
            
            <h2>Available Endpoints</h2>
            <div class="endpoint">
                <strong>API Documentation:</strong> 
                <a href="/docs" class="docs-link">OpenAPI Docs</a>
                <a href="/redoc" class="docs-link">ReDoc</a>
            </div>
            <div class="endpoint">
                <strong>Health Check:</strong> <a href="/health" class="api-link">/health</a>
            </div>
            <div class="endpoint">
                <strong>API Status:</strong> <a href="/api/v1/status" class="api-link">/api/v1/status</a>
            </div>
            <div class="endpoint">
                <strong>Authentication:</strong> <a href="/api/v1/auth" class="api-link">/api/v1/auth</a>
            </div>
            <div class="endpoint">
                <strong>Sessions:</strong> <a href="/api/v1/sessions" class="api-link">/api/v1/sessions</a>
            </div>
            <div class="endpoint">
                <strong>Files:</strong> <a href="/api/v1/files" class="api-link">/api/v1/files</a>
            </div>
            <div class="endpoint">
                <strong>Executions:</strong> <a href="/api/v1/executions" class="api-link">/api/v1/executions</a>
            </div>
            <div class="endpoint">
                <strong>Submissions:</strong> <a href="/api/v1/submissions" class="api-link">/api/v1/submissions</a>
            </div>
            <div class="endpoint">
                <strong>Workspace:</strong> <a href="/api/v1/workspace" class="api-link">/api/v1/workspace</a>
            </div>
            
            <h2>Quick Start</h2>
            <p>To get started with AfterIDE:</p>
            <ol>
                <li>Check the <a href="/docs">API documentation</a> for available endpoints</li>
                <li>Use the authentication endpoints to register/login</li>
                <li>Create a development session</li>
                <li>Start coding in your web-based IDE!</li>
            </ol>
            
            <h2>API Examples</h2>
            <p>Try these endpoints to test the API:</p>
            <ul>
                <li><a href="/api/v1/auth/status" class="api-link">Auth Status</a></li>
                <li><a href="/api/v1/sessions/status" class="api-link">Sessions Status</a></li>
                <li><a href="/api/v1/files/status" class="api-link">Files Status</a></li>
                <li><a href="/api/v1/executions/status" class="api-link">Executions Status</a></li>
                <li><a href="/api/v1/submissions/status" class="api-link">Submissions Status</a></li>
            </ul>
        </body>
        </html>
        """
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Include WebSocket routes
    app.include_router(websocket_router)
    
    # Additional utility endpoints
    @app.get("/info")
    async def app_info():
        """Get application information."""
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": "AfterIDE - Web-Based Integrated Development Environment",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "docs_url": "/docs" if settings.DEBUG else None,
            "health_url": "/health",
            "api_base_url": "/api/v1"
        }
    
    @app.get("/ping")
    async def ping():
        """Simple ping endpoint for testing."""
        return {"message": "pong", "status": "ok"}
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        """Custom 404 handler."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Not Found",
                "message": "The requested endpoint was not found.",
                "available_endpoints": [
                    "/",
                    "/health",
                    "/info",
                    "/ping",
                    "/docs",
                    "/api/v1/status",
                    "/api/v1/auth",
                    "/api/v1/sessions",
                    "/api/v1/files",
                    "/api/v1/executions",
                    "/api/v1/submissions",
                    "/api/v1/workspace"
                ]
            }
        )
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event handler."""
        logger.info("Starting AfterIDE application", version=settings.VERSION)
        
        # Initialize database
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
        
        # Initialize workspace service for WebSocket manager
        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                workspace_service = WorkspaceService(session)
                websocket_manager.set_workspace_service(workspace_service)
                
                # Set WebSocket manager for terminal service to enable file system notifications
                from app.services.terminal import terminal_service
                terminal_service.set_websocket_manager(websocket_manager)
                
                logger.info("Workspace service initialized for WebSocket manager")
                logger.info("WebSocket manager set for terminal service")
        except Exception as e:
            logger.error("Failed to initialize workspace service", error=str(e))
            # Don't raise here as the app can still function without workspace service
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event handler."""
        logger.info("Shutting down AfterIDE application")
        
        # Clean up any temporary workspaces
        # This would be handled by the workspace service cleanup methods
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local",
            "redis_url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "local"
        }
    
    return app

# Create application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    # Use Railway's PORT environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    ) 