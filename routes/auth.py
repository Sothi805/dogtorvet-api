from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from bson import ObjectId
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_collection, COLLECTIONS
from models.user import User, UserCreate, UserLogin, UserResponse, Token
from utils.auth import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token, 
    get_password_hash,
    security,
    get_current_user
)
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate):
    """Register a new user"""
    users_collection = get_collection(COLLECTIONS["users"])
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone number already exists (if provided)
    if user_data.phone:
        existing_phone = await users_collection.find_one({"phone": user_data.phone})
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    # Insert user
    result = await users_collection.insert_one(user_dict)
    
    # Retrieve created user
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    return UserResponse(**created_user, id=str(created_user["_id"]))


@router.post("/login", response_model=dict)
@limiter.limit("10/minute")
async def login(request: Request, user_credentials: UserLogin):
    """Authenticate user and return tokens"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    
    return {
        "status": "success",
        "message": "Login successful",
        "data": {
            "token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token using refresh token"""
    from jose import JWTError, jwt
    from config import settings
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Verify user still exists
    users_collection = get_collection(COLLECTIONS["users"])
    user_doc = await users_collection.find_one({"email": email})
    
    if user_doc is None:
        raise credentials_exception
    
    # Create new tokens
    access_token = create_access_token(data={"sub": email})
    refresh_token = create_refresh_token(data={"sub": email})
    
    return {
        "status": "success",
        "data": {
            "token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "status": "success",
        "data": {
            "id": str(current_user.id),
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "name": f"{current_user.first_name} {current_user.last_name}",
            "email": current_user.email,
            "role": current_user.role,
            "phone": current_user.phone,
            "specialization": current_user.specialization,
            "email_verified_at": current_user.email_verified_at.isoformat() if current_user.email_verified_at else None
        }
    }


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)"""
    return {
        "status": "success",
        "message": "Successfully logged out"
    }


@router.get("/test-auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    """Test endpoint to debug authentication without role checking"""
    return {
        "status": "success",
        "message": "Authentication working",
        "user": {
            "email": current_user.email,
            "role": current_user.role,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name
        }
    } 