from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import species_crud
from app.schemas.species import SpeciesDB, SpeciesCreate, SpeciesUpdate, SpeciesResponse
from app.schemas.base import APIResponse


router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_species(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: SpeciesDB = Depends(get_current_active_user)
):
    """Get all species, optionally filtered by status."""
    collection = database.get_collection(COLLECTIONS["species"])
    
    # Build filters
    filters = {}
    if status and status != "all":
        if status == "active":
            filters["status"] = True
        elif status == "inactive":
            filters["status"] = False
    
    species_list = await species_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
    
    species_response = [
        SpeciesResponse(
            id=str(species.id),
            name=species.name,
            description=species.description,
            created_at=species.created_at,
            updated_at=species.updated_at,
            status=species.status
        )
        for species in species_list
    ]
    
    return APIResponse(
        success=True,
        message="Species retrieved successfully",
        data=species_response
    )


@router.post("/", response_model=APIResponse)
async def create_species(
    species_create: SpeciesCreate,
    current_user: SpeciesDB = Depends(get_current_active_user)
):
    """Create a new species."""
    collection = database.get_collection(COLLECTIONS["species"])
    
    # Check if species name already exists
    if await species_crud.name_exists(collection, species_create.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Species name already exists"
        )
    
    # Create species
    species = await species_crud.create(collection, species_create)
    
    return APIResponse(
        success=True,
        message="Species created successfully",
        data=SpeciesResponse(
            id=str(species.id),
            name=species.name,
            description=species.description,
            created_at=species.created_at,
            updated_at=species.updated_at,
            status=species.status
        )
    )


@router.get("/{species_id}", response_model=APIResponse)
async def get_species_by_id(
    species_id: str,
    current_user: SpeciesDB = Depends(get_current_active_user)
):
    """Get a specific species."""
    collection = database.get_collection(COLLECTIONS["species"])
    species = await species_crud.get(collection, species_id)
    
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    return APIResponse(
        success=True,
        message="Species retrieved successfully",
        data=SpeciesResponse(
            id=str(species.id),
            name=species.name,
            description=species.description,
            created_at=species.created_at,
            updated_at=species.updated_at,
            status=species.status
        )
    )


@router.put("/{species_id}", response_model=APIResponse)
async def update_species(
    species_id: str,
    species_update: SpeciesUpdate,
    current_user: SpeciesDB = Depends(get_current_active_user)
):
    """Update a species."""
    collection = database.get_collection(COLLECTIONS["species"])
    
    # Check if species exists
    existing_species = await species_crud.get(collection, species_id)
    if not existing_species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Check if species name already exists for another species
    if species_update.name and species_update.name != existing_species.name:
        if await species_crud.name_exists(collection, species_update.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Species name already exists"
            )
    
    # Update species
    species = await species_crud.update(collection, species_id, species_update)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    return APIResponse(
        success=True,
        message="Species updated successfully",
        data=SpeciesResponse(
            id=str(species.id),
            name=species.name,
            description=species.description,
            created_at=species.created_at,
            updated_at=species.updated_at,
            status=species.status
        )
    )


@router.delete("/{species_id}", response_model=APIResponse)
async def delete_species(
    species_id: str,
    current_user: SpeciesDB = Depends(get_current_active_user)
):
    """Delete a species."""
    collection = database.get_collection(COLLECTIONS["species"])
    
    # Check if species exists
    if not await species_crud.exists(collection, species_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Delete species
    success = await species_crud.delete(collection, species_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    return APIResponse(
        success=True,
        message="Species deleted successfully",
        data=None
    ) 