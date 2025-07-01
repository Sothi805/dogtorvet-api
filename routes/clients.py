from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.client import Client, ClientCreate, ClientUpdate, ClientResponse
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=dict)
async def get_clients(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or phone"),
    current_user: User = Depends(get_current_user)
):
    """Get all clients with Laravel-style pagination"""
    clients_collection = get_collection(COLLECTIONS["clients"])
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone_number": {"$regex": search, "$options": "i"}}
        ]
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await clients_collection.count_documents(query)
    
    # Execute query
    cursor = clients_collection.find(query).skip(skip).limit(per_page)
    clients_list = []
    
    async for client_doc in cursor:
        # Convert ObjectId to string and provide defaults for missing fields
        client_data = {
            "id": str(client_doc["_id"]),  # Use actual MongoDB ObjectId as string
            "name": client_doc.get("name", ""),
            "email": client_doc.get("email", ""),
            "phone_number": client_doc.get("phone_number", ""),
            "gender": client_doc.get("gender", "other"),
            "other_contact_info": client_doc.get("other_contact_info", ""),
            "status": client_doc.get("status", True),
            "created_at": client_doc.get("created_at").isoformat() if client_doc.get("created_at") else None,
            "updated_at": client_doc.get("updated_at").isoformat() if client_doc.get("updated_at") else None
        }
        
        clients_list.append(client_data)
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": clients_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if clients_list else None,
            "to": skip + len(clients_list) if clients_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/clients"
    }


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get client by ID"""
    if not ObjectId.is_valid(client_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )
    
    clients_collection = get_collection(COLLECTIONS["clients"])
    client_doc = await clients_collection.find_one({"_id": ObjectId(client_id), "status": True})
    
    if not client_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return ClientResponse(**client_doc, id=str(client_doc["_id"]))


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new client"""
    clients_collection = get_collection(COLLECTIONS["clients"])
    
    # Check if phone number already exists
    existing_client = await clients_collection.find_one({"phone_number": client_data.phone_number})
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create client
    client_dict = client_data.dict()
    client_dict["created_at"] = datetime.utcnow()
    client_dict["updated_at"] = datetime.utcnow()
    
    result = await clients_collection.insert_one(client_dict)
    created_client = await clients_collection.find_one({"_id": result.inserted_id})
    
    return ClientResponse(**created_client, id=str(created_client["_id"]))


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update client"""
    if not ObjectId.is_valid(client_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )
    
    clients_collection = get_collection(COLLECTIONS["clients"])
    
    # Check if client exists
    existing_client = await clients_collection.find_one({"_id": ObjectId(client_id)})
    if not existing_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check phone number uniqueness if being updated
    if client_data.phone_number:
        phone_check = await clients_collection.find_one({
            "phone_number": client_data.phone_number,
            "_id": {"$ne": ObjectId(client_id)}
        })
        if phone_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Update client
    update_data = client_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await clients_collection.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": update_data}
    )
    
    updated_client = await clients_collection.find_one({"_id": ObjectId(client_id)})
    return ClientResponse(**updated_client, id=str(updated_client["_id"]))


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete client"""
    if not ObjectId.is_valid(client_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID"
        )
    
    clients_collection = get_collection(COLLECTIONS["clients"])
    
    # Check if client exists
    existing_client = await clients_collection.find_one({"_id": ObjectId(client_id)})
    if not existing_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Soft delete
    await clients_collection.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Client deleted successfully"} 