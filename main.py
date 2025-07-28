from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.database import database
from app.api.v1 import api_router
from app.schemas.user import UserCreate, UserRole
from app.crud import user_crud
from app.db.database import COLLECTIONS


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events."""
    logger.info("🚀 Starting DogTorVet API v2.0...")
    
    # Connect to database (with retry logic)
    await database.connect()
    
    # Only proceed with database operations if connected
    if database.is_connected():
        logger.info("✅ Database connected - proceeding with admin user setup")
        try:
            collection = database.get_collection(COLLECTIONS["users"])
            
            # Check if admin user exists
            admin_user = await user_crud.get_by_email(collection, settings.admin_email)
            
            if admin_user is None:
                logger.info("Creating admin user...")
                admin_create = UserCreate(
                    first_name=settings.admin_first_name,
                    last_name=settings.admin_last_name,
                    email=settings.admin_email,
                    password=settings.admin_password,
                    role=UserRole.ADMIN
                )
                await user_crud.create(collection, admin_create)
                logger.info("✅ Admin user created successfully")
            else:
                logger.info("✅ Admin user already exists")
        except Exception as e:
            logger.error(f"❌ Error setting up admin user: {e}")
    else:
        logger.warning("⚠️ Database not connected - skipping admin user setup")
        logger.info("📚 API documentation will still be available at /docs")
    
    yield
    
    # Disconnect from database
    await database.disconnect()
    logger.info("👋 DogTorVet API v2.0 shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.description,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "errors": [str(exc)] if settings.debug else ["Internal server error"]
        }
    )

# Health check endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to DogTorVet API v2.0",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "database_status": "connected" if database.is_connected() else "disconnected"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "DogTorVet API v2.0 is running",
        "version": settings.app_version,
        "database_connected": database.is_connected(),
        "environment": settings.environment
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 