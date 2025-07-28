from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.schemas.allergy_type import AllergyTypeDB, AllergyTypeCreate, AllergyTypeUpdate
from .base import CRUDBase


class CRUDAllergyType(CRUDBase[AllergyTypeDB, AllergyTypeCreate, AllergyTypeUpdate]):
    """CRUD operations for AllergyType."""
    
    async def get_by_name(self, collection: AsyncIOMotorCollection, name: str) -> Optional[AllergyTypeDB]:
        """Get allergy type by name."""
        document = await collection.find_one({"name": name})
        return AllergyTypeDB(**document) if document else None
    
    async def name_exists(self, collection: AsyncIOMotorCollection, name: str) -> bool:
        """Check if allergy type name already exists."""
        document = await collection.find_one({"name": name})
        return document is not None


# Create instance
allergy_type_crud = CRUDAllergyType(AllergyTypeDB) 