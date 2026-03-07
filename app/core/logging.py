"""
Structured logging configuration using loguru.
"""

import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """Configure structured logging with loguru."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for production
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/app.log",
            format=settings.LOG_FORMAT,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=False  # Don't include sensitive info in production logs
        )
    
    # Add error file handler
    logger.add(
        "logs/errors.log",
        format=settings.LOG_FORMAT,
        level="ERROR",
        rotation="1 week",
        retention="4 weeks",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    logger.info("Logging configured successfully")


def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)