"""
AfterIDE - FastAPI Application Entry Point

Main application configuration and startup logic for the AfterIDE backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Include WebSocket routes
    app.include_router(websocket_router)
    
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