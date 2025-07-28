from pydantic import Field
from typing import Optional
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class VaccinationTypeDB(BaseDBSchema):
    """Vaccination type database schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Vaccination type name")
    description: Optional[str] = Field(None, max_length=1000, description="Vaccination type description")
    duration_months: int = Field(..., ge=1, le=60, description="Duration in months")


class VaccinationTypeCreate(BaseCreateSchema):
    """Vaccination type creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Vaccination type name")
    description: Optional[str] = Field(None, max_length=1000, description="Vaccination type description")
    duration_months: int = Field(..., ge=1, le=60, description="Duration in months")


class VaccinationTypeUpdate(BaseUpdateSchema):
    """Vaccination type update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Vaccination type name")
    description: Optional[str] = Field(None, max_length=1000, description="Vaccination type description")
    duration_months: Optional[int] = Field(None, ge=1, le=60, description="Duration in months")


class VaccinationTypeResponse(BaseResponseSchema):
    """Vaccination type response schema"""
    name: str
    description: Optional[str]
    duration_months: int 