from pydantic import Field
from typing import Optional
from decimal import Decimal
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Service(BaseDBModel):
    """Service database model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Service description")
    price: Decimal = Field(..., max_digits=10, decimal_places=2, ge=0, description="Service price")
    duration_minutes: int = Field(default=30, ge=1, description="Service duration in minutes")


class ServiceCreate(BaseCreateModel):
    """Service creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Service description")
    price: float = Field(..., ge=0, description="Service price")
    duration_minutes: Optional[int] = Field(default=30, ge=1, description="Service duration in minutes")


class ServiceUpdate(BaseUpdateModel):
    """Service update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Service description")
    price: Optional[float] = Field(None, ge=0, description="Service price")
    duration_minutes: Optional[int] = Field(None, ge=1, description="Service duration in minutes")


class ServiceResponse(BaseResponseModel):
    """Service response model"""
    name: str
    description: Optional[str]
    price: float
    duration_minutes: int 