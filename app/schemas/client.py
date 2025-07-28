from pydantic import Field
from typing import Optional
from enum import Enum
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class Gender(str, Enum):
    """Gender enumeration"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ClientDB(BaseDBSchema):
    """Client database schema"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Gender = Field(default=Gender.OTHER)
    phone_number: str = Field(..., min_length=1, max_length=15, unique=True)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientCreate(BaseCreateSchema):
    """Client creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    gender: Optional[Gender] = Field(default=Gender.OTHER)
    phone_number: str = Field(..., min_length=1, max_length=15)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientUpdate(BaseUpdateSchema):
    """Client update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[Gender] = None
    phone_number: Optional[str] = Field(None, min_length=1, max_length=15)
    other_contact_info: Optional[str] = Field(None, max_length=255)


class ClientResponse(BaseResponseSchema):
    """Client response schema"""
    name: str
    gender: Gender
    phone_number: str
    other_contact_info: Optional[str] 