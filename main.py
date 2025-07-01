from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from database import connect_to_mongo, close_mongo_connection, is_mongodb_available, get_database
from seeders.root_user_seeder import seed_root_user
from database_indexes import create_indexes
from utils.logging import logger
from routes import (
    auth_router, users_router, clients_router, species_router, 
    breeds_router, pets_router, services_router, products_router, 
    appointments_router, invoices_router, invoice_items_router, analytics_router,
    allergies_router, vaccinations_router, audit_logs_router
)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting DogTorVet API...")
    await connect_to_mongo()
    
    if is_mongodb_available():
        logger.success("Connected to MongoDB")
        
        # Create database indexes
        try:
            db = get_database()
            await create_indexes(db)
            logger.success("Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation error (non-critical): {str(e)}")
        
        # Run database seeding (only root user)
        try:
            await seed_root_user()
            logger.success("Root user seeding completed")
        except Exception as e:
            logger.warning(f"Seeding error (non-critical): {str(e)}")
    else:
        logger.error("MongoDB not available - API will run with limited functionality")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DogTorVet API...")
    await close_mongo_connection()
    if is_mongodb_available():
        logger.success("Disconnected from MongoDB")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DogTorVet Veterinary Management System API",
    lifespan=lifespan
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dogtorvetservices.onrender.com",
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include all routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(species_router, prefix="/api")
app.include_router(breeds_router, prefix="/api")
app.include_router(pets_router, prefix="/api")
app.include_router(services_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(appointments_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(invoice_items_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(allergies_router, prefix="/api")
app.include_router(vaccinations_router, prefix="/api")
app.include_router(audit_logs_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DogTorVet API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "mongodb_status": "connected" if is_mongodb_available() else "disconnected"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "DogTorVet API is running",
        "version": settings.app_version,
        "mongodb_available": is_mongodb_available(),
        "environment": settings.environment
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.debug:
        raise exc
    
    # Return generic error in production
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 