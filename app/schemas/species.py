from pydantic import Field
from typing import Optional
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class SpeciesDB(BaseDBSchema):
    """Species database schema"""
    name: str = Field(..., min_length=1, max_length=255, unique=True)
    description: Optional[str] = Field(None, max_length=1000)


class SpeciesCreate(BaseCreateSchema):
    """Species creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class SpeciesUpdate(BaseUpdateSchema):
    """Species update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class SpeciesResponse(BaseResponseSchema):
    """Species response schema"""
    name: str
    description: Optional[str] 