from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.user import User, UserCreate, UserUpdate, UserResponse
from utils.auth import get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/test-no-auth")
async def test_no_auth():
    """Test endpoint without authentication to check if users route works at all"""
    return {"message": "Users route is accessible", "route": "/api/users/test-no-auth"}


@router.get("/", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get all users with Laravel-style pagination"""
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    # Calculate skip and limit
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total = await users_collection.count_documents(query)
    
    # Execute query
    cursor = users_collection.find(query).skip(skip).limit(per_page)
    users_list = []
    
    async for user_doc in cursor:
        # Convert ObjectId to string and handle field mapping
        if "_id" in user_doc:
            user_doc["id"] = str(user_doc["_id"])
            del user_doc["_id"]
        
        # Create the response format that matches frontend expectations
        # Use the ObjectId string as the ID
        object_id_str = user_doc["id"]
        
        user_response_data = {
            "id": object_id_str,
            "name": f"{user_doc.get('first_name', '')} {user_doc.get('last_name', '')}".strip(),
            "email": user_doc.get("email", ""),
            "role": user_doc.get("role", "vet"),
            "status": True,  # Default to active since we don't have status in our model
            "phone": user_doc.get("phone"),
            "specialization": user_doc.get("specialization"),
            "email_verified_at": user_doc.get("email_verified_at").isoformat() if user_doc.get("email_verified_at") else None,
            "created_at": user_doc.get("created_at").isoformat() if user_doc.get("created_at") else None,
            "updated_at": user_doc.get("updated_at").isoformat() if user_doc.get("updated_at") else None
        }
        
        users_list.append(user_response_data)
    
    # Calculate pagination metadata
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": users_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if users_list else None,
            "to": skip + len(users_list) if users_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/users"
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    users_collection = get_collection(COLLECTIONS["users"])
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user_doc, id=str(user_doc["_id"]))


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    result = await users_collection.insert_one(user_dict)
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    
    return UserResponse(**created_user, id=str(created_user["_id"]))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Check if user exists
    existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare update data
    update_data = user_data.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return UserResponse(**updated_user, id=str(updated_user["_id"]))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete user"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Check if user exists
    existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "User deleted successfully"} 