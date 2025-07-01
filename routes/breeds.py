from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.breed import Breed, BreedCreate, BreedUpdate, BreedResponse
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/breeds", tags=["Breeds"])


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    status: Optional[str] = Query("active"),  # 'active', 'inactive', or 'all'
    species_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the breeds (matching Laravel pagination)"""
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    
    # Build query
    query = {}
    if status == "active":
        query["status"] = True
    elif status == "inactive":
        query["status"] = False
    # If status == "all", don't filter by status
    
    if species_id:
        if not ObjectId.is_valid(species_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid species ID"
            )
        query["species_id"] = ObjectId(species_id)
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await breeds_collection.count_documents(query)
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    
    # Execute query
    cursor = breeds_collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(per_page)
    breeds_list = []
    
    # Get species collection for lookups
    species_collection = get_collection(COLLECTIONS["species"])
    
    async for breed_doc in cursor:
        # Load species data
        species_doc = await species_collection.find_one({"_id": breed_doc["species_id"]})
        species_data = None
        if species_doc:
            species_data = {
                "id": str(species_doc["_id"]),
                "name": species_doc["name"]
            }
        
        # Create breed response with species data
        breed_response = BreedResponse(
            id=str(breed_doc["_id"]),
            name=breed_doc["name"],
            species_id=str(breed_doc["species_id"]),
            status=breed_doc.get("status", True),
            created_at=breed_doc["created_at"].isoformat(),
            updated_at=breed_doc["updated_at"].isoformat(),
            species=species_data
        )
        breeds_list.append(breed_response)
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": breeds_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if breeds_list else None,
            "to": skip + len(breeds_list) if breeds_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/breeds"
    }


@router.post("/", response_model=BreedResponse, status_code=status.HTTP_201_CREATED)
async def store(
    breed_data: BreedCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created breed"""
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    species_collection = get_collection(COLLECTIONS["species"])
    
    # Validate species exists
    if not ObjectId.is_valid(breed_data.species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid species ID"
        )
    
    species = await species_collection.find_one({"_id": ObjectId(breed_data.species_id), "status": True})
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Create breed
    breed_dict = breed_data.dict()
    breed_dict["species_id"] = ObjectId(breed_data.species_id)
    breed_dict["created_at"] = datetime.utcnow()
    breed_dict["updated_at"] = datetime.utcnow()
    
    result = await breeds_collection.insert_one(breed_dict)
    created_breed = await breeds_collection.find_one({"_id": result.inserted_id})
    
    return BreedResponse(
        id=str(created_breed["_id"]),
        name=created_breed["name"],
        species_id=str(created_breed["species_id"]),
        status=created_breed.get("status", True),
        created_at=created_breed["created_at"].isoformat(),
        updated_at=created_breed["updated_at"].isoformat()
    )


@router.get("/{breed_id}", response_model=BreedResponse)
async def show(
    breed_id: str,
    current_user: User = Depends(get_current_user)
):
    """Display the specified breed"""
    if not ObjectId.is_valid(breed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid breed ID"
        )
    
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    breed_doc = await breeds_collection.find_one({"_id": ObjectId(breed_id)})
    
    if not breed_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breed not found"
        )
    
    return BreedResponse(
        id=str(breed_doc["_id"]),
        name=breed_doc["name"],
        species_id=str(breed_doc["species_id"]),
        status=breed_doc.get("status", True),
        created_at=breed_doc["created_at"].isoformat(),
        updated_at=breed_doc["updated_at"].isoformat()
    )


@router.put("/{breed_id}", response_model=BreedResponse)
async def update(
    breed_id: str,
    breed_data: BreedUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified breed"""
    if not ObjectId.is_valid(breed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid breed ID"
        )
    
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    
    # Check if breed exists
    existing_breed = await breeds_collection.find_one({"_id": ObjectId(breed_id)})
    if not existing_breed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breed not found"
        )
    
    # Update breed
    update_data = breed_data.dict(exclude_unset=True)
    if "species_id" in update_data:
        update_data["species_id"] = ObjectId(update_data["species_id"])
    update_data["updated_at"] = datetime.utcnow()
    
    await breeds_collection.update_one(
        {"_id": ObjectId(breed_id)},
        {"$set": update_data}
    )
    
    updated_breed = await breeds_collection.find_one({"_id": ObjectId(breed_id)})
    return BreedResponse(
        id=str(updated_breed["_id"]),
        name=updated_breed["name"],
        species_id=str(updated_breed["species_id"]),
        status=updated_breed.get("status", True),
        created_at=updated_breed["created_at"].isoformat(),
        updated_at=updated_breed["updated_at"].isoformat()
    )


@router.delete("/{breed_id}")
async def destroy(
    breed_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified breed (soft delete)"""
    if not ObjectId.is_valid(breed_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid breed ID"
        )
    
    breeds_collection = get_collection(COLLECTIONS["breeds"])
    
    # Check if breed exists
    existing_breed = await breeds_collection.find_one({"_id": ObjectId(breed_id)})
    if not existing_breed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Breed not found"
        )
    
    # Soft delete
    await breeds_collection.update_one(
        {"_id": ObjectId(breed_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Breed deactivated successfully"} 