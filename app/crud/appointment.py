from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime, date

from app.schemas.appointment import AppointmentDB, AppointmentCreate, AppointmentUpdate
from .base import CRUDBase


class CRUDAppointment(CRUDBase[AppointmentDB, AppointmentCreate, AppointmentUpdate]):
    """CRUD operations for Appointment."""
    
    async def get_by_client(self, collection: AsyncIOMotorCollection, client_id: str) -> List[AppointmentDB]:
        """Get appointments by client ID."""
        if not ObjectId.is_valid(client_id):
            return []
        
        cursor = collection.find({"client_id": client_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_pet(self, collection: AsyncIOMotorCollection, pet_id: str) -> List[AppointmentDB]:
        """Get appointments by pet ID."""
        if not ObjectId.is_valid(pet_id):
            return []
        
        cursor = collection.find({"pet_id": pet_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_veterinarian(self, collection: AsyncIOMotorCollection, veterinarian_id: str) -> List[AppointmentDB]:
        """Get appointments by veterinarian ID."""
        if not ObjectId.is_valid(veterinarian_id):
            return []
        
        cursor = collection.find({"veterinarian_id": veterinarian_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_service(self, collection: AsyncIOMotorCollection, service_id: str) -> List[AppointmentDB]:
        """Get appointments by service ID."""
        if not ObjectId.is_valid(service_id):
            return []
        
        cursor = collection.find({"service_id": service_id, "status": True})
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_date(self, collection: AsyncIOMotorCollection, appointment_date: date) -> List[AppointmentDB]:
        """Get appointments by date."""
        start_date = datetime.combine(appointment_date, datetime.min.time())
        end_date = datetime.combine(appointment_date, datetime.max.time())
        
        cursor = collection.find({
            "appointment_date": {"$gte": start_date, "$lte": end_date},
            "status": True
        })
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_date_range(self, collection: AsyncIOMotorCollection, start_date: date, end_date: date) -> List[AppointmentDB]:
        """Get appointments by date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        cursor = collection.find({
            "appointment_date": {"$gte": start_datetime, "$lte": end_datetime},
            "status": True
        })
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]
    
    async def get_by_status(self, collection: AsyncIOMotorCollection, appointment_status: str) -> List[AppointmentDB]:
        """Get appointments by status."""
        cursor = collection.find({"appointment_status": appointment_status, "status": True})
        documents = await cursor.to_list(length=None)
        return [AppointmentDB(**doc) for doc in documents]


# Create instance
appointment_crud = CRUDAppointment(AppointmentDB) 