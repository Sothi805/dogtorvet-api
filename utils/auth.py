from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId

from config import settings
from database import get_collection, COLLECTIONS
from models.user import User, UserRole

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple, working authentication"""
    print(f"🔐 Auth: Processing token: {credentials.credentials[:50]}...")
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
            
        print(f"🔐 Auth: Valid token for {email}")
            
    except JWTError as e:
        print(f"❌ Auth: JWT error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    # Get user from database
    users_collection = get_collection(COLLECTIONS["users"])
    user_doc = await users_collection.find_one({"email": email})
    
    if user_doc is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Simple conversion
    if "_id" in user_doc:
        user_doc["id"] = str(user_doc["_id"])
        del user_doc["_id"]
        
    # Set defaults
    user_doc.setdefault("first_name", "Unknown")
    user_doc.setdefault("last_name", "User")
    user_doc.setdefault("phone", None)
    user_doc.setdefault("specialization", None)
    user_doc.setdefault("email_verified_at", None)
    user_doc.setdefault("remember_token", None)
    
    # Role conversion
    role_str = user_doc.get("role", "vet")
    user_doc["role"] = UserRole.ADMIN if role_str == "admin" else UserRole.VET
    
    user = User(**user_doc)
    print(f"✅ Auth: Success for {user.email}, role: {user.role}")
    return user


async def authenticate_user(email: str, password: str):
    """Simple user authentication"""
    try:
        users_collection = get_collection(COLLECTIONS["users"])
        user_doc = await users_collection.find_one({"email": email})
        
        if not user_doc:
            return False
        
        if "_id" in user_doc:
            user_doc["id"] = str(user_doc["_id"])
            del user_doc["_id"]
            
        user_doc.setdefault("first_name", "Unknown")
        user_doc.setdefault("last_name", "User")
        user_doc.setdefault("phone", None)
        user_doc.setdefault("specialization", None)
        user_doc.setdefault("email_verified_at", None)
        user_doc.setdefault("remember_token", None)
        
        role_str = user_doc.get("role", "vet")
        user_doc["role"] = UserRole.ADMIN if role_str == "admin" else UserRole.VET
            
        user = User(**user_doc)
        return user if verify_password(password, user.password) else False
    except Exception as e:
        print(f"Authentication error: {e}")
        return False


# SIMPLIFIED DEPENDENCY - NO ROLE CHECKING BY DEFAULT
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user - SIMPLIFIED, NO ROLE RESTRICTIONS"""
    print(f"✅ Auth: Active user check passed for {current_user.email}")
    return current_user


# OPTIONAL: Role-based dependency (only use when needed)
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role - USE ONLY WHEN NEEDED"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user 