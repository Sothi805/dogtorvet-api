from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio
import logging
from app.core.config import settings


logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.connected: bool = False
    
    async def connect(self):
        """Connect to MongoDB with retry logic."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{max_retries})")
                self.client = AsyncIOMotorClient(settings.database_url)
                
                # Test connection with shorter timeout
                await asyncio.wait_for(self.client.admin.command('ping'), timeout=10.0)
                
                self.db = self.client[settings.database_name]
                self.connected = True
                logger.info(f"✅ Successfully connected to MongoDB database: {settings.database_name}")
                return
                
            except Exception as e:
                logger.error(f"❌ MongoDB connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.warning("⚠️ Failed to connect to MongoDB after all retries. API will run with limited functionality.")
                    self.connected = False
                    self.client = None
                    self.db = None
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client and self.connected:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
        
        self.connected = False
        self.client = None
        self.db = None
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if not self.connected or self.db is None:
            raise RuntimeError("Database not connected")
        return self.db
    
    def get_collection(self, collection_name: str):
        """Get collection by name."""
        if not self.connected or self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.connected


# Global database instance
database = Database()


async def get_db():
    """Dependency to get database instance."""
    if not database.is_connected():
        raise RuntimeError("Database not connected")
    return database.get_database()


# Collection names
COLLECTIONS = {
    "users": "users",
    "clients": "clients",
    "pets": "pets",
    "species": "species",
    "breeds": "breeds",
    "allergies": "allergies",
    "vaccinations": "vaccinations",
    "appointments": "appointments",
    "services": "services",
    "products": "products",
    "invoices": "invoices",
    "invoice_items": "invoice_items",
    "audit_logs": "audit_logs"
} 