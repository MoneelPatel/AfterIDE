"""
AfterIDE - FastAPI Application Entry Point

Main application configuration and startup logic for the AfterIDE backend.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import structlog
import os
import httpx

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.core.security import security_middleware, security_config
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
        docs_url="/docs",  # Always enable docs
        redoc_url="/redoc",  # Always enable redoc
        openapi_url="/openapi.json",  # Always enable OpenAPI JSON
    )
    
    # Add security middleware first (before CORS)
    app.middleware("http")(security_middleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://after-ide-production.up.railway.app",
            "https://after-ide-development.up.railway.app", 
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "*"  # Fallback for development
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
            "X-Instance-ID",
            "Cache-Control",
            "Pragma",
            "Expires"
        ],
        expose_headers=["X-Request-ID", "X-Instance-ID"],
        max_age=86400,  # Cache preflight requests for 24 hours
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
                    transition: background-color 0.3s ease;
                }}
                .docs-link:hover {{
                    background: #5a6fd8;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                .api-docs-section {{
                    background: #f8f9fa;
                    padding: 1.5rem;
                    border-radius: 10px;
                    margin: 1rem 0;
                    border-left: 4px solid #667eea;
                }}
                .feature-list {{
                    list-style: none;
                    padding: 0;
                }}
                .feature-list li {{
                    padding: 0.5rem 0;
                    border-bottom: 1px solid #e9ecef;
                }}
                .feature-list li:last-child {{
                    border-bottom: none;
                }}
                .feature-list li:before {{
                    content: "✅ ";
                    margin-right: 0.5rem;
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
                <a href="/docs" class="docs-link">OpenAPI Docs (Swagger)</a>
                <a href="/redoc" class="docs-link">ReDoc</a>
                <a href="/openapi.json" class="docs-link">OpenAPI JSON</a>
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
                <li>Check the <a href="/docs">API documentation</a> for available endpoints (interactive Swagger UI)</li>
                <li>Use the authentication endpoints to register/login</li>
                <li>Create a development session</li>
                <li>Start coding in your web-based IDE!</li>
            </ol>
            
            <h2>API Documentation</h2>
            <div class="api-docs-section">
                <p>The API documentation is fully interactive and allows you to:</p>
                <ul class="feature-list">
                    <li>View all endpoints with detailed descriptions</li>
                    <li>Test API calls directly from the browser</li>
                    <li>See request/response schemas for all endpoints</li>
                    <li>Authenticate and make real API calls to test functionality</li>
                </ul>
                <p><a href="/docs" class="docs-link">🚀 Open Interactive API Documentation</a></p>
            </div>
            
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
            "docs_url": "/docs",  # Always available
            "redoc_url": "/redoc",  # Always available
            "openapi_url": "/openapi.json",  # Always available
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
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Global HTTP exception handler to ensure CORS headers are added."""
        # Get the origin from the request
        origin = request.headers.get("origin")
        
        # Create response with CORS headers
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
        
        # Add CORS headers if origin is present
        if origin:
            # Check if origin is in allowed origins
            allowed_origins = [
                "https://after-ide-production.up.railway.app",
                "https://after-ide-development.up.railway.app", 
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "*"
            ]
            
            if origin in allowed_origins or "*" in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-Request-ID, X-Instance-ID, Cache-Control, Pragma, Expires"
                response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Instance-ID"
        
        return response
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event handler."""
        logger.info("Starting AfterIDE application", version=settings.VERSION)
        
        # Log all registered routes for debugging
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                if hasattr(route, 'methods'):
                    routes.append(f"{route.methods} {route.path}")
                else:
                    routes.append(f"WS {route.path}")
        logger.info("Registered routes", routes=routes)
        
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
    
    @app.get("/test-proxy")
    async def test_proxy():
        """Test endpoint to verify proxy functionality."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://sad-chess-production.up.railway.app/api/v1/submissions/stats")
                return {
                    "status": "proxy_test_successful",
                    "sad_chess_status": response.status_code,
                    "sad_chess_response": response.json() if response.status_code == 200 else {"error": "Failed to reach sad-chess API"}
                }
        except Exception as e:
            return {
                "status": "proxy_test_failed",
                "error": str(e)
            }
    
    # Proxy route to forward requests to sad-chess API
    @app.api_route("/proxy/sad-chess/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    async def proxy_sad_chess(request: Request, path: str):
        """Proxy requests to sad-chess API to avoid CORS issues."""
        try:
            # Construct the target URL
            target_url = f"https://sad-chess-production.up.railway.app/api/v1/{path}"
            
            # Get query parameters
            query_params = str(request.query_params) if request.query_params else ""
            if query_params:
                target_url += f"?{query_params}"
            
            # Get request body
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # Get headers (filter out problematic ones)
            headers = dict(request.headers)
            headers_to_remove = [
                "host", "content-length", "transfer-encoding", 
                "connection", "upgrade", "http2-settings"
            ]
            for header in headers_to_remove:
                headers.pop(header.lower(), None)
            
            # Make the request to sad-chess API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    follow_redirects=True
                )
                
                # Return the response
                return JSONResponse(
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except Exception as e:
            logger.error("Proxy request failed", error=str(e), path=path)
            return JSONResponse(
                status_code=500,
                content={"error": "Proxy request failed", "detail": str(e)}
            )
    
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