from pydantic import Field
from typing import Optional
from decimal import Decimal
from enum import Enum
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel, PyObjectId


class ItemType(str, Enum):
    SERVICE = "service"
    PRODUCT = "product"


class InvoiceItem(BaseDBModel):
    """Invoice Item database model"""
    invoice_id: PyObjectId = Field(..., description="Invoice ID reference")
    item_type: ItemType = Field(..., description="Type of item (service or product)")
    service_id: Optional[PyObjectId] = Field(None, description="Service ID reference")
    product_id: Optional[PyObjectId] = Field(None, description="Product ID reference")
    item_name: str = Field(..., min_length=1, max_length=255, description="Item name for historical purposes")
    item_description: Optional[str] = Field(None, description="Item description")
    unit_price: Decimal = Field(..., max_digits=10, decimal_places=2, ge=0)
    quantity: int = Field(default=1, ge=1)
    discount_percent: Decimal = Field(default=0, max_digits=5, decimal_places=2, ge=0, le=100)
    net_price: Decimal = Field(..., max_digits=10, decimal_places=2, ge=0, description="Final price after discount")


class InvoiceItemCreate(BaseCreateModel):
    """Invoice Item creation model"""
    invoice_id: str = Field(..., description="Invoice ID reference")
    item_type: ItemType = Field(..., description="Type of item (service or product)")
    service_id: Optional[str] = Field(None, description="Service ID reference")
    product_id: Optional[str] = Field(None, description="Product ID reference")
    item_name: str = Field(..., min_length=1, max_length=255, description="Item name for historical purposes")
    item_description: Optional[str] = Field(None, description="Item description")
    unit_price: float = Field(..., ge=0)
    quantity: Optional[int] = Field(default=1, ge=1)
    discount_percent: Optional[float] = Field(default=0, ge=0, le=100)
    net_price: float = Field(..., ge=0, description="Final price after discount")


class InvoiceItemUpdate(BaseUpdateModel):
    """Invoice Item update model"""
    invoice_id: Optional[str] = Field(None, description="Invoice ID reference")
    item_type: Optional[ItemType] = Field(None, description="Type of item (service or product)")
    service_id: Optional[str] = Field(None, description="Service ID reference")
    product_id: Optional[str] = Field(None, description="Product ID reference")
    item_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Item name for historical purposes")
    item_description: Optional[str] = Field(None, description="Item description")
    unit_price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    net_price: Optional[float] = Field(None, ge=0, description="Final price after discount")


class InvoiceItemResponse(BaseResponseModel):
    """Invoice Item response model"""
    invoice_id: str
    item_type: ItemType
    service_id: Optional[str]
    product_id: Optional[str]
    item_name: str
    item_description: Optional[str]
    unit_price: float
    quantity: int
    discount_percent: float
    net_price: float 