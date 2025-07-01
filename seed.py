#!/usr/bin/env python3
"""
Root user seeder for DogTorVet API
Only seeds the initial admin user - no sample data
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import sys

from config import settings
from utils.auth import get_password_hash
from database import COLLECTIONS

# MongoDB connection
client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.database_name]

async def seed_root_user_only():
    """Seed only the root admin user"""
    
    print("🌱 Seeding root user...")
    
    # Check if admin user already exists
    users_collection = db[COLLECTIONS["users"]]
    existing_admin = await users_collection.find_one({"email": settings.root_user_email})
    
    if existing_admin:
        print(f"✅ Root user '{settings.root_user_email}' already exists. Skipping.")
        return
    
    # Create root admin user
    admin_user = {
        "_id": ObjectId(),
        "first_name": settings.root_user_first_name,
        "last_name": settings.root_user_last_name,
        "email": settings.root_user_email,
        "password": get_password_hash(settings.root_user_password),
        "role": "admin",
        "phone": settings.root_user_phone,
        "specialization": settings.root_user_specialization,
        "email_verified_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": True
    }
    
    await users_collection.insert_one(admin_user)
    print(f"✅ Root admin user created successfully!")
    print(f"📧 Email: {settings.root_user_email}")
    print(f"🔑 Password: {settings.root_user_password}")
    
    client.close()

async def check_root_user():
    """Check if root user exists"""
    users_collection = db[COLLECTIONS["users"]]
    root_user = await users_collection.find_one({"email": settings.root_user_email})
    
    if root_user:
        print(f"✅ Root user '{settings.root_user_email}' exists")
        print(f"🆔 User ID: {str(root_user['_id'])}")
        print(f"👤 Name: {root_user['first_name']} {root_user['last_name']}")
        print(f"📱 Phone: {root_user.get('phone', 'N/A')}")
        print(f"🛡️ Role: {root_user.get('role', 'N/A')}")
    else:
        print(f"❌ Root user '{settings.root_user_email}' not found")
    
    client.close()

async def reset_root_password():
    """Reset root user password"""
    users_collection = db[COLLECTIONS["users"]]
    
    # Hash the new password
    hashed_password = get_password_hash(settings.root_user_password)
    
    # Update the password
    result = await users_collection.update_one(
        {"email": settings.root_user_email},
        {
            "$set": {
                "password": hashed_password,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"🔄 Root user password reset successfully!")
        print(f"📧 Email: {settings.root_user_email}")
        print(f"🔑 New Password: {settings.root_user_password}")
    else:
        print(f"❌ Failed to reset root user password")
    
    client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            asyncio.run(check_root_user())
        elif sys.argv[1] == "--reset-password":
            asyncio.run(reset_root_password())
        else:
            print("Usage: python seed.py [--check|--reset-password]")
    else:
        asyncio.run(seed_root_user_only()) 