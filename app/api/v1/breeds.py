from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import breed_crud
from app.schemas.breed import BreedDB, BreedCreate, BreedUpdate, BreedResponse
from app.schemas.base import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_breeds(
    species_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_active_user)
):
    """Get all breeds, optionally filtered by species_id and status."""
    collection = database.get_collection(COLLECTIONS["breeds"])
    
    # Build filters
    filters = {}
    if species_id:
        filters["species_id"] = species_id
    if status and status != "all":
        if status == "active":
            filters["status"] = True
        elif status == "inactive":
            filters["status"] = False
    # If status is "all" or not provided, don't filter by status
    
    breeds = await breed_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
    
    # Simple response without complex schema validation
    breed_response = []
    for breed in breeds:
        try:
            # Get species information
            species_collection = database.get_collection(COLLECTIONS["species"])
            species = await species_collection.find_one({"_id": breed.species_id})
            species_name = species.get("name", "Unknown") if species else "Unknown"
            
            breed_response.append({
                "id": str(breed.id),
                "name": breed.name,
                "species_id": str(breed.species_id),
                "species": {
                    "id": str(breed.species_id),
                    "name": species_name
                },
                "created_at": breed.created_at,
                "updated_at": breed.updated_at,
                "status": breed.status
            })
        except Exception as e:
            print(f"⚠️ Error processing breed {breed.id}: {e}")
            continue
    return APIResponse(success=True, message="Breeds retrieved successfully", data=breed_response)

@router.post("/", response_model=APIResponse)
async def create_breed(
    breed_create: BreedCreate,
    current_user=Depends(get_current_active_user)
):
    """Create a new breed."""
    collection = database.get_collection(COLLECTIONS["breeds"])
    # Check if breed name already exists for this species
    if await breed_crud.name_exists_for_species(collection, breed_create.name, breed_create.species_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Breed name already exists for this species")
    breed = await breed_crud.create(collection, breed_create)
    # Get species information
    species_collection = database.get_collection(COLLECTIONS["species"])
    species = await species_collection.find_one({"_id": breed.species_id})
    species_name = species.get("name", "Unknown") if species else "Unknown"
    
    return APIResponse(success=True, message="Breed created successfully", data={
        "id": str(breed.id),
        "name": breed.name,
        "species_id": str(breed.species_id),
        "species": {
            "id": str(breed.species_id),
            "name": species_name
        },
        "created_at": breed.created_at,
        "updated_at": breed.updated_at,
        "status": breed.status
    })

@router.get("/{breed_id}", response_model=APIResponse)
async def get_breed_by_id(
    breed_id: str,
    current_user=Depends(get_current_active_user)
):
    """Get a specific breed."""
    collection = database.get_collection(COLLECTIONS["breeds"])
    breed = await breed_crud.get(collection, breed_id)
    if not breed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found")
    # Get species information
    species_collection = database.get_collection(COLLECTIONS["species"])
    species = await species_collection.find_one({"_id": breed.species_id})
    species_name = species.get("name", "Unknown") if species else "Unknown"
    
    return APIResponse(success=True, message="Breed retrieved successfully", data={
        "id": str(breed.id),
        "name": breed.name,
        "species_id": str(breed.species_id),
        "species": {
            "id": str(breed.species_id),
            "name": species_name
        },
        "created_at": breed.created_at,
        "updated_at": breed.updated_at,
        "status": breed.status
    })

@router.put("/{breed_id}", response_model=APIResponse)
async def update_breed(
    breed_id: str,
    breed_update: BreedUpdate,
    current_user=Depends(get_current_active_user)
):
    """Update a breed."""
    collection = database.get_collection(COLLECTIONS["breeds"])
    existing_breed = await breed_crud.get(collection, breed_id)
    if not existing_breed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found")
    # Check for name conflict
    if breed_update.name and breed_update.name != existing_breed.name:
        if await breed_crud.name_exists_for_species(collection, breed_update.name, existing_breed.species_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Breed name already exists for this species")
    breed = await breed_crud.update(collection, breed_id, breed_update)
    if not breed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found")
    # Get species information
    species_collection = database.get_collection(COLLECTIONS["species"])
    species = await species_collection.find_one({"_id": breed.species_id})
    species_name = species.get("name", "Unknown") if species else "Unknown"
    
    return APIResponse(success=True, message="Breed updated successfully", data={
        "id": str(breed.id),
        "name": breed.name,
        "species_id": str(breed.species_id),
        "species": {
            "id": str(breed.species_id),
            "name": species_name
        },
        "created_at": breed.created_at,
        "updated_at": breed.updated_at,
        "status": breed.status
    })

@router.delete("/{breed_id}", response_model=APIResponse)
async def delete_breed(
    breed_id: str,
    current_user=Depends(get_current_active_user)
):
    """Delete a breed."""
    collection = database.get_collection(COLLECTIONS["breeds"])
    if not await breed_crud.exists(collection, breed_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found")
    success = await breed_crud.delete(collection, breed_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found")
    return APIResponse(success=True, message="Breed deleted successfully", data=None) 