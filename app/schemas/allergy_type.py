from pydantic import Field
from typing import Optional
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class AllergyTypeDB(BaseDBSchema):
    """Allergy type database schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Allergy type name")
    description: Optional[str] = Field(None, max_length=1000, description="Allergy type description")


class AllergyTypeCreate(BaseCreateSchema):
    """Allergy type creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Allergy type name")
    description: Optional[str] = Field(None, max_length=1000, description="Allergy type description")


class AllergyTypeUpdate(BaseUpdateSchema):
    """Allergy type update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Allergy type name")
    description: Optional[str] = Field(None, max_length=1000, description="Allergy type description")


class AllergyTypeResponse(BaseResponseSchema):
    """Allergy type response schema"""
    name: str
    description: Optional[str] 