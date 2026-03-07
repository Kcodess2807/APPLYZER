"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    """Application lifespan events."""
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
    """Create and configure FastAPI application."""
    
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