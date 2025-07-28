from pydantic import Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentDB(BaseDBSchema):
    """Appointment database schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    client_id: str = Field(..., description="Client ID reference")
    veterinarian_id: str = Field(..., description="Veterinarian ID reference")
    service_id: str = Field(..., description="Service ID reference")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    duration_minutes: int = Field(default=30, description="Duration in minutes")
    appointment_status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    diagnosis: Optional[str] = Field(None, max_length=1000, description="Diagnosis notes")
    treatment: Optional[str] = Field(None, max_length=1000, description="Treatment notes")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up appointment date")


class AppointmentCreate(BaseCreateSchema):
    """Appointment creation schema"""
    pet_id: str = Field(..., description="Pet ID reference")
    client_id: str = Field(..., description="Client ID reference")
    veterinarian_id: str = Field(..., description="Veterinarian ID reference")
    service_id: str = Field(..., description="Service ID reference")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    duration_minutes: int = Field(default=30, description="Duration in minutes")
    appointment_status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class AppointmentUpdate(BaseUpdateSchema):
    """Appointment update schema"""
    appointment_date: Optional[datetime] = Field(None, description="Appointment date and time")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    appointment_status: Optional[AppointmentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    diagnosis: Optional[str] = Field(None, max_length=1000, description="Diagnosis notes")
    treatment: Optional[str] = Field(None, max_length=1000, description="Treatment notes")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up appointment date")


class AppointmentResponse(BaseResponseSchema):
    """Appointment response schema"""
    pet_id: str
    client_id: str
    veterinarian_id: str
    service_id: str
    appointment_date: datetime
    duration_minutes: int
    appointment_status: AppointmentStatus
    notes: Optional[str]
    diagnosis: Optional[str]
    treatment: Optional[str]
    follow_up_date: Optional[datetime] 