from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import security, get_current_active_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.database import database, COLLECTIONS
from app.crud import user_crud
from app.schemas.user import UserLogin, Token, UserResponse
from app.schemas.base import APIResponse


router = APIRouter()


def check_database_connection():
    """Check if database is connected and raise error if not."""
    if not database.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )


@router.post("/login", response_model=APIResponse)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT tokens."""
    check_database_connection()
    
    collection = database.get_collection(COLLECTIONS["users"])
    
    # Authenticate user
    user = await user_crud.authenticate(
        collection, 
        email=user_credentials.email, 
        password=user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return APIResponse(
        success=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse(
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
        }
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh JWT token."""
    check_database_connection()
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from database
    collection = database.get_collection(COLLECTIONS["users"])
    user = await user_crud.get_by_email(collection, email=email)
    if user is None:
        raise credentials_exception
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return APIResponse(
        success=True,
        message="Token refreshed successfully",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user information."""
    return APIResponse(
        success=True,
        message="User information retrieved successfully",
        data=UserResponse(
            id=str(current_user.id),
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            email=current_user.email,
            phone=current_user.phone,
            role=current_user.role,
            specialization=current_user.specialization,
            email_verified_at=current_user.email_verified_at,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            status=current_user.status
        )
    )


@router.post("/logout", response_model=APIResponse)
async def logout(current_user: UserResponse = Depends(get_current_active_user)):
    """Logout user (client-side token removal)."""
    return APIResponse(
        success=True,
        message="Logout successful",
        data=None
    ) 