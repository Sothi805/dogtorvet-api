from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas.species import SpeciesDB, SpeciesCreate, SpeciesUpdate
from .base import CRUDBase


class CRUDSpecies(CRUDBase[SpeciesDB, SpeciesCreate, SpeciesUpdate]):
    """CRUD operations for Species."""
    
    async def get_by_name(self, collection: AsyncIOMotorCollection, name: str) -> Optional[SpeciesDB]:
        """Get species by name."""
        document = await collection.find_one({"name": name, "status": True})
        if document:
            return SpeciesDB(**document)
        return None
    
    async def name_exists(self, collection: AsyncIOMotorCollection, name: str) -> bool:
        """Check if species name already exists."""
        count = await collection.count_documents({"name": name, "status": True})
        return count > 0


# Create instance
species_crud = CRUDSpecies(SpeciesDB) 