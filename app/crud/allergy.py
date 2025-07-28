from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.schemas.allergy import AllergyDB, AllergyCreate, AllergyUpdate
from .base import CRUDBase


class CRUDAllergy(CRUDBase[AllergyDB, AllergyCreate, AllergyUpdate]):
    """CRUD operations for Allergy."""
    
    async def get_by_pet(self, collection: AsyncIOMotorCollection, pet_id: str) -> List[AllergyDB]:
        """Get allergies by pet ID."""
        if not ObjectId.is_valid(pet_id):
            return []
        
        cursor = collection.find({"pet_id": pet_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [AllergyDB(**doc) for doc in documents]
    
    async def get_by_allergen(self, collection: AsyncIOMotorCollection, allergen: str) -> List[AllergyDB]:
        """Get allergies by allergen."""
        cursor = collection.find({"allergen": allergen, "status": True})
        documents = await cursor.to_list(length=None)
        return [AllergyDB(**doc) for doc in documents]
    
    async def get_by_severity(self, collection: AsyncIOMotorCollection, severity: str) -> List[AllergyDB]:
        """Get allergies by severity."""
        cursor = collection.find({"severity": severity, "status": True})
        documents = await cursor.to_list(length=None)
        return [AllergyDB(**doc) for doc in documents]
    
    async def get_by_pet_and_allergen(self, collection: AsyncIOMotorCollection, pet_id: str, allergen: str) -> Optional[AllergyDB]:
        """Get allergy by pet ID and allergen."""
        if not ObjectId.is_valid(pet_id):
            return None
        
        document = await collection.find_one({"pet_id": pet_id, "allergen": allergen, "status": True})
        if document:
            return AllergyDB(**document)
        return None


# Create instance
allergy_crud = CRUDAllergy(AllergyDB) 