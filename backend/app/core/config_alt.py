"""
AfterIDE - Alternative Configuration Management
Uses standard Python libraries instead of pydantic-settings
"""

import os
from typing import List

class Settings:
    """Application settings and configuration using standard Python."""
    
    def __init__(self):
        # Application metadata
        self.PROJECT_NAME = "AfterIDE"
        self.VERSION = "1.0.0"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
        self.ALGORITHM = "HS256"
        
        # CORS and allowed hosts
        self.CORS_ORIGINS = self._parse_list(os.getenv("CORS_ORIGINS", "*"))
        self.ALLOWED_HOSTS = self._parse_list(os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*"))
        
        # Database - Railway PostgreSQL
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./afteride.db")
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        self.DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
        
        # Redis - Railway Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", "10"))
        
        # Session management
        self.SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))
        self.MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
        
        # Code execution
        self.MAX_EXECUTION_TIME = int(os.getenv("MAX_EXECUTION_TIME", "30"))
        self.MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "512"))
        self.MAX_PROCESSES = int(os.getenv("MAX_PROCESSES", "10"))
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.CONTAINER_IMAGE = os.getenv("CONTAINER_IMAGE", "python:3.11-slim")
        
        # File system
        self.MAX_FILES_PER_SESSION = int(os.getenv("MAX_FILES_PER_SESSION", "100"))
        self.TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/afteride")
        
        # WebSocket
        self.WEBSOCKET_PING_INTERVAL = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))
        self.WEBSOCKET_PING_TIMEOUT = int(os.getenv("WEBSOCKET_PING_TIMEOUT", "10"))
        self.WEBSOCKET_MAX_CONNECTIONS = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "100"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse a comma-separated string into a list."""
        if not value:
            return []
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

# Create settings instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
    # Allow Railway domains
    settings.CORS_ORIGINS = ["*"]  # Allow all for now, can be restricted later
    settings.ALLOWED_HOSTS = ["*"]  # Allow all for Railway deployment 