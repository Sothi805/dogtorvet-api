from pydantic import Field
from typing import Optional, Dict, Any
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel, PyObjectId


class Breed(BaseDBModel):
    """Breed database model"""
    name: str = Field(..., min_length=1, max_length=255)
    species_id: PyObjectId = Field(..., description="Species ID reference")


class BreedCreate(BaseCreateModel):
    """Breed creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    species_id: str = Field(..., description="Species ID reference")


class BreedUpdate(BaseUpdateModel):
    """Breed update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    species_id: Optional[str] = Field(None, description="Species ID reference")


class BreedResponse(BaseResponseModel):
    """Breed response model"""
    name: str
    species_id: str 
    species: Optional[Dict[str, Any]] = None 