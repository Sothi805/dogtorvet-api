from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.allergy import AllergyCreate, AllergyUpdate, AllergyResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/allergies", tags=["allergies"])

@router.get("/", response_model=dict)
async def get_allergies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    current_user=Depends(get_current_user)
):
    """Get all allergies with pagination and search"""
    try:
        collection = get_collection(COLLECTIONS["allergies"])
        
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
        
        # Get allergies
        cursor = collection.find(filter_query).skip(skip).limit(per_page).sort("name", 1)
        allergies = []
        async for doc in cursor:
            allergy = {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "description": doc.get("description", ""),
                "status": doc.get("status", True),
                "created_at": doc.get("created_at", datetime.utcnow()).isoformat(),
                "updated_at": doc.get("updated_at", datetime.utcnow()).isoformat()
            }
            allergies.append(allergy)
        
        return {
            "data": allergies,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch allergies: {str(e)}")

@router.post("/", response_model=AllergyResponse)
async def create_allergy(
    allergy_data: AllergyCreate,
    current_user=Depends(get_current_user)
):
    """Create a new allergy"""
    try:
        collection = get_collection(COLLECTIONS["allergies"])
        
        # Check if allergy name already exists
        existing = await collection.find_one({"name": allergy_data.name})
        if existing:
            raise HTTPException(status_code=400, detail="Allergy with this name already exists")
        
        # Create allergy document
        allergy_doc = {
            "name": allergy_data.name,
            "description": allergy_data.description,
            "status": allergy_data.status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await collection.insert_one(allergy_doc)
        
        # Return created allergy
        created_allergy = await collection.find_one({"_id": result.inserted_id})
        return {
            "id": str(created_allergy["_id"]),
            "name": created_allergy["name"],
            "description": created_allergy["description"],
            "status": created_allergy["status"],
            "created_at": created_allergy["created_at"].isoformat(),
            "updated_at": created_allergy["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create allergy: {str(e)}")

@router.get("/{allergy_id}", response_model=AllergyResponse)
async def get_allergy(
    allergy_id: str,
    current_user=Depends(get_current_user)
):
    """Get a specific allergy by ID"""
    try:
        collection = get_collection(COLLECTIONS["allergies"])
        
        allergy = await collection.find_one({"_id": ObjectId(allergy_id)})
        if not allergy:
            raise HTTPException(status_code=404, detail="Allergy not found")
        
        return {
            "id": str(allergy["_id"]),
            "name": allergy["name"],
            "description": allergy["description"],
            "status": allergy["status"],
            "created_at": allergy["created_at"].isoformat(),
            "updated_at": allergy["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch allergy: {str(e)}")

@router.put("/{allergy_id}", response_model=AllergyResponse)
async def update_allergy(
    allergy_id: str,
    allergy_data: AllergyUpdate,
    current_user=Depends(get_current_user)
):
    """Update an allergy"""
    try:
        collection = get_collection(COLLECTIONS["allergies"])
        
        # Check if allergy exists
        existing = await collection.find_one({"_id": ObjectId(allergy_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Allergy not found")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow()}
        if allergy_data.name is not None:
            update_data["name"] = allergy_data.name
        if allergy_data.description is not None:
            update_data["description"] = allergy_data.description
        if allergy_data.status is not None:
            update_data["status"] = allergy_data.status
        
        # Update allergy
        await collection.update_one(
            {"_id": ObjectId(allergy_id)},
            {"$set": update_data}
        )
        
        # Return updated allergy
        updated_allergy = await collection.find_one({"_id": ObjectId(allergy_id)})
        return {
            "id": str(updated_allergy["_id"]),
            "name": updated_allergy["name"],
            "description": updated_allergy["description"],
            "status": updated_allergy["status"],
            "created_at": updated_allergy["created_at"].isoformat(),
            "updated_at": updated_allergy["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update allergy: {str(e)}")

@router.put("/{allergy_id}/toggle-status")
async def toggle_allergy_status(
    allergy_id: str,
    current_user=Depends(get_current_user)
):
    """Toggle allergy status (soft delete)"""
    try:
        collection = get_collection(COLLECTIONS["allergies"])
        
        # Check if allergy exists
        existing = await collection.find_one({"_id": ObjectId(allergy_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Allergy not found")
        
        # Toggle status
        new_status = not existing.get("status", True)
        await collection.update_one(
            {"_id": ObjectId(allergy_id)},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
        )
        
        action = "activated" if new_status else "deactivated"
        return {"message": f"Allergy {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle allergy status: {str(e)}") 