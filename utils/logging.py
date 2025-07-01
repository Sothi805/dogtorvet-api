from loguru import logger
import sys
import os
from config import settings

# Remove default logger
logger.remove()

# Configure logging based on environment
if settings.environment == "production":
    # Production: JSON format for structured logging
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
        serialize=True  # JSON output
    )
    
    # Also log errors to file
    logger.add(
        "logs/error.log",
        rotation="10 MB",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
else:
    # Development: Human-readable format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.debug else "INFO",
        colorize=True
    )

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Export configured logger
__all__ = ["logger"] 