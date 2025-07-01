from pydantic import Field
from typing import Optional
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Allergy(BaseDBModel):
    """Allergy database model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Allergy description")


class AllergyCreate(BaseCreateModel):
    """Allergy creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Allergy description")


class AllergyUpdate(BaseUpdateModel):
    """Allergy update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Allergy description")


class AllergyResponse(BaseResponseModel):
    """Allergy response model"""
    name: str
    description: Optional[str] 