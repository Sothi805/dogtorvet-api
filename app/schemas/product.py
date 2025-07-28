from pydantic import Field
from typing import Optional
from decimal import Decimal
from .base import BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class ProductDB(BaseDBSchema):
    """Product database schema"""
    name: str = Field(..., min_length=1, max_length=255, unique=True)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0, description="Product price")
    stock_quantity: int = Field(default=0, ge=0, description="Stock quantity")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, max_length=50, description="Stock keeping unit")


class ProductCreate(BaseCreateSchema):
    """Product creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0, description="Product price")
    stock_quantity: int = Field(default=0, ge=0, description="Stock quantity")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, max_length=50, description="Stock keeping unit")


class ProductUpdate(BaseUpdateSchema):
    """Product update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, max_length=50, description="Stock keeping unit")


class ProductResponse(BaseResponseSchema):
    """Product response schema"""
    name: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    category: Optional[str]
    sku: Optional[str] 