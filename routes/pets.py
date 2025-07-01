from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from enum import Enum

from database import get_collection, COLLECTIONS
from models.pet import Pet, PetCreate, PetUpdate, PetResponse, PetGender
from utils.auth import get_current_user
from models.user import User


router = APIRouter(prefix="/pets", tags=["Pets"])


async def populate_pet_relationships(pet_doc: dict, include: str = "") -> dict:
    """Populate pet relationships based on include parameter"""
    pet = pet_doc.copy()
    
    # Convert ObjectIds to strings for consistent ID handling
    pet["id"] = str(pet_doc["_id"])
    pet["client_id"] = str(pet_doc["client_id"])
    pet["species_id"] = str(pet_doc["species_id"])
    pet["breed_id"] = str(pet_doc["breed_id"])
    
    # Remove the original ObjectId field as it's not JSON serializable
    pet.pop("_id", None)
    
    # Add missing required fields for frontend
    pet["weight"] = pet_doc.get("weight")
    pet["gender"] = pet_doc.get("gender", "")
    pet["color"] = pet_doc.get("color", "")
    
    # Handle date fields safely and remove original datetime fields
    date_of_birth = pet_doc.get("dob") or pet_doc.get("date_of_birth")
    pet["dob"] = date_of_birth.isoformat() if date_of_birth and hasattr(date_of_birth, 'isoformat') else None
    pet.pop("date_of_birth", None)  # Remove original datetime field if it exists
    
    created_at = pet_doc.get("created_at")
    pet["created_at"] = created_at.isoformat() if created_at and hasattr(created_at, 'isoformat') else None
    
    updated_at = pet_doc.get("updated_at")
    pet["updated_at"] = updated_at.isoformat() if updated_at and hasattr(updated_at, 'isoformat') else None
    
    pet["name"] = pet_doc.get("name", "")
    pet["status"] = pet_doc.get("status", True)
    
    if not include:
        return pet
    
    include_list = [item.strip() for item in include.split(',')]
    
    # Populate client
    if 'client' in include_list and pet_doc.get("client_id"):
        clients_collection = get_collection(COLLECTIONS["clients"])
        client_doc = await clients_collection.find_one({"_id": pet_doc["client_id"]})
        if client_doc:
            pet["client"] = {
                "id": str(client_doc["_id"]),
                "name": client_doc.get("name", ""),
                "email": client_doc.get("email", ""),
                "phone": client_doc.get("phone_number", "")
            }
    
    # Populate species
    if 'species' in include_list and pet_doc.get("species_id"):
        species_collection = get_collection(COLLECTIONS["species"])
        species_doc = await species_collection.find_one({"_id": pet_doc["species_id"]})
        if species_doc:
            pet["species"] = {
                "id": str(species_doc["_id"]),
                "name": species_doc.get("name", "")
            }
    
    # Populate breed
    if 'breed' in include_list and pet_doc.get("breed_id"):
        breeds_collection = get_collection(COLLECTIONS["breeds"])
        breed_doc = await breeds_collection.find_one({"_id": pet_doc["breed_id"]})
        if breed_doc:
            pet["breed"] = {
                "id": str(breed_doc["_id"]),
                "name": breed_doc.get("name", "")
            }
    
    # Populate allergies
    if 'allergies' in include_list:
        allergies_collection = get_collection(COLLECTIONS["allergies"])
        allergies_cursor = allergies_collection.find({"pet_id": pet_doc["_id"]})
        allergies_list = []
        async for allergy_doc in allergies_cursor:
            allergies_list.append({
                "id": str(allergy_doc["_id"]),
                "allergen": allergy_doc.get("allergen", ""),
                "severity": allergy_doc.get("severity", "")
            })
        pet["allergies"] = allergies_list
    
    # Populate vaccinations
    if 'vaccinations' in include_list:
        vaccinations_collection = get_collection(COLLECTIONS["vaccinations"])
        vaccinations_cursor = vaccinations_collection.find({"pet_id": pet_doc["_id"]})
        vaccinations_list = []
        async for vaccination_doc in vaccinations_cursor:
            vaccinations_list.append({
                "id": str(vaccination_doc["_id"]),
                "vaccine_name": vaccination_doc.get("vaccine_name", ""),
                "vaccination_date": vaccination_doc.get("vaccination_date", ""),
                "next_due_date": vaccination_doc.get("next_due_date", "")
            })
        pet["vaccinations"] = vaccinations_list
    
    return pet


