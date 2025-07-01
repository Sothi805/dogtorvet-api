from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.service import Service, ServiceCreate, ServiceUpdate, ServiceResponse
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the services"""
    services_collection = get_collection(COLLECTIONS["services"])
    
    query = {}
    skip = (page - 1) * per_page
    total = await services_collection.count_documents(query)
    
    cursor = services_collection.find(query).skip(skip).limit(per_page)
    services_list = []
    
    async for service_doc in cursor:
        # Convert ObjectId to string and provide defaults for missing fields
        service_data = {
            "id": str(service_doc["_id"]),
            "name": service_doc.get("name", ""),
            "description": service_doc.get("description", ""),
            "price": service_doc.get("price", 0.0),
            "duration_minutes": service_doc.get("duration_minutes", 30),
            "service_type": service_doc.get("service_type", "consultation"),
            "status": service_doc.get("status", True),
            "created_at": service_doc.get("created_at", ""),
            "updated_at": service_doc.get("updated_at", "")
        }
        services_list.append(service_data)
    
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": services_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if services_list else None,
            "to": skip + len(services_list) if services_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/services"
    }


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def store(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created service"""
    services_collection = get_collection(COLLECTIONS["services"])
    
    service_dict = service_data.dict()
    service_dict["created_at"] = datetime.utcnow()
    service_dict["updated_at"] = datetime.utcnow()
    
    result = await services_collection.insert_one(service_dict)
    created_service = await services_collection.find_one({"_id": result.inserted_id})
    
    return ServiceResponse(**created_service, id=str(created_service["_id"]))


@router.get("/{service_id}", response_model=ServiceResponse)
async def show(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Display the specified service"""
    if not ObjectId.is_valid(service_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID"
        )
    
    services_collection = get_collection(COLLECTIONS["services"])
    service_doc = await services_collection.find_one({"_id": ObjectId(service_id)})
    
    if not service_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return ServiceResponse(**service_doc, id=str(service_doc["_id"]))


@router.put("/{service_id}", response_model=ServiceResponse)
async def update(
    service_id: str,
    service_data: ServiceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified service"""
    if not ObjectId.is_valid(service_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID"
        )
    
    services_collection = get_collection(COLLECTIONS["services"])
    
    existing_service = await services_collection.find_one({"_id": ObjectId(service_id)})
    if not existing_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    update_data = service_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await services_collection.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": update_data}
    )
    
    updated_service = await services_collection.find_one({"_id": ObjectId(service_id)})
    return ServiceResponse(**updated_service, id=str(updated_service["_id"]))


@router.delete("/{service_id}")
async def destroy(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified service (soft delete)"""
    if not ObjectId.is_valid(service_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service ID"
        )
    
    services_collection = get_collection(COLLECTIONS["services"])
    
    existing_service = await services_collection.find_one({"_id": ObjectId(service_id)})
    if not existing_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    await services_collection.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Service deactivated successfully"} 