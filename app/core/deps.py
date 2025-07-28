from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security import decode_token
from app.db.database import database, COLLECTIONS
from app.crud import user_crud
from app.schemas.user import UserDB, TokenData


security = HTTPBearer()


def check_database_connection():
    """Check if database is connected and raise error if not."""
    if not database.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserDB:
    """Get current authenticated user."""
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
        
        token_data = TokenData(email=email)
    except Exception:
        raise credentials_exception
    
    # Get user from database
    collection = database.get_collection(COLLECTIONS["users"])
    user = await user_crud.get_by_email(collection, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Get current active user."""
    if not current_user.status:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: UserDB = Depends(get_current_active_user)) -> UserDB:
    """Get current admin user."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Optional auth for public endpoints
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserDB]:
    """Get current user (optional)."""
    if credentials is None or not database.is_connected():
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload is None:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        # Get user from database
        collection = database.get_collection(COLLECTIONS["users"])
        user = await user_crud.get_by_email(collection, email=email)
        return user
    except Exception:
        return None 