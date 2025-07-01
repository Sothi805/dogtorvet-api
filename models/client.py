from pydantic import Field
from typing import Optional
from enum import Enum
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Client(BaseDBModel):
    """Client database model"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Gender = Field(default=Gender.OTHER)
    phone_number: str = Field(..., min_length=1, max_length=15, unique=True)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientCreate(BaseCreateModel):
    """Client creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[Gender] = Field(default=Gender.OTHER)
    phone_number: str = Field(..., min_length=1, max_length=15)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientUpdate(BaseUpdateModel):
    """Client update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[Gender] = None
    phone_number: Optional[str] = Field(None, min_length=1, max_length=15)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientResponse(BaseResponseModel):
    """Client response model"""
    name: str
    gender: Gender
    phone_number: str
    other_contact_info: Optional[str] 