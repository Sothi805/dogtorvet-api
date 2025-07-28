from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas.service import ServiceDB, ServiceCreate, ServiceUpdate
from .base import CRUDBase


class CRUDService(CRUDBase[ServiceDB, ServiceCreate, ServiceUpdate]):
    """CRUD operations for Service."""
    
    async def get_by_name(self, collection: AsyncIOMotorCollection, name: str) -> Optional[ServiceDB]:
        """Get service by name."""
        document = await collection.find_one({"name": name, "status": True})
        if document:
            return ServiceDB(**document)
        return None
    
    async def get_by_category(self, collection: AsyncIOMotorCollection, category: str) -> List[ServiceDB]:
        """Get services by category."""
        cursor = collection.find({"category": category, "status": True})
        documents = await cursor.to_list(length=None)
        return [ServiceDB(**doc) for doc in documents]
    
    async def name_exists(self, collection: AsyncIOMotorCollection, name: str) -> bool:
        """Check if service name already exists."""
        count = await collection.count_documents({"name": name, "status": True})
        return count > 0


# Create instance
service_crud = CRUDService(ServiceDB) 