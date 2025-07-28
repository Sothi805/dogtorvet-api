from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.schemas.breed import BreedDB, BreedCreate, BreedUpdate
from .base import CRUDBase


class CRUDBreed(CRUDBase[BreedDB, BreedCreate, BreedUpdate]):
    """CRUD operations for Breed."""
    
    async def get_by_species(self, collection: AsyncIOMotorCollection, species_id: str) -> List[BreedDB]:
        """Get breeds by species ID."""
        if not ObjectId.is_valid(species_id):
            return []
        
        cursor = collection.find({"species_id": ObjectId(species_id), "status": True})
        documents = await cursor.to_list(length=None)
        return [BreedDB(**doc) for doc in documents]
    
    async def get_by_name_and_species(self, collection: AsyncIOMotorCollection, name: str, species_id: str) -> Optional[BreedDB]:
        """Get breed by name and species ID."""
        if not ObjectId.is_valid(species_id):
            return None
        
        document = await collection.find_one({"name": name, "species_id": ObjectId(species_id), "status": True})
        if document:
            return BreedDB(**document)
        return None
    
    async def name_exists_for_species(self, collection: AsyncIOMotorCollection, name: str, species_id: str) -> bool:
        """Check if breed name already exists for a species."""
        if not ObjectId.is_valid(species_id):
            return False
        
        count = await collection.count_documents({"name": name, "species_id": ObjectId(species_id), "status": True})
        return count > 0


# Create instance
breed_crud = CRUDBreed(BreedDB) 