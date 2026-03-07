#for monitoring the health of the application--->production shit :)
from fastapi import APIRouter
from loguru import logger
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def healthCheck():
    #a minimal checkpoint to check current health
    logger.info("User just wants to know whether the app is healthy or what?")
    return {
        "status": "Healthy",
        "service": "job-application-system",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed")
async def detailedHealthCheck():
    #will give other information too apart from the minimal health checkup
    logger.info("User wants a detailed health checkUp")
    
    # Check database connectivity
    db_status = "healthy"
    try:
        from app.database.init_db import check_db_connection
        if not check_db_connection():
            db_status = "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    # TODO: Add Redis connectivity check
    # TODO: Add external API connectivity checks
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "service": "job-application-system",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": db_status,
            "redis": "not_implemented",
            "external_apis": "not_implemented"
        },
        "database_url": "supabase" if "supabase.co" in settings.getDatabaseUrl else settings.getDatabaseUrl,
        "uptime": "not_implemented"
    }