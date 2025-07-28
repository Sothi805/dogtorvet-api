from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas.user import UserDB, UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from .base import CRUDBase


class CRUDUser(CRUDBase[UserDB, UserCreate, UserUpdate]):
    """CRUD operations for User."""
    
    async def get_by_email(self, collection: AsyncIOMotorCollection, email: str) -> Optional[UserDB]:
        """Get user by email."""
        document = await collection.find_one({"email": email, "status": True})
        if document is not None:
            return UserDB(**document)
        return None
    
    async def authenticate(self, collection: AsyncIOMotorCollection, email: str, password: str) -> Optional[UserDB]:
        """Authenticate user."""
        user = await self.get_by_email(collection, email)
        if user is None:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    async def create(self, collection: AsyncIOMotorCollection, obj_in: UserCreate) -> UserDB:
        """Create new user with hashed password."""
        obj_data = obj_in.model_dump()
        obj_data["password"] = hash_password(obj_data["password"])
        
        # Create the user document
        from datetime import datetime, timezone
        obj_data["created_at"] = datetime.now(timezone.utc)
        obj_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(obj_data)
        created_document = await collection.find_one({"_id": result.inserted_id})
        if created_document is not None:
            return UserDB(**created_document)
        raise RuntimeError("Failed to create user")
    
    async def update_password(self, collection: AsyncIOMotorCollection, id: str, password: str) -> Optional[UserDB]:
        """Update user password."""
        hashed_password = hash_password(password)
        return await self.update(collection, id, {"password": hashed_password})
    
    async def email_exists(self, collection: AsyncIOMotorCollection, email: str) -> bool:
        """Check if email already exists."""
        count = await collection.count_documents({"email": email, "status": True})
        return count > 0


# Create instance
user_crud = CRUDUser(UserDB) 