from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.vaccination import VaccinationCreate, VaccinationUpdate, VaccinationResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/vaccinations", tags=["vaccinations"])

@router.get("/", response_model=dict)
async def get_vaccinations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    current_user=Depends(get_current_user)
):
    """Get all vaccinations with pagination and search"""
    try:
        collection = get_collection(COLLECTIONS["vaccinations"])
        
        # Build filter
        filter_query = {}
        
        # Status filter
        if status == "active":
            filter_query["status"] = True
        elif status == "inactive":
            filter_query["status"] = False
        # If status == "all", don't add status filter
            
        # Search filter
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Count total
        total = await collection.count_documents(filter_query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        # Get vaccinations
        cursor = collection.find(filter_query).skip(skip).limit(per_page).sort("name", 1)
        vaccinations = []
        async for doc in cursor:
            vaccination = {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "description": doc.get("description", ""),
                "duration_months": doc.get("duration_months", 12),
                "status": doc.get("status", True),
                "created_at": doc.get("created_at", datetime.utcnow()).isoformat(),
                "updated_at": doc.get("updated_at", datetime.utcnow()).isoformat()
            }
            vaccinations.append(vaccination)
        
        return {
            "data": vaccinations,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vaccinations: {str(e)}")

@router.post("/", response_model=VaccinationResponse)
async def create_vaccination(
    vaccination_data: VaccinationCreate,
    current_user=Depends(get_current_user)
):
    """Create a new vaccination"""
    try:
        collection = get_collection(COLLECTIONS["vaccinations"])
        
        # Check if vaccination name already exists
        existing = await collection.find_one({"name": vaccination_data.name})
        if existing:
            raise HTTPException(status_code=400, detail="Vaccination with this name already exists")
        
        # Create vaccination document
        vaccination_doc = {
            "name": vaccination_data.name,
            "description": vaccination_data.description,
            "duration_months": vaccination_data.duration_months,
            "status": vaccination_data.status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await collection.insert_one(vaccination_doc)
        
        # Return created vaccination
        created_vaccination = await collection.find_one({"_id": result.inserted_id})
        return {
            "id": str(created_vaccination["_id"]),
            "name": created_vaccination["name"],
            "description": created_vaccination["description"],
            "duration_months": created_vaccination["duration_months"],
            "status": created_vaccination["status"],
            "created_at": created_vaccination["created_at"].isoformat(),
            "updated_at": created_vaccination["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vaccination: {str(e)}")

@router.get("/{vaccination_id}", response_model=VaccinationResponse)
async def get_vaccination(
    vaccination_id: str,
    current_user=Depends(get_current_user)
):
    """Get a specific vaccination by ID"""
    try:
        collection = get_collection(COLLECTIONS["vaccinations"])
        
        vaccination = await collection.find_one({"_id": ObjectId(vaccination_id)})
        if not vaccination:
            raise HTTPException(status_code=404, detail="Vaccination not found")
        
        return {
            "id": str(vaccination["_id"]),
            "name": vaccination["name"],
            "description": vaccination["description"],
            "duration_months": vaccination["duration_months"],
            "status": vaccination["status"],
            "created_at": vaccination["created_at"].isoformat(),
            "updated_at": vaccination["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vaccination: {str(e)}")

@router.put("/{vaccination_id}", response_model=VaccinationResponse)
async def update_vaccination(
    vaccination_id: str,
    vaccination_data: VaccinationUpdate,
    current_user=Depends(get_current_user)
):
    """Update a vaccination"""
    try:
        collection = get_collection(COLLECTIONS["vaccinations"])
        
        # Check if vaccination exists
        existing = await collection.find_one({"_id": ObjectId(vaccination_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Vaccination not found")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow()}
        if vaccination_data.name is not None:
            update_data["name"] = vaccination_data.name
        if vaccination_data.description is not None:
            update_data["description"] = vaccination_data.description
        if vaccination_data.duration_months is not None:
            update_data["duration_months"] = vaccination_data.duration_months
        if vaccination_data.status is not None:
            update_data["status"] = vaccination_data.status
        
        # Update vaccination
        await collection.update_one(
            {"_id": ObjectId(vaccination_id)},
            {"$set": update_data}
        )
        
        # Return updated vaccination
        updated_vaccination = await collection.find_one({"_id": ObjectId(vaccination_id)})
        return {
            "id": str(updated_vaccination["_id"]),
            "name": updated_vaccination["name"],
            "description": updated_vaccination["description"],
            "duration_months": updated_vaccination["duration_months"],
            "status": updated_vaccination["status"],
            "created_at": updated_vaccination["created_at"].isoformat(),
            "updated_at": updated_vaccination["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vaccination: {str(e)}")

@router.put("/{vaccination_id}/toggle-status")
async def toggle_vaccination_status(
    vaccination_id: str,
    current_user=Depends(get_current_user)
):
    """Toggle vaccination status (soft delete)"""
    try:
        collection = get_collection(COLLECTIONS["vaccinations"])
        
        # Check if vaccination exists
        existing = await collection.find_one({"_id": ObjectId(vaccination_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Vaccination not found")
        
        # Toggle status
        new_status = not existing.get("status", True)
        await collection.update_one(
            {"_id": ObjectId(vaccination_id)},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
        )
        
        action = "activated" if new_status else "deactivated"
        return {"message": f"Vaccination {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle vaccination status: {str(e)}") 