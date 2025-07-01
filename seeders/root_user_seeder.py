from datetime import datetime
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database
from utils.auth import get_password_hash


async def seed_root_user():
    """Seed the root admin user if it doesn't exist"""
    try:
        # Get database instance
        db = get_database()
        
        # Check if admin user already exists
        existing_admin = await db.users.find_one({"email": "admin@dogtorvet.com"})
        
        if existing_admin:
            print("✅ Root user 'admin@dogtorvet.com' already exists. Skipping seeding.")
            return
        
        # Create root admin user
        admin_user = {
            "first_name": "System",
            "last_name": "Administrator", 
            "email": "admin@dogtorvet.com",
            "phone": "+1234567890",
            "email_verified_at": datetime.utcnow(),
            "password": get_password_hash("DogTorVet2025!"),
            "role": "admin",
            "specialization": "System Administration",
            "remember_token": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.users.insert_one(admin_user)
        print(f"✅ Root admin user created with ID: {result.inserted_id}")
        print("📧 Email: admin@dogtorvet.com")
        print("🔐 Password: DogTorVet2025!")
        
    except Exception as e:
        print(f"❌ Error seeding root user: {e}")
        raise

async def check_root_user():
    """Check if root user exists and return user info"""
    users_collection = get_collection(COLLECTIONS["users"])
    
    root_user = await users_collection.find_one({
        "email": settings.root_user_email
    })
    
    if root_user:
        print(f"✅ Root user '{settings.root_user_email}' exists")
        print(f"🆔 User ID: {str(root_user['_id'])}")
        print(f"👤 Role: {root_user.get('role', 'N/A')}")
        print(f"📱 Phone: {root_user.get('phone', 'N/A')}")
        return root_user
    else:
        print(f"❌ Root user '{settings.root_user_email}' not found")
        return None

async def reset_root_password():
    """Reset root user password to the one in config"""
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Hash the new password
    hashed_password = pwd_context.hash(settings.root_user_password)
    
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
        return True
    else:
        print(f"❌ Failed to reset root user password")
        return False 