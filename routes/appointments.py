from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, date
from enum import Enum

from database import get_collection, COLLECTIONS
from models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse
from models.user import User
from utils.auth import get_current_user


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


router = APIRouter(prefix="/appointments", tags=["Appointments"])


async def populate_appointment_relationships(appointment_doc: dict, include: str = "") -> dict:
    """Populate appointment relationships based on include parameter"""
    appointment = appointment_doc.copy()
    
    # Convert ObjectIds to integer IDs
    appointment["id"] = abs(hash(str(appointment_doc["_id"]))) % (10**8)
    appointment["client_id"] = abs(hash(str(appointment_doc["client_id"]))) % (10**8)
    appointment["pet_id"] = abs(hash(str(appointment_doc["pet_id"]))) % (10**8)
    appointment["veterinarian_id"] = abs(hash(str(appointment_doc["veterinarian_id"]))) % (10**8)
    if appointment_doc.get("service_id"):
        appointment["service_id"] = abs(hash(str(appointment_doc["service_id"]))) % (10**8)
    
    # Format dates
    appointment["appointment_date"] = appointment_doc.get("appointment_date").isoformat() if appointment_doc.get("appointment_date") else None
    appointment["created_at"] = appointment_doc.get("created_at").isoformat() if appointment_doc.get("created_at") else None
    appointment["updated_at"] = appointment_doc.get("updated_at").isoformat() if appointment_doc.get("updated_at") else None
    
    if not include:
        return appointment
    
    include_list = [item.strip() for item in include.split(',')]
    
    # Populate client
    if 'client' in include_list and appointment_doc.get("client_id"):
        clients_collection = get_collection(COLLECTIONS["clients"])
        client_doc = await clients_collection.find_one({"_id": appointment_doc["client_id"]})
        if client_doc:
            appointment["client"] = {
                "id": abs(hash(str(client_doc["_id"]))) % (10**8),
                "name": client_doc.get("name", ""),
                "email": client_doc.get("email", ""),
                "phone": client_doc.get("phone_number", "")
            }
    
    # Populate pet
    if 'pet' in include_list and appointment_doc.get("pet_id"):
        pets_collection = get_collection(COLLECTIONS["pets"])
        pet_doc = await pets_collection.find_one({"_id": appointment_doc["pet_id"]})
        if pet_doc:
            pet_data = {
                "id": abs(hash(str(pet_doc["_id"]))) % (10**8),
                "name": pet_doc.get("name", "")
            }
            
            # Also get species and breed if available
            if pet_doc.get("species_id"):
                species_collection = get_collection(COLLECTIONS["species"])
                species_doc = await species_collection.find_one({"_id": pet_doc["species_id"]})
                if species_doc:
                    pet_data["species"] = {
                        "id": abs(hash(str(species_doc["_id"]))) % (10**8),
                        "name": species_doc.get("name", "")
                    }
            
            if pet_doc.get("breed_id"):
                breeds_collection = get_collection(COLLECTIONS["breeds"])
                breed_doc = await breeds_collection.find_one({"_id": pet_doc["breed_id"]})
                if breed_doc:
                    pet_data["breed"] = {
                        "id": abs(hash(str(breed_doc["_id"]))) % (10**8),
                        "name": breed_doc.get("name", "")
                    }
            
            appointment["pet"] = pet_data
    
    # Populate service
    if 'service' in include_list and appointment_doc.get("service_id"):
        services_collection = get_collection(COLLECTIONS["services"])
        service_doc = await services_collection.find_one({"_id": appointment_doc["service_id"]})
        if service_doc:
            appointment["service"] = {
                "id": abs(hash(str(service_doc["_id"]))) % (10**8),
                "name": service_doc.get("name", ""),
                "price": service_doc.get("price", 0),
                "duration_minutes": service_doc.get("duration_minutes", 30)
            }
    
    # Populate user (veterinarian)
    if 'user' in include_list:
        user_id = appointment_doc.get("veterinarian_id") or appointment_doc.get("user_id")
        if user_id:
            users_collection = get_collection(COLLECTIONS["users"])
            user_doc = await users_collection.find_one({"_id": user_id})
            if user_doc:
                appointment["user"] = {
                    "id": abs(hash(str(user_doc["_id"]))) % (10**8),
                    "name": f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip(),
                    "role": user_doc.get("role", "")
                }
    
    return appointment


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    include: str = Query("", description="Comma-separated list of relationships to include"),
    search: str = Query("", description="Search term"),
    appointment_status: Optional[str] = Query(None, description="Filter by appointment status"),
    appointment_date_from: Optional[str] = Query(None, description="Filter appointments from date (YYYY-MM-DD)"),
    appointment_date_to: Optional[str] = Query(None, description="Filter appointments to date (YYYY-MM-DD)"),
    sort_by: str = Query("appointment_date", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    include_inactive: bool = Query(True, description="Include inactive records"),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the appointments (matching Laravel pagination)"""
    appointments_collection = get_collection(COLLECTIONS["appointments"])
    
    # Build query
    query = {}
    
    # Add status filter
    if appointment_status and appointment_status != "all":
        query["appointment_status"] = appointment_status
    
    # Add date range filters
    if appointment_date_from or appointment_date_to:
        date_filter = {}
        if appointment_date_from:
            try:
                from_date = datetime.strptime(appointment_date_from, "%Y-%m-%d")
                date_filter["$gte"] = from_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format for appointment_date_from. Use YYYY-MM-DD"
                )
        if appointment_date_to:
            try:
                to_date = datetime.strptime(appointment_date_to, "%Y-%m-%d")
                # Add 23:59:59 to include the entire day
                to_date = to_date.replace(hour=23, minute=59, second=59)
                date_filter["$lte"] = to_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format for appointment_date_to. Use YYYY-MM-DD"
                )
        if date_filter:
            query["appointment_date"] = date_filter
    
    # Add search filter
    if search:
        query["$or"] = [
            {"notes": {"$regex": search, "$options": "i"}}
        ]
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await appointments_collection.count_documents(query)
    
    # Build sort criteria
    sort_criteria = []
    if sort_order == "desc":
        sort_criteria.append((sort_by, -1))
    else:
        sort_criteria.append((sort_by, 1))
    
    # Execute query
    cursor = appointments_collection.find(query).sort(sort_criteria).skip(skip).limit(per_page)
    appointments_list = []
    
    async for appointment_doc in cursor:
        # Convert to consistent ObjectId string format
        appointment_data = {
            "id": str(appointment_doc["_id"]),
            "appointment_date": appointment_doc.get("appointment_date").isoformat() if appointment_doc.get("appointment_date") else None,
            "client_id": str(appointment_doc.get("client_id")) if appointment_doc.get("client_id") else None,
            "pet_id": str(appointment_doc.get("pet_id")) if appointment_doc.get("pet_id") else None,
            "veterinarian_id": str(appointment_doc.get("user_id")) if appointment_doc.get("user_id") else None,
            "service_id": str(appointment_doc.get("service_id")) if appointment_doc.get("service_id") else None,
            "appointment_status": appointment_doc.get("appointment_status", "scheduled"),
            "notes": appointment_doc.get("notes", ""),
            "created_at": appointment_doc.get("created_at").isoformat() if appointment_doc.get("created_at") else None,
            "updated_at": appointment_doc.get("updated_at").isoformat() if appointment_doc.get("updated_at") else None
        }
        appointments_list.append(appointment_data)
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": appointments_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if appointments_list else None,
            "to": skip + len(appointments_list) if appointments_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/appointments"
    }


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def store(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created appointment"""
    appointments_collection = get_collection(COLLECTIONS["appointments"])
    
    # Create appointment
    appointment_dict = appointment_data.dict()
    appointment_dict["client_id"] = ObjectId(appointment_data.client_id)
    appointment_dict["pet_id"] = ObjectId(appointment_data.pet_id)
    appointment_dict["veterinarian_id"] = ObjectId(appointment_data.veterinarian_id)
    appointment_dict["created_at"] = datetime.utcnow()
    appointment_dict["updated_at"] = datetime.utcnow()
    
    result = await appointments_collection.insert_one(appointment_dict)
    created_appointment = await appointments_collection.find_one({"_id": result.inserted_id})
    
    return AppointmentResponse(
        **created_appointment, 
        id=str(created_appointment["_id"]),
        client_id=str(created_appointment["client_id"]),
        pet_id=str(created_appointment["pet_id"]),
        veterinarian_id=str(created_appointment["veterinarian_id"])
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def show(
    appointment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Display the specified appointment"""
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID"
        )
    
    appointments_collection = get_collection(COLLECTIONS["appointments"])
    appointment_doc = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    
    if not appointment_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return AppointmentResponse(
        **appointment_doc, 
        id=str(appointment_doc["_id"]),
        client_id=str(appointment_doc["client_id"]),
        pet_id=str(appointment_doc["pet_id"]),
        veterinarian_id=str(appointment_doc["veterinarian_id"])
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update(
    appointment_id: str,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified appointment"""
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID"
        )
    
    appointments_collection = get_collection(COLLECTIONS["appointments"])
    
    # Check if appointment exists
    existing_appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Update appointment
    update_data = appointment_data.dict(exclude_unset=True)
    for field in ["client_id", "pet_id", "veterinarian_id"]:
        if field in update_data:
            update_data[field] = ObjectId(update_data[field])
    update_data["updated_at"] = datetime.utcnow()
    
    await appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": update_data}
    )
    
    updated_appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    return AppointmentResponse(
        **updated_appointment, 
        id=str(updated_appointment["_id"]),
        client_id=str(updated_appointment["client_id"]),
        pet_id=str(updated_appointment["pet_id"]),
        veterinarian_id=str(updated_appointment["veterinarian_id"])
    )


@router.delete("/{appointment_id}")
async def destroy(
    appointment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified appointment (soft delete)"""
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment ID"
        )
    
    appointments_collection = get_collection(COLLECTIONS["appointments"])
    
    # Check if appointment exists
    existing_appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Soft delete
    await appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Appointment deactivated successfully"} 