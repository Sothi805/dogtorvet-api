from pydantic import Field, field_serializer
from typing import Optional
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema, PyObjectId


class BreedDB(BaseDBSchema):
    """Breed database schema"""
    name: str = Field(..., min_length=1, max_length=255)
    species_id: PyObjectId = Field(..., description="Species ID reference")


class BreedCreate(BaseCreateSchema):
    """Breed creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    species_id: str = Field(..., description="Species ID reference")


class BreedUpdate(BaseUpdateSchema):
    """Breed update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    species_id: Optional[str] = Field(None, description="Species ID reference")


class BreedResponse(BaseResponseSchema):
    """Breed response schema"""
    name: str
    species_id: str
    
    @field_serializer('species_id')
    def serialize_species_id(self, value: PyObjectId) -> str:
        """Serialize ObjectId to string"""
        return str(value) if value else None