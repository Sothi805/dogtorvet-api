from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas.client import ClientDB, ClientCreate, ClientUpdate
from .base import CRUDBase


class CRUDClient(CRUDBase[ClientDB, ClientCreate, ClientUpdate]):
    """CRUD operations for Client."""
    
    async def get_by_phone(self, collection: AsyncIOMotorCollection, phone_number: str) -> Optional[ClientDB]:
        """Get client by phone number."""
        document = await collection.find_one({"phone_number": phone_number, "status": True})
        if document:
            return ClientDB(**document)
        return None
    
    async def phone_exists(self, collection: AsyncIOMotorCollection, phone_number: str) -> bool:
        """Check if phone number already exists."""
        count = await collection.count_documents({"phone_number": phone_number, "status": True})
        return count > 0


# Create instance
client_crud = CRUDClient(ClientDB) 