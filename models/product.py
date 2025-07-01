from pydantic import Field
from typing import Optional
from decimal import Decimal
from .base import BaseDBModel, BaseCreateModel, BaseUpdateModel, BaseResponseModel


class Product(BaseDBModel):
    """Product database model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., max_digits=10, decimal_places=2, ge=0, description="Product price")
    stock_quantity: int = Field(default=0, ge=0, description="Stock quantity")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")


class ProductCreate(BaseCreateModel):
    """Product creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Product price")
    stock_quantity: Optional[int] = Field(default=0, ge=0, description="Stock quantity")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")


class ProductUpdate(BaseUpdateModel):
    """Product update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, ge=0, description="Product price")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")


class ProductResponse(BaseResponseModel):
    """Product response model"""
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    sku: Optional[str] 