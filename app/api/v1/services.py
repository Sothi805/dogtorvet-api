from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import service_crud
from app.schemas.service import ServiceDB, ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.user import UserDB
from app.schemas.base import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_services(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["services"])
    filters = {}
    if status and status != "all":
        if status == "active":
            filters["status"] = True
        elif status == "inactive":
            filters["status"] = False
    services = await service_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
    services_response = [
        ServiceResponse(
            id=str(service.id),
            name=service.name,
            description=service.description,
            price=service.price,
            duration=service.duration,
            category=service.category,
            service_type=service.service_type,
            status=service.status,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
        for service in services
    ]
    return APIResponse(success=True, message="Services retrieved successfully", data=services_response)

@router.post("/", response_model=APIResponse)
async def create_service(
    service_create: ServiceCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["services"])
    # Check if service name already exists
    if await service_crud.name_exists(collection, service_create.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service name already exists")
    service = await service_crud.create(collection, service_create)
    return APIResponse(success=True, message="Service created successfully", data=ServiceResponse(
        id=str(service.id),
        name=service.name,
        description=service.description,
        price=service.price,
        duration=service.duration,
        category=service.category,
        service_type=service.service_type,
        status=service.status,
        created_at=service.created_at,
        updated_at=service.updated_at
    ))

@router.delete("/{service_id}", response_model=APIResponse)
async def delete_service(
    service_id: str = Path(..., description="The ID of the service to delete"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["services"])
    
    # Check if service exists
    service = await service_crud.get(collection, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    # Soft delete the service
    success = await service_crud.delete(collection, service_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete service")
    
    return APIResponse(success=True, message="Service deleted successfully") 

@router.patch("/{service_id}/status", response_model=APIResponse)
async def update_service_status(
    service_id: str = Path(..., description="The ID of the service to update status for"),
    status_value: bool = Body(..., embed=True, description="The new status value (true=active, false=inactive)"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["services"])
    service = await service_crud.get(collection, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    update_result = await service_crud.update(collection, service_id, {"status": status_value})
    if not update_result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update service status")
    return APIResponse(success=True, message="Service status updated successfully") 

@router.put("/{service_id}", response_model=APIResponse)
async def update_service(
    service_id: str,
    service_update: ServiceUpdate,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["services"])
    service = await service_crud.get(collection, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    updated_service = await service_crud.update(collection, service_id, service_update)
    if not updated_service:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update service")
    return APIResponse(success=True, message="Service updated successfully", data=ServiceResponse(
        id=str(updated_service.id),
        name=updated_service.name,
        description=updated_service.description,
        price=updated_service.price,
        duration=updated_service.duration,
        category=updated_service.category,
        service_type=updated_service.service_type,
        status=updated_service.status,
        created_at=updated_service.created_at,
        updated_at=updated_service.updated_at
    )) 