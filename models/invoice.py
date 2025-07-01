from pydantic import Field
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel, PyObjectId


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(BaseDBModel):
    """Invoice database model"""
    invoice_number: str = Field(..., min_length=1, max_length=50, unique=True)
    client_id: PyObjectId = Field(..., description="Client ID reference")
    pet_id: Optional[PyObjectId] = Field(None, description="Pet ID reference")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    subtotal: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    discount_percent: Decimal = Field(default=0, max_digits=5, decimal_places=2, ge=0, le=100)
    total: Decimal = Field(default=0, max_digits=10, decimal_places=2, ge=0)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    notes: Optional[str] = Field(None, description="Invoice notes")


class InvoiceCreate(BaseCreateModel):
    """Invoice creation model"""
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    client_id: str = Field(..., description="Client ID reference")
    pet_id: Optional[str] = Field(None, description="Pet ID reference")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    subtotal: Optional[float] = Field(default=0, ge=0)
    discount_percent: Optional[float] = Field(default=0, ge=0, le=100)
    total: Optional[float] = Field(default=0, ge=0)
    payment_status: Optional[PaymentStatus] = Field(default=PaymentStatus.PENDING)
    notes: Optional[str] = Field(None, description="Invoice notes")


class InvoiceUpdate(BaseUpdateModel):
    """Invoice update model"""
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    client_id: Optional[str] = Field(None, description="Client ID reference")
    pet_id: Optional[str] = Field(None, description="Pet ID reference")
    invoice_date: Optional[date] = Field(None, description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    subtotal: Optional[float] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    total: Optional[float] = Field(None, ge=0)
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = Field(None, description="Invoice notes")


class InvoiceResponse(BaseResponseModel):
    """Invoice response model"""
    invoice_number: str
    client_id: str
    pet_id: Optional[str]
    invoice_date: date
    due_date: Optional[date]
    subtotal: float
    discount_percent: float
    total: float
    payment_status: PaymentStatus
    notes: Optional[str] 