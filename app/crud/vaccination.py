from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import date

from app.schemas.vaccination import VaccinationDB, VaccinationCreate, VaccinationUpdate
from .base import CRUDBase


class CRUDVaccination(CRUDBase[VaccinationDB, VaccinationCreate, VaccinationUpdate]):
    """CRUD operations for Vaccination."""
    
    async def get_by_pet(self, collection: AsyncIOMotorCollection, pet_id: str) -> List[VaccinationDB]:
        """Get vaccinations by pet ID."""
        if not ObjectId.is_valid(pet_id):
            return []
        
        cursor = collection.find({"pet_id": pet_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [VaccinationDB(**doc) for doc in documents]
    
    async def get_by_vet(self, collection: AsyncIOMotorCollection, vet_id: str) -> List[VaccinationDB]:
        """Get vaccinations by vet ID."""
        if not ObjectId.is_valid(vet_id):
            return []
        
        cursor = collection.find({"vet_id": vet_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [VaccinationDB(**doc) for doc in documents]
    
    async def get_by_vaccine_name(self, collection: AsyncIOMotorCollection, vaccine_name: str) -> List[VaccinationDB]:
        """Get vaccinations by vaccine name."""
        cursor = collection.find({"vaccine_name": vaccine_name, "status": True})
        documents = await cursor.to_list(length=None)
        return [VaccinationDB(**doc) for doc in documents]
    
    async def get_due_vaccinations(self, collection: AsyncIOMotorCollection, due_date: date) -> List[VaccinationDB]:
        """Get vaccinations due by date."""
        cursor = collection.find({"next_due_date": {"$lte": due_date}, "status": True})
        documents = await cursor.to_list(length=None)
        return [VaccinationDB(**doc) for doc in documents]


# Create instance
vaccination_crud = CRUDVaccination(VaccinationDB) 