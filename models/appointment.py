from pydantic import Field
from typing import Optional
from datetime import datetime
from enum import Enum
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel, PyObjectId


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(BaseDBModel):
    """Appointment database model"""
    client_id: PyObjectId = Field(..., description="Client ID reference")
    pet_id: PyObjectId = Field(..., description="Pet ID reference")
    service_id: Optional[PyObjectId] = Field(None, description="Service ID reference")
    user_id: Optional[PyObjectId] = Field(None, description="Veterinarian user ID reference")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    duration_minutes: int = Field(default=30, ge=1, description="Appointment duration in minutes")
    appointment_status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    notes: Optional[str] = Field(None, description="Appointment notes")
    diagnosis: Optional[str] = Field(None, description="Diagnosis notes")
    treatment: Optional[str] = Field(None, description="Treatment notes")


class AppointmentCreate(BaseCreateModel):
    """Appointment creation model"""
    client_id: str = Field(..., description="Client ID reference")
    pet_id: str = Field(..., description="Pet ID reference")
    service_id: Optional[str] = Field(None, description="Service ID reference")
    user_id: Optional[str] = Field(None, description="Veterinarian user ID reference")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    duration_minutes: Optional[int] = Field(default=30, ge=1, description="Appointment duration in minutes")
    appointment_status: Optional[AppointmentStatus] = Field(default=AppointmentStatus.SCHEDULED)
    notes: Optional[str] = Field(None, description="Appointment notes")
    diagnosis: Optional[str] = Field(None, description="Diagnosis notes")
    treatment: Optional[str] = Field(None, description="Treatment notes")


class AppointmentUpdate(BaseUpdateModel):
    """Appointment update model"""
    client_id: Optional[str] = Field(None, description="Client ID reference")
    pet_id: Optional[str] = Field(None, description="Pet ID reference")
    service_id: Optional[str] = Field(None, description="Service ID reference")
    user_id: Optional[str] = Field(None, description="Veterinarian user ID reference")
    appointment_date: Optional[datetime] = Field(None, description="Appointment date and time")
    duration_minutes: Optional[int] = Field(None, ge=1, description="Appointment duration in minutes")
    appointment_status: Optional[AppointmentStatus] = None
    notes: Optional[str] = Field(None, description="Appointment notes")
    diagnosis: Optional[str] = Field(None, description="Diagnosis notes")
    treatment: Optional[str] = Field(None, description="Treatment notes")


class AppointmentResponse(BaseResponseModel):
    """Appointment response model"""
    client_id: str
    pet_id: str
    service_id: Optional[str]
    user_id: Optional[str]
    appointment_date: datetime
    duration_minutes: int
    appointment_status: AppointmentStatus
    notes: Optional[str]
    diagnosis: Optional[str]
    treatment: Optional[str] 