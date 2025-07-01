from pydantic import Field
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Species(BaseDBModel):
    """Species database model"""
    name: str = Field(..., min_length=1, max_length=255)


class SpeciesCreate(BaseCreateModel):
    """Species creation model"""
    name: str = Field(..., min_length=1, max_length=255)


class SpeciesUpdate(BaseUpdateModel):
    """Species update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class SpeciesResponse(BaseResponseModel):
    """Species response model"""
    name: str 