@router.get("/")
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    include: str = Query("", description="Comma-separated list of relationships to include"),
    include_inactive: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status: 'active', 'inactive', or 'all'"),
    client_id: Optional[str] = Query(None),
    species_id: Optional[str] = Query(None),
    breed_id: Optional[str] = Query(None),
    gender: Optional[PetGender] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the pets (matching Laravel pagination)"""
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Build query
    query = {}
    
    # Handle status filtering - prioritize the new 'status' parameter over 'include_inactive'
    if status:
        if status.lower() == "active":
            query["status"] = True
        elif status.lower() == "inactive":
            query["status"] = False
        # If status is "all", don't add any status filter
    elif include_inactive is None or include_inactive.lower() != "true":
        query["status"] = True
    
    if client_id:
        if not ObjectId.is_valid(client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID"
            )
        query["client_id"] = ObjectId(client_id)
    
    if species_id:
        if not ObjectId.is_valid(species_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid species ID"
            )
        query["species_id"] = ObjectId(species_id)
    
    if breed_id:
        if not ObjectId.is_valid(breed_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid breed ID"
            )
        query["breed_id"] = ObjectId(breed_id)
    
    if gender:
        query["gender"] = gender
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"color": {"$regex": search, "$options": "i"}}
        ]
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await pets_collection.count_documents(query)
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    
    # Execute query
    cursor = pets_collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(per_page)
    pets_list = []
    
    async for pet_doc in cursor:
        populated_pet = await populate_pet_relationships(pet_doc, include)
        pets_list.append(populated_pet)
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": pets_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if pets_list else None,
            "to": skip + len(pets_list) if pets_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/pets"
    }


@router.post("/", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def store(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created pet"""
    pets_collection = get_collection(COLLECTIONS["pets"])
    clients_collection = get_collection(COLLECTIONS["clients"])
    species_collection = get_collection(COLLECTIONS["species"])
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    
    # Validate client exists
    if not ObjectId.is_valid(pet_data.client_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )
    
    client = await clients_collection.find_one({"_id": ObjectId(pet_data.client_id), "status": True})
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Validate species exists
    if not ObjectId.is_valid(pet_data.species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid species ID"
        )
    
    species = await species_collection.find_one({"_id": ObjectId(pet_data.species_id), "status": True})
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Validate breed exists
    if not ObjectId.is_valid(pet_data.breed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid breed ID"
        )
    
    breed = await breeds_collection.find_one({"_id": ObjectId(pet_data.breed_id), "status": True})
    if not breed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breed not found"
        )
    
    # Create pet
    pet_dict = pet_data.dict()
    pet_dict["client_id"] = ObjectId(pet_data.client_id)
    pet_dict["species_id"] = ObjectId(pet_data.species_id)
    pet_dict["breed_id"] = ObjectId(pet_data.breed_id)
    pet_dict["created_at"] = datetime.utcnow()
    pet_dict["updated_at"] = datetime.utcnow()
    
    result = await pets_collection.insert_one(pet_dict)
    created_pet = await pets_collection.find_one({"_id": result.inserted_id})
    
    return PetResponse(
        **created_pet, 
        id=str(created_pet["_id"]),
        client_id=str(created_pet["client_id"]),
        species_id=str(created_pet["species_id"]),
        breed_id=str(created_pet["breed_id"])
    )


