from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import client_crud
from app.schemas.client import ClientDB, ClientCreate, ClientUpdate, ClientResponse
from app.schemas.user import UserDB
from app.schemas.base import APIResponse


router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get all clients."""
    collection = database.get_collection(COLLECTIONS["clients"])
    clients = await client_crud.get_multi(collection, skip=skip, limit=limit)
    
    clients_response = [
        ClientResponse(
            id=str(client.id),
            name=client.name,
            gender=client.gender,
            phone_number=client.phone_number,
            other_contact_info=client.other_contact_info,
            created_at=client.created_at,
            updated_at=client.updated_at,
            status=client.status
        )
        for client in clients
    ]
    
    return APIResponse(
        success=True,
        message="Clients retrieved successfully",
        data=clients_response
    )


@router.post("/", response_model=APIResponse)
async def create_client(
    client_create: ClientCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Create a new client."""
    collection = database.get_collection(COLLECTIONS["clients"])
    
    # Check if phone number already exists
    if await client_crud.phone_exists(collection, client_create.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create client
    client = await client_crud.create(collection, client_create)
    
    return APIResponse(
        success=True,
        message="Client created successfully",
        data=ClientResponse(
            id=str(client.id),
            name=client.name,
            gender=client.gender,
            phone_number=client.phone_number,
            other_contact_info=client.other_contact_info,
            created_at=client.created_at,
            updated_at=client.updated_at,
            status=client.status
        )
    )


@router.get("/{client_id}", response_model=APIResponse)
async def get_client(
    client_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get a specific client."""
    collection = database.get_collection(COLLECTIONS["clients"])
    client = await client_crud.get(collection, client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return APIResponse(
        success=True,
        message="Client retrieved successfully",
        data=ClientResponse(
            id=str(client.id),
            name=client.name,
            gender=client.gender,
            phone_number=client.phone_number,
            other_contact_info=client.other_contact_info,
            created_at=client.created_at,
            updated_at=client.updated_at,
            status=client.status
        )
    )


@router.put("/{client_id}", response_model=APIResponse)
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Update a client."""
    collection = database.get_collection(COLLECTIONS["clients"])
    
    # Check if client exists
    existing_client = await client_crud.get(collection, client_id)
    if not existing_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check if phone number already exists for another client
    if client_update.phone_number and client_update.phone_number != existing_client.phone_number:
        if await client_crud.phone_exists(collection, client_update.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Update client
    client = await client_crud.update(collection, client_id, client_update)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return APIResponse(
        success=True,
        message="Client updated successfully",
        data=ClientResponse(
            id=str(client.id),
            name=client.name,
            gender=client.gender,
            phone_number=client.phone_number,
            other_contact_info=client.other_contact_info,
            created_at=client.created_at,
            updated_at=client.updated_at,
            status=client.status
        )
    )


@router.delete("/{client_id}", response_model=APIResponse)
async def delete_client(
    client_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Delete a client."""
    collection = database.get_collection(COLLECTIONS["clients"])
    
    # Check if client exists
    if not await client_crud.exists(collection, client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Delete client
    success = await client_crud.delete(collection, client_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return APIResponse(
        success=True,
        message="Client deleted successfully",
        data=None
    ) 