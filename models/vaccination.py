from pydantic import Field
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Vaccination(BaseDBModel):
    """Vaccination database model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Vaccination description")
    duration_months: int = Field(default=12, ge=1, description="How long this vaccination lasts in months")


class VaccinationCreate(BaseCreateModel):
    """Vaccination creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Vaccination description")
    duration_months: Optional[int] = Field(default=12, ge=1, description="How long this vaccination lasts in months")


class VaccinationUpdate(BaseUpdateModel):
    """Vaccination update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Vaccination description")
    duration_months: Optional[int] = Field(None, ge=1, description="How long this vaccination lasts in months")


class VaccinationResponse(BaseResponseModel):
    """Vaccination response model"""
    name: str
    description: Optional[str]
    duration_months: int 