@router.get("/{pet_id}", response_model=PetResponse)
async def show(
    pet_id: str,
    include: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Display the specified pet"""
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    pet_doc = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    return PetResponse(
        **pet_doc, 
        id=str(pet_doc["_id"]),
        client_id=str(pet_doc["client_id"]),
        species_id=str(pet_doc["species_id"]),
        breed_id=str(pet_doc["breed_id"])
    )


@router.put("/{pet_id}")
async def update(
    pet_id: str,
    pet_data: PetUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified pet"""
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Check if pet exists
    existing_pet = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    if not existing_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    # Update pet
    update_data = pet_data.dict(exclude_unset=True)
    for field in ["client_id", "species_id", "breed_id"]:
        if field in update_data:
            update_data[field] = ObjectId(update_data[field])
    update_data["updated_at"] = datetime.utcnow()
    
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$set": update_data}
    )
    
    # If only updating status, return success message
    if len(update_data.keys()) == 2 and "status" in update_data:  # 2 because we always add updated_at
        action = "activated" if update_data["status"] else "deactivated"
        return {"message": f"Pet {action} successfully"}
    
    # For other updates, return the updated pet
    updated_pet = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    return PetResponse(
        **updated_pet, 
        id=str(updated_pet["_id"]),
        client_id=str(updated_pet["client_id"]),
        species_id=str(updated_pet["species_id"]),
        breed_id=str(updated_pet["breed_id"])
    )


@router.delete("/{pet_id}")
async def destroy(
    pet_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified pet (soft delete)"""
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Check if pet exists
    existing_pet = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    if not existing_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    # Soft delete
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Pet deactivated successfully"}


# Pet Allergies endpoints
@router.post("/{pet_id}/allergies")
async def add_allergy(
    pet_id: str,
    allergy_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Add allergy to pet"""
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID"
        )
    
    allergy_id = allergy_data.get("allergy_id")
    if not allergy_id or not ObjectId.is_valid(allergy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid allergy ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    allergies_collection = get_collection(COLLECTIONS["allergies"])
    
    # Check if pet and allergy exist
    pet = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    allergy = await allergies_collection.find_one({"_id": ObjectId(allergy_id)})
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy not found"
        )
    
    # Add allergy to pet's allergies array
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$addToSet": {"allergies": ObjectId(allergy_id)}}
    )
    
    return {"message": "Allergy added to pet successfully"}


@router.delete("/{pet_id}/allergies/{allergy_id}")
async def remove_allergy(
    pet_id: str,
    allergy_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove allergy from pet"""
    if not ObjectId.is_valid(pet_id) or not ObjectId.is_valid(allergy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID or allergy ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Remove allergy from pet's allergies array
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$pull": {"allergies": ObjectId(allergy_id)}}
    )
    
    return {"message": "Allergy removed from pet successfully"}


# Pet Vaccinations endpoints
@router.post("/{pet_id}/vaccinations")
async def add_vaccination(
    pet_id: str,
    vaccination_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Add vaccination to pet"""
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID"
        )
    
    vaccination_id = vaccination_data.get("vaccination_id")
    if not vaccination_id or not ObjectId.is_valid(vaccination_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vaccination ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    vaccinations_collection = get_collection(COLLECTIONS["vaccinations"])
    
    # Check if pet and vaccination exist
    pet = await pets_collection.find_one({"_id": ObjectId(pet_id)})
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    vaccination = await vaccinations_collection.find_one({"_id": ObjectId(vaccination_id)})
    if not vaccination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaccination not found"
        )
    
    # Add vaccination to pet's vaccinations array
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$addToSet": {"vaccinations": ObjectId(vaccination_id)}}
    )
    
    return {"message": "Vaccination added to pet successfully"}


@router.delete("/{pet_id}/vaccinations/{vaccination_id}")
async def remove_vaccination(
    pet_id: str,
    vaccination_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove vaccination from pet"""
    if not ObjectId.is_valid(pet_id) or not ObjectId.is_valid(vaccination_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID or vaccination ID"
        )
    
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Remove vaccination from pet's vaccinations array
    await pets_collection.update_one(
        {"_id": ObjectId(pet_id)},
        {"$pull": {"vaccinations": ObjectId(vaccination_id)}}
    )
    
    return {"message": "Vaccination removed from pet successfully"} 