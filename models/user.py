from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    VET = "vet"


class User(BaseDBModel):
    """User database model"""
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


class UserCreate(BaseCreateModel):
    """User creation model"""
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=15)
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = Field(default=UserRole.VET)
    specialization: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseUpdateModel):
    """User update model"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    specialization: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseResponseModel):
    """User response model"""
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
    """User login model"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None