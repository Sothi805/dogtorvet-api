from pydantic import Field
from typing import Optional
from decimal import Decimal
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class ServiceDB(BaseDBSchema):
    """Service database schema"""
    name: str = Field(..., min_length=1, max_length=255, unique=True)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0, description="Service price")
    duration: int = Field(default=60, description="Duration in minutes")
    category: Optional[str] = Field(None, max_length=100, description="Service category")
    service_type: str = Field(..., description="Type of service (consultation, vaccination, surgery, etc.)")


class ServiceCreate(BaseCreateSchema):
    """Service creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0, description="Service price")
    duration: int = Field(default=60, description="Duration in minutes")
    category: Optional[str] = Field(None, max_length=100, description="Service category")
    service_type: str = Field(..., description="Type of service (consultation, vaccination, surgery, etc.)")


class ServiceUpdate(BaseUpdateSchema):
    """Service update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, gt=0, description="Service price")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    category: Optional[str] = Field(None, max_length=100, description="Service category")
    service_type: Optional[str] = Field(None, description="Type of service (consultation, vaccination, surgery, etc.)")


class ServiceResponse(BaseResponseSchema):
    """Service response schema"""
    name: str
    description: Optional[str]
    price: Decimal
    duration: int
    category: Optional[str]
    service_type: str 