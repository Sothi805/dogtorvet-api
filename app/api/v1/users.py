from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

from app.core.deps import get_current_active_user, get_current_admin_user
from app.db.database import database, COLLECTIONS
from app.crud import user_crud
from app.schemas.user import UserDB, UserCreate, UserUpdate, UserResponse
from app.schemas.base import APIResponse


class PasswordUpdate(BaseModel):
    password: str


router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Get all users (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Calculate skip for pagination
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total_count = await user_crud.count(collection)
    
    # Get users with pagination
    users = await user_crud.get_multi(collection, skip=skip, limit=per_page)
    
    users_response = [
        UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            specialization=user.specialization,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            status=user.status
        )
        for user in users
    ]
    
    # Calculate pagination metadata
    total_pages = (total_count + per_page - 1) // per_page
    from_item = skip + 1
    to_item = min(skip + per_page, total_count)
    
    return APIResponse(
        success=True,
        message="Users retrieved successfully",
        data={
            "data": users_response,
            "links": {
                "first": f"/api/v1/users/?page=1&per_page={per_page}",
                "last": f"/api/v1/users/?page={total_pages}&per_page={per_page}",
                "prev": f"/api/v1/users/?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/users/?page={page+1}&per_page={per_page}" if page < total_pages else None
            },
            "meta": {
                "current_page": page,
                "from": from_item,
                "last_page": total_pages,
                "per_page": per_page,
                "to": to_item,
                "total": total_count
            }
        }
    )


@router.post("/", response_model=APIResponse)
async def create_user(
    user_create: UserCreate,
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Create a new user (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Check if email already exists
    if await user_crud.email_exists(collection, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_crud.create(collection, user_create)
    
    return APIResponse(
        success=True,
        message="User created successfully",
        data=UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            specialization=user.specialization,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            status=user.status
        )
    )


@router.get("/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: str,
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Get a specific user (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    user = await user_crud.get(collection, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return APIResponse(
        success=True,
        message="User retrieved successfully",
        data=UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            specialization=user.specialization,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            status=user.status
        )
    )


@router.put("/{user_id}", response_model=APIResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Update a user (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Check if user exists
    existing_user = await user_crud.get(collection, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email already exists for another user
    if user_update.email and user_update.email != existing_user.email:
        if await user_crud.email_exists(collection, user_update.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user
    user = await user_crud.update(collection, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return APIResponse(
        success=True,
        message="User updated successfully",
        data=UserResponse(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            specialization=user.specialization,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            status=user.status
        )
    )


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: str,
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Delete a user (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Check if user exists
    if not await user_crud.exists(collection, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    success = await user_crud.delete(collection, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return APIResponse(
        success=True,
        message="User deleted successfully",
        data=None
    )


@router.put("/{user_id}/password", response_model=APIResponse)
async def update_user_password(
    user_id: str,
    password_update: PasswordUpdate,
    current_user: UserDB = Depends(get_current_admin_user)
):
    """Update user password (Admin only)."""
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Check if user exists
    user = await user_crud.get(collection, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update the password
    await user_crud.update_password(collection, user_id, password_update.password)
    
    return APIResponse(
        success=True,
        message="Password updated successfully",
        data=None
    )