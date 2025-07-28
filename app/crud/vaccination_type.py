from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.schemas.vaccination_type import VaccinationTypeDB, VaccinationTypeCreate, VaccinationTypeUpdate
from .base import CRUDBase


class CRUDVaccinationType(CRUDBase[VaccinationTypeDB, VaccinationTypeCreate, VaccinationTypeUpdate]):
    """CRUD operations for VaccinationType."""
    
    async def get_by_name(self, collection: AsyncIOMotorCollection, name: str) -> Optional[VaccinationTypeDB]:
        """Get vaccination type by name."""
        document = await collection.find_one({"name": name})
        return VaccinationTypeDB(**document) if document else None
    
    async def name_exists(self, collection: AsyncIOMotorCollection, name: str) -> bool:
        """Check if vaccination type name already exists."""
        document = await collection.find_one({"name": name})
        return document is not None


# Create instance
vaccination_type_crud = CRUDVaccinationType(VaccinationTypeDB) 