from pydantic import Field
from typing import Optional
from datetime import date
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class VaccinationDB(BaseDBSchema):
    """Vaccination database schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    vaccine_name: str = Field(..., min_length=1, max_length=255, description="Vaccine name")
    vaccine_brand: Optional[str] = Field(None, max_length=255, description="Vaccine brand")
    vaccination_date: date = Field(..., description="Vaccination date")
    next_due_date: Optional[date] = Field(None, description="Next vaccination due date")
    vet_id: str = Field(..., description="Veterinarian ID reference")
    batch_number: Optional[str] = Field(None, max_length=100, description="Vaccine batch number")
    notes: Optional[str] = Field(None, max_length=1000, description="Vaccination notes")


class VaccinationCreate(BaseCreateSchema):
    """Vaccination creation schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    vaccine_name: str = Field(..., min_length=1, max_length=255, description="Vaccine name")
    vaccine_brand: Optional[str] = Field(None, max_length=255, description="Vaccine brand")
    vaccination_date: date = Field(..., description="Vaccination date")
    next_due_date: Optional[date] = Field(None, description="Next vaccination due date")
    vet_id: str = Field(..., description="Veterinarian ID reference")
    batch_number: Optional[str] = Field(None, max_length=100, description="Vaccine batch number")
    notes: Optional[str] = Field(None, max_length=1000, description="Vaccination notes")


class VaccinationUpdate(BaseUpdateSchema):
    """Vaccination update schema"""
    vaccine_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Vaccine name")
    vaccine_brand: Optional[str] = Field(None, max_length=255, description="Vaccine brand")
    vaccination_date: Optional[date] = Field(None, description="Vaccination date")
    next_due_date: Optional[date] = Field(None, description="Next vaccination due date")
    batch_number: Optional[str] = Field(None, max_length=100, description="Vaccine batch number")
    notes: Optional[str] = Field(None, max_length=1000, description="Vaccination notes")


class VaccinationResponse(BaseResponseSchema):
    """Vaccination response schema"""
    pet_id: str
    vaccine_name: str
    vaccine_brand: Optional[str]
    vaccination_date: date
    next_due_date: Optional[date]
    vet_id: str
    batch_number: Optional[str]
    notes: Optional[str] 