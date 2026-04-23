"""
ApplyBot - AI-Powered Job Application Automation System

Main FastAPI application entry point. This module initializes the web server,
configures middleware, sets up database connections, and manages background workers
for automated email tracking and follow-ups.

Key Features:
    - RESTful API with FastAPI
    - PostgreSQL database with SQLAlchemy ORM
    - Background workers for Gmail reply checking and follow-up scheduling
    - OAuth2 integration with Gmail and Google Sheets
    - AI-powered resume and cover letter generation
    - Automated job application pipeline

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    GROQ_API_KEY: Groq AI API key for text generation
    GMAIL_CLIENT_ID: Gmail OAuth2 client ID
    GMAIL_CLIENT_SECRET: Gmail OAuth2 client secret
    SHEETS_SPREADSHEET_ID: Google Sheets tracking spreadsheet ID
    ENABLE_BACKGROUND_WORKERS: Enable/disable background workers (true/false)

Usage:
    Development:
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    Production:
        gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

Author: ApplyBot Team
Version: 1.0.0
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import asyncio
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router


# Global flag to control background workers
ENABLE_BACKGROUND_WORKERS = os.getenv("ENABLE_BACKGROUND_WORKERS", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events (startup and shutdown).
    
    Startup:
        1. Initialize logging system
        2. Check and initialize database connection
        3. Start background workers (if enabled)
            - Reply checker: Monitors Gmail for application responses
            - Follow-up scheduler: Sends automated follow-up emails
    
    Shutdown:
        1. Cancel background worker tasks
        2. Clean up resources
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Control returns to FastAPI during application runtime
    """
    # Startup
    setup_logging()
    logger.info("🚀 Job Application System starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    try:
        from app.database.init_db import check_db_connection, init_db
        
        if check_db_connection():
            init_db()
            logger.info("✅ Database initialized successfully")
        else:
            logger.warning("⚠️  Database connection failed - some features may not work")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    # Start background workers if enabled
    background_task = None
    if ENABLE_BACKGROUND_WORKERS:
        logger.info("🔄 Starting background workers...")
        try:
            from app.workers.scheduler_manager import start_schedulers
            background_task = asyncio.create_task(start_schedulers())
            logger.info("✅ Background workers started")
        except Exception as e:
            logger.error(f"❌ Failed to start background workers: {e}")
            logger.info("💡 Tip: Background workers require Gmail and Sheets authentication")
    else:
        logger.info("ℹ️  Background workers disabled (set ENABLE_BACKGROUND_WORKERS=true to enable)")
    
    yield
    
    # Shutdown
    logger.info("📴 Job Application System shutting down...")
    
    # Stop background workers
    if background_task and not background_task.done():
        logger.info("Stopping background workers...")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background workers stopped")



def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Configuration includes:
        - API metadata (title, description, version)
        - CORS middleware for cross-origin requests
        - API router with versioned endpoints (/api/v1)
        - Global exception handler for error logging
        - Lifespan context manager for startup/shutdown
    
    Returns:
        FastAPI: Configured FastAPI application instance
        
    Example:
        >>> app = create_application()
        >>> # Run with: uvicorn app.main:app --reload
    """
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-powered automated job application system",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    import traceback

    # Global exception handler — handle development vs production error responses.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
        
        if settings.DEBUG:
            logger.exception("Development mode: returning full traceback.")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred.",
                    "error": str(exc),
                    "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)
                },
            )
            
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    return app


# Create the FastAPI app instance
app = create_application()


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Job Application System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": f"{settings.API_V1_STR}/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "job-application-system",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None
    )