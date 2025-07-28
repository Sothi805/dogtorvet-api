from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud.allergy_type import allergy_type_crud
from app.schemas.allergy_type import AllergyTypeDB, AllergyTypeCreate, AllergyTypeUpdate, AllergyTypeResponse
from app.schemas.base import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_allergies(
    status: Optional[str] = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_active_user)
):
    """Get all allergies with filtering"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        # Build filters
        filters = {}
        if status and status != "all":
            if status == "active":
                filters["status"] = True
            elif status == "inactive":
                filters["status"] = False
        
        print(f"🔍 Fetching allergies with filters: {filters}")
        
        # Get allergies with pagination
        allergies = await allergy_type_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
        
        print(f"📊 Found {len(allergies)} allergies")
        
        # Simple response without complex schema validation
        allergy_response = []
        for allergy in allergies:
            try:
                allergy_response.append({
                    "id": str(allergy.id),
                    "name": allergy.name,
                    "description": allergy.description,
                    "created_at": allergy.created_at,
                    "updated_at": allergy.updated_at,
                    "status": allergy.status
                })
            except Exception as e:
                print(f"⚠️ Error processing allergy {allergy.id}: {e}")
                continue
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(allergy_response)} allergies",
            data=allergy_response
        )
        
    except Exception as e:
        print(f"❌ Error in get_allergies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve allergies: {str(e)}"
        )

@router.post("/", response_model=APIResponse)
async def create_allergy(
    allergy_create: AllergyTypeCreate,
    current_user=Depends(get_current_active_user)
):
    """Create a new allergy"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        # Check if allergy name already exists
        if await allergy_type_crud.name_exists(collection, allergy_create.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allergy name already exists")
        
        allergy = await allergy_type_crud.create(collection, allergy_create)
        
        return APIResponse(success=True, message="Allergy created successfully", data={
            "id": str(allergy.id),
            "name": allergy.name,
            "description": allergy.description,
            "created_at": allergy.created_at,
            "updated_at": allergy.updated_at,
            "status": allergy.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in create_allergy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create allergy: {str(e)}"
        )

@router.get("/{allergy_id}", response_model=APIResponse)
async def get_allergy(
    allergy_id: str,
    current_user=Depends(get_current_active_user)
):
    """Get a specific allergy by ID"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        allergy = await allergy_type_crud.get(collection, allergy_id)
        if not allergy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
        
        return APIResponse(success=True, message="Allergy retrieved successfully", data={
            "id": str(allergy.id),
            "name": allergy.name,
            "description": allergy.description,
            "created_at": allergy.created_at,
            "updated_at": allergy.updated_at,
            "status": allergy.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_allergy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve allergy: {str(e)}"
        )

@router.put("/{allergy_id}", response_model=APIResponse)
async def update_allergy(
    allergy_id: str,
    allergy_update: AllergyTypeUpdate,
    current_user=Depends(get_current_active_user)
):
    """Update an allergy"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        # Check if allergy exists
        existing_allergy = await allergy_type_crud.get(collection, allergy_id)
        if not existing_allergy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
        
        # Check if new name conflicts with existing allergy
        if allergy_update.name:
            name_conflict = await allergy_type_crud.get_by_name(collection, allergy_update.name)
            if name_conflict and str(name_conflict.id) != allergy_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Allergy name already exists")
        
        allergy = await allergy_type_crud.update(collection, allergy_id, allergy_update)
        
        return APIResponse(success=True, message="Allergy updated successfully", data={
            "id": str(allergy.id),
            "name": allergy.name,
            "description": allergy.description,
            "created_at": allergy.created_at,
            "updated_at": allergy.updated_at,
            "status": allergy.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_allergy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update allergy: {str(e)}"
        )

@router.put("/{allergy_id}/toggle-status", response_model=APIResponse)
async def toggle_allergy_status(
    allergy_id: str,
    current_user=Depends(get_current_active_user)
):
    """Toggle allergy status (activate/deactivate)"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        allergy = await allergy_type_crud.get(collection, allergy_id)
        if not allergy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
        
        # Toggle status
        new_status = not allergy.status
        allergy = await allergy_type_crud.update(collection, allergy_id, {"status": new_status})
        
        action = "activated" if new_status else "deactivated"
        return APIResponse(success=True, message=f"Allergy {action} successfully", data={
            "id": str(allergy.id),
            "name": allergy.name,
            "status": allergy.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in toggle_allergy_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle allergy status: {str(e)}"
        )

@router.delete("/{allergy_id}", response_model=APIResponse)
async def delete_allergy(
    allergy_id: str,
    current_user=Depends(get_current_active_user)
):
    """Delete an allergy (soft delete)"""
    try:
        collection = database.get_collection(COLLECTIONS["allergies"])
        
        allergy = await allergy_type_crud.get(collection, allergy_id)
        if not allergy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found")
        
        # Soft delete by setting status to False
        await allergy_type_crud.update(collection, allergy_id, {"status": False})
        
        return APIResponse(success=True, message="Allergy deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in delete_allergy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete allergy: {str(e)}"
        ) 