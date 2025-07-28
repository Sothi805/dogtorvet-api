from pydantic import Field
from typing import Optional
from enum import Enum
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class AllergySeverity(str, Enum):
    """Allergy severity enumeration"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class AllergyDB(BaseDBSchema):
    """Allergy database schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    allergen: str = Field(..., min_length=1, max_length=255, description="Allergen name")
    severity: AllergySeverity = Field(default=AllergySeverity.MILD, description="Allergy severity")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Allergy symptoms")
    treatment: Optional[str] = Field(None, max_length=1000, description="Treatment notes")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class AllergyCreate(BaseCreateSchema):
    """Allergy creation schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    allergen: str = Field(..., min_length=1, max_length=255, description="Allergen name")
    severity: Optional[AllergySeverity] = Field(default=AllergySeverity.MILD, description="Allergy severity")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Allergy symptoms")
    treatment: Optional[str] = Field(None, max_length=1000, description="Treatment notes")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class AllergyUpdate(BaseUpdateSchema):
    """Allergy update schema"""
    allergen: Optional[str] = Field(None, min_length=1, max_length=255, description="Allergen name")
    severity: Optional[AllergySeverity] = Field(None, description="Allergy severity")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Allergy symptoms")
    treatment: Optional[str] = Field(None, max_length=1000, description="Treatment notes")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class AllergyResponse(BaseResponseSchema):
    """Allergy response schema"""
    pet_id: str
    allergen: str
    severity: AllergySeverity
    symptoms: Optional[str]
    treatment: Optional[str]
    notes: Optional[str] 