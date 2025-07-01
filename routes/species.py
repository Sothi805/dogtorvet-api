from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.species import Species, SpeciesCreate, SpeciesUpdate, SpeciesResponse
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/species", tags=["Species"])


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    include_inactive: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status: 'active', 'inactive', or 'all'"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    include: Optional[str] = Query(None)
):
    """Display a listing of the species (matching Laravel pagination)"""
    species_collection = get_collection(COLLECTIONS["species"])
    
    # Build query
    query = {}
    
    # Handle status filtering - prioritize the new 'status' parameter over 'include_inactive'
    if status:
        if status.lower() == "active":
            query["status"] = True
        elif status.lower() == "inactive":
            query["status"] = False
        # If status is "all", don't add any status filter
    elif include_inactive != "true":
        query["status"] = True
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await species_collection.count_documents(query)
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    
    # Execute query
    cursor = species_collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(per_page)
    species_list = []
    
    async for species_doc in cursor:
        species_list.append(SpeciesResponse(**species_doc, id=str(species_doc["_id"])))
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": species_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if species_list else None,
            "to": skip + len(species_list) if species_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/species"
    }


@router.post("/", response_model=SpeciesResponse, status_code=status.HTTP_201_CREATED)
async def store(
    species_data: SpeciesCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created species"""
    species_collection = get_collection(COLLECTIONS["species"])
    
    # Check if species already exists (case insensitive)
    existing_species = await species_collection.find_one({
        "name": {"$regex": f"^{species_data.name}$", "$options": "i"}
    })
    if existing_species:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Species name already exists"
        )
    
    # Create species
    species_dict = species_data.dict()
    species_dict["created_at"] = datetime.utcnow()
    species_dict["updated_at"] = datetime.utcnow()
    
    result = await species_collection.insert_one(species_dict)
    created_species = await species_collection.find_one({"_id": result.inserted_id})
    
    return SpeciesResponse(**created_species, id=str(created_species["_id"]))


@router.get("/{species_id}", response_model=SpeciesResponse)
async def show(
    species_id: str,
    include: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Display the specified species"""
    if not ObjectId.is_valid(species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid species ID"
        )
    
    species_collection = get_collection(COLLECTIONS["species"])
    species_doc = await species_collection.find_one({"_id": ObjectId(species_id)})
    
    if not species_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    return SpeciesResponse(**species_doc, id=str(species_doc["_id"]))


@router.put("/{species_id}", response_model=SpeciesResponse)
async def update(
    species_id: str,
    species_data: SpeciesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified species"""
    if not ObjectId.is_valid(species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid species ID"
        )
    
    species_collection = get_collection(COLLECTIONS["species"])
    
    # Check if species exists
    existing_species = await species_collection.find_one({"_id": ObjectId(species_id)})
    if not existing_species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Check name uniqueness if being updated
    if species_data.name:
        name_check = await species_collection.find_one({
            "name": {"$regex": f"^{species_data.name}$", "$options": "i"},
            "_id": {"$ne": ObjectId(species_id)}
        })
        if name_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Species name already exists"
            )
    
    # Update species
    update_data = species_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await species_collection.update_one(
        {"_id": ObjectId(species_id)},
        {"$set": update_data}
    )
    
    updated_species = await species_collection.find_one({"_id": ObjectId(species_id)})
    return SpeciesResponse(**updated_species, id=str(updated_species["_id"]))


@router.delete("/{species_id}")
async def destroy(
    species_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified species (soft delete)"""
    if not ObjectId.is_valid(species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid species ID"
        )
    
    species_collection = get_collection(COLLECTIONS["species"])
    
    # Check if species exists
    existing_species = await species_collection.find_one({"_id": ObjectId(species_id)})
    if not existing_species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Soft delete
    await species_collection.update_one(
        {"_id": ObjectId(species_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Species deactivated successfully"} 