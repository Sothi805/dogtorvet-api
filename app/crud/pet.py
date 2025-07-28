from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.schemas.pet import PetDB, PetCreate, PetUpdate
from .base import CRUDBase


class CRUDPet(CRUDBase[PetDB, PetCreate, PetUpdate]):
    """CRUD operations for Pet."""
    
    async def get_by_client(self, collection: AsyncIOMotorCollection, client_id: str) -> List[PetDB]:
        """Get pets by client ID."""
        if not ObjectId.is_valid(client_id):
            return []
        
        cursor = collection.find({"client_id": client_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [PetDB(**doc) for doc in documents]
    
    async def get_by_species(self, collection: AsyncIOMotorCollection, species_id: str) -> List[PetDB]:
        """Get pets by species ID."""
        if not ObjectId.is_valid(species_id):
            return []
        
        cursor = collection.find({"species_id": species_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [PetDB(**doc) for doc in documents]
    
    async def get_by_breed(self, collection: AsyncIOMotorCollection, breed_id: str) -> List[PetDB]:
        """Get pets by breed ID."""
        if not ObjectId.is_valid(breed_id):
            return []
        
        cursor = collection.find({"breed_id": breed_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [PetDB(**doc) for doc in documents]


# Create instance
pet_crud = CRUDPet(PetDB) 