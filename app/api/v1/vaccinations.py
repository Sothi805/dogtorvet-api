from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud.vaccination_type import vaccination_type_crud
from app.schemas.vaccination_type import VaccinationTypeDB, VaccinationTypeCreate, VaccinationTypeUpdate, VaccinationTypeResponse
from app.schemas.base import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_vaccinations(
    status: Optional[str] = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_active_user)
):
    """Get all vaccinations with filtering"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        # Build filters
        filters = {}
        if status and status != "all":
            if status == "active":
                filters["status"] = True
            elif status == "inactive":
                filters["status"] = False
        
        print(f"🔍 Fetching vaccinations with filters: {filters}")
        
        # Get vaccinations with pagination
        vaccinations = await vaccination_type_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
        
        print(f"📊 Found {len(vaccinations)} vaccinations")
        
        # Simple response without complex schema validation
        vaccination_response = []
        for vaccination in vaccinations:
            try:
                vaccination_response.append({
                    "id": str(vaccination.id),
                    "name": vaccination.name,
                    "description": vaccination.description,
                    "duration_months": vaccination.duration_months,
                    "created_at": vaccination.created_at,
                    "updated_at": vaccination.updated_at,
                    "status": vaccination.status
                })
            except Exception as e:
                print(f"⚠️ Error processing vaccination {vaccination.id}: {e}")
                continue
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(vaccination_response)} vaccinations",
            data=vaccination_response
        )
        
    except Exception as e:
        print(f"❌ Error in get_vaccinations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vaccinations: {str(e)}"
        )

@router.post("/", response_model=APIResponse)
async def create_vaccination(
    vaccination_create: VaccinationTypeCreate,
    current_user=Depends(get_current_active_user)
):
    """Create a new vaccination"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        # Check if vaccination name already exists
        if await vaccination_type_crud.name_exists(collection, vaccination_create.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vaccination name already exists")
        
        vaccination = await vaccination_type_crud.create(collection, vaccination_create)
        
        return APIResponse(success=True, message="Vaccination created successfully", data={
            "id": str(vaccination.id),
            "name": vaccination.name,
            "description": vaccination.description,
            "duration_months": vaccination.duration_months,
            "created_at": vaccination.created_at,
            "updated_at": vaccination.updated_at,
            "status": vaccination.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in create_vaccination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vaccination: {str(e)}"
        )

@router.get("/{vaccination_id}", response_model=APIResponse)
async def get_vaccination(
    vaccination_id: str,
    current_user=Depends(get_current_active_user)
):
    """Get a specific vaccination by ID"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        vaccination = await vaccination_type_crud.get(collection, vaccination_id)
        if not vaccination:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
        
        return APIResponse(success=True, message="Vaccination retrieved successfully", data={
            "id": str(vaccination.id),
            "name": vaccination.name,
            "description": vaccination.description,
            "duration_months": vaccination.duration_months,
            "created_at": vaccination.created_at,
            "updated_at": vaccination.updated_at,
            "status": vaccination.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_vaccination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vaccination: {str(e)}"
        )

@router.put("/{vaccination_id}", response_model=APIResponse)
async def update_vaccination(
    vaccination_id: str,
    vaccination_update: VaccinationTypeUpdate,
    current_user=Depends(get_current_active_user)
):
    """Update a vaccination"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        # Check if vaccination exists
        existing_vaccination = await vaccination_type_crud.get(collection, vaccination_id)
        if not existing_vaccination:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
        
        # Check if new name conflicts with existing vaccination
        if vaccination_update.name:
            name_conflict = await vaccination_type_crud.get_by_name(collection, vaccination_update.name)
            if name_conflict and str(name_conflict.id) != vaccination_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vaccination name already exists")
        
        vaccination = await vaccination_type_crud.update(collection, vaccination_id, vaccination_update)
        
        return APIResponse(success=True, message="Vaccination updated successfully", data={
            "id": str(vaccination.id),
            "name": vaccination.name,
            "description": vaccination.description,
            "duration_months": vaccination.duration_months,
            "created_at": vaccination.created_at,
            "updated_at": vaccination.updated_at,
            "status": vaccination.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_vaccination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vaccination: {str(e)}"
        )

@router.put("/{vaccination_id}/toggle-status", response_model=APIResponse)
async def toggle_vaccination_status(
    vaccination_id: str,
    current_user=Depends(get_current_active_user)
):
    """Toggle vaccination status (activate/deactivate)"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        vaccination = await vaccination_type_crud.get(collection, vaccination_id)
        if not vaccination:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
        
        # Toggle status
        new_status = not vaccination.status
        vaccination = await vaccination_type_crud.update(collection, vaccination_id, {"status": new_status})
        
        action = "activated" if new_status else "deactivated"
        return APIResponse(success=True, message=f"Vaccination {action} successfully", data={
            "id": str(vaccination.id),
            "name": vaccination.name,
            "status": vaccination.status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in toggle_vaccination_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle vaccination status: {str(e)}"
        )

@router.delete("/{vaccination_id}", response_model=APIResponse)
async def delete_vaccination(
    vaccination_id: str,
    current_user=Depends(get_current_active_user)
):
    """Delete a vaccination (soft delete)"""
    try:
        collection = database.get_collection(COLLECTIONS["vaccinations"])
        
        vaccination = await vaccination_type_crud.get(collection, vaccination_id)
        if not vaccination:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
        
        # Soft delete by setting status to False
        await vaccination_type_crud.update(collection, vaccination_id, {"status": False})
        
        return APIResponse(success=True, message="Vaccination deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in delete_vaccination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vaccination: {str(e)}"
        ) 