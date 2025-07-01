from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import asyncio
from config import settings

# Global variables
client: Optional[AsyncIOMotorClient] = None
database = None
mongodb_available = False

# Collection names
COLLECTIONS = {
    "users": "users",
    "clients": "clients", 
    "pets": "pets",
    "species": "species",
    "breeds": "breeds",
    "appointments": "appointments",
    "services": "services",
    "products": "products",
    "invoices": "invoices",
    "invoice_items": "invoice_items",
    "allergies": "allergies",
    "vaccinations": "vaccinations",
    "audit_logs": "audit_logs"
}

async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, database, mongodb_available
    
    try:
        print(f"Attempting to connect to MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url)
        
        # Test the connection
        await asyncio.wait_for(client.admin.command('ping'), timeout=5.0)
        
        database = client[settings.database_name]
        mongodb_available = True
        print(f"✅ Successfully connected to MongoDB database: {settings.database_name}")
        
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {str(e)}")
        print(f"🔄 Running in development mode without MongoDB")
        mongodb_available = False
        client = None
        database = None

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client, mongodb_available
    
    if client and mongodb_available:
        client.close()
        print("✅ MongoDB connection closed")
    
    mongodb_available = False

def get_database():
    """Get database instance"""
    if not mongodb_available:
        raise Exception("MongoDB not available - running in development mode")
    return database

def get_collection(collection_name: str):
    """Get collection by name"""
    if not mongodb_available:
        raise Exception("MongoDB not available - running in development mode")
    return database[collection_name]

def is_mongodb_available() -> bool:
    """Check if MongoDB is available"""
    return mongodb_available 