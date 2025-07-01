from pydantic import Field
from typing import Optional
from datetime import date
from enum import Enum
from decimal import Decimal
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel, PyObjectId


class PetGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Pet(BaseDBModel):
    """Pet database model"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: PetGender = Field(default=PetGender.MALE)
    dob: date = Field(..., description="Date of birth")
    species_id: PyObjectId = Field(..., description="Species ID reference")
    breed_id: PyObjectId = Field(..., description="Breed ID reference")
    weight: Decimal = Field(..., max_digits=5, decimal_places=2, description="Weight in kg")
    color: str = Field(..., min_length=1, max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: PyObjectId = Field(..., description="Client ID reference")


class PetCreate(BaseCreateModel):
    """Pet creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[PetGender] = Field(default=PetGender.MALE)
    dob: date = Field(..., description="Date of birth")
    species_id: str = Field(..., description="Species ID reference")
    breed_id: str = Field(..., description="Breed ID reference")
    weight: float = Field(..., gt=0, description="Weight in kg")
    color: str = Field(..., min_length=1, max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: str = Field(..., description="Client ID reference")


class PetUpdate(BaseUpdateModel):
    """Pet update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[PetGender] = None
    dob: Optional[date] = Field(None, description="Date of birth")
    species_id: Optional[str] = Field(None, description="Species ID reference")
    breed_id: Optional[str] = Field(None, description="Breed ID reference")
    weight: Optional[float] = Field(None, gt=0, description="Weight in kg")
    color: Optional[str] = Field(None, min_length=1, max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: Optional[str] = Field(None, description="Client ID reference")
    status: Optional[bool] = Field(None, description="Pet active status")


class PetResponse(BaseResponseModel):
    """Pet response model"""
    name: str
    gender: PetGender
    dob: date
    species_id: str
    breed_id: str
    weight: float
    color: str
    medical_history: Optional[str]
    client_id: str 