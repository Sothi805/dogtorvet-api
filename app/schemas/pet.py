from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
from app.schemas.base import PyObjectId
from pydantic import field_serializer
from app.schemas.client import ClientResponse
from app.schemas.breed import BreedResponse
from app.schemas.species import SpeciesResponse


class PetGender(str, Enum):
    """Pet gender enumeration"""
    MALE = "male"
    FEMALE = "female"


class AllergyResponse(BaseResponseSchema):
    """Allergy response schema for pet allergies"""
    name: str
    description: Optional[str] = None
    status: bool = True


class VaccinationResponse(BaseResponseSchema):
    """Vaccination response schema for pet vaccinations"""
    name: str
    description: Optional[str] = None
    vaccination_date: Optional[str] = None
    next_due_date: Optional[str] = None
    status: bool = True


class PetDB(BaseDBSchema):
    """Pet database schema"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: PetGender = Field(default=PetGender.MALE)
    dob: date = Field(..., description="Date of birth")
    species_id: PyObjectId = Field(..., description="Species ID reference")
    breed_id: Optional[PyObjectId] = Field(None, description="Breed ID reference")
    weight: float = Field(..., gt=0, description="Weight in kg")
    color: Optional[str] = Field(None, description="Pet color", max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: PyObjectId = Field(..., description="Client ID reference")
    sterilized: Optional[bool] = Field(False, description="Whether the pet is sterilized")
    allergies: Optional[List[str]] = Field(default=[], description="List of allergy IDs")
    vaccinations: Optional[List[Dict[str, Any]]] = Field(default=[], description="List of vaccination records")


class PetCreate(BaseCreateSchema):
    """Pet creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[PetGender] = Field(default=PetGender.MALE)
    dob: date = Field(..., description="Date of birth")
    species_id: str = Field(..., description="Species ID reference")
    breed_id: Optional[str] = Field(None, description="Breed ID reference")
    weight: float = Field(..., gt=0, description="Weight in kg")
    color: Optional[str] = Field(None, description="Pet color", max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: str = Field(..., description="Client ID reference")
    sterilized: Optional[bool] = Field(False, description="Whether the pet is sterilized")
    allergies: Optional[List[str]] = Field(default=[], description="List of allergy IDs")
    vaccinations: Optional[List[Dict[str, Any]]] = Field(default=[], description="List of vaccination records")


class PetUpdate(BaseUpdateSchema):
    """Pet update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[PetGender] = None
    dob: Optional[date] = Field(None, description="Date of birth")
    species_id: Optional[str] = Field(None, description="Species ID reference")
    breed_id: Optional[str] = Field(None, description="Breed ID reference")
    weight: Optional[float] = Field(None, gt=0, description="Weight in kg")
    color: Optional[str] = Field(None, max_length=50)
    medical_history: Optional[str] = Field(None, description="Medical history notes")
    client_id: Optional[str] = Field(None, description="Client ID reference")
    sterilized: Optional[bool] = Field(None, description="Whether the pet is sterilized")
    allergies: Optional[List[str]] = Field(None, description="List of allergy IDs")
    vaccinations: Optional[List[Dict[str, Any]]] = Field(None, description="List of vaccination records")


class PetResponse(BaseResponseSchema):
    """Pet response schema"""
    name: str
    gender: PetGender
    dob: date
    species_id: str
    breed_id: Optional[str]
    weight: float
    color: Optional[str]
    medical_history: Optional[str]
    client_id: str
    sterilized: Optional[bool]
    allergies: Optional[List[AllergyResponse]] = []
    vaccinations: Optional[List[VaccinationResponse]] = []
    client: Optional[ClientResponse] = None
    species: Optional[SpeciesResponse] = None
    breed: Optional[BreedResponse] = None

    @field_serializer('id', 'species_id', 'breed_id', 'client_id')
    def serialize_objectid(self, value):
        return str(value) if value is not None else None 