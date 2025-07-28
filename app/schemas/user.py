from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    VET = "vet"


class UserDB(BaseDBSchema):
    """User database schema"""
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., unique=True)
    phone: Optional[str] = Field(None, max_length=15)
    email_verified_at: Optional[datetime] = None
    password: str = Field(..., min_length=6)
    role: UserRole = Field(default=UserRole.VET)
    specialization: Optional[str] = Field(None, max_length=255)
    remember_token: Optional[str] = None

    @property
    def name(self) -> str:
        """Computed full name property"""
        return f"{self.first_name} {self.last_name}"


class UserCreate(BaseCreateSchema):
    """User creation schema"""
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=15)
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = Field(default=UserRole.VET)
    specialization: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseUpdateSchema):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    specialization: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseResponseSchema):
    """User response schema"""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    specialization: Optional[str]
    email_verified_at: Optional[datetime]
    
    @property
    def name(self) -> str:
        """Computed full name property"""
        return f"{self.first_name} {self.last_name}"


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema"""
    email: Optional[str] = None
    user_id: Optional[str] = None 