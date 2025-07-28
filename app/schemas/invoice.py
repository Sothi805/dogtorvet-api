from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pydantic import field_validator

class InvoiceItemBase(BaseModel):
    item_type: str  # 'service' or 'product'
    item_name: str
    item_description: Optional[str] = None
    unit_price: float
    quantity: int
    discount_percent: float = 0.0
    net_price: float
    # Historical snapshot fields - preserve original data
    service_id: Optional[str] = None
    product_id: Optional[str] = None
    # Snapshot of original service/product data at time of creation
    original_service_data: Optional[dict] = None  # Snapshot of service when added
    original_product_data: Optional[dict] = None   # Snapshot of product when added

class InvoiceItemCreate(InvoiceItemBase):
    invoice_id: str

class InvoiceItemUpdate(BaseModel):
    item_type: Optional[str] = None
    item_name: Optional[str] = None
    item_description: Optional[str] = None
    unit_price: Optional[float] = None
    quantity: Optional[int] = None
    discount_percent: Optional[float] = None
    net_price: Optional[float] = None
    service_id: Optional[str] = None
    product_id: Optional[str] = None

class InvoiceItemDB(InvoiceItemBase):
    id: str
    invoice_id: str
    service: Optional[dict] = None
    product: Optional[dict] = None

class InvoiceBase(BaseModel):
    invoice_number: str
    client_id: str
    pet_id: Optional[str] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    subtotal: float
    discount_percent: float = 0.0
    total: float
    deposit: float = 0.0
    # Remove payment_status since we calculate it dynamically now
    notes: Optional[str] = None
    status: bool = True

class InvoiceCreate(BaseModel):
    client_id: str
    pet_id: Optional[str] = None
    invoice_date: str  # Accept string from frontend
    due_date: Optional[str] = None  # Accept string from frontend
    discount_percent: float = 0.0
    deposit: float = 0.0
    # Remove payment_status since we calculate it dynamically
    notes: Optional[str] = None
    status: bool = True
    items: Optional[List[InvoiceItemCreate]] = []

    @field_validator('invoice_date')
    @classmethod
    def validate_invoice_date(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    client_id: Optional[str] = None
    pet_id: Optional[str] = None
    invoice_date: Optional[str] = None  # Accept string from frontend
    due_date: Optional[str] = None  # Accept string from frontend
    subtotal: Optional[float] = None
    discount_percent: Optional[float] = None
    total: Optional[float] = None
    deposit: Optional[float] = None
    # Remove payment_status since we calculate it dynamically
    notes: Optional[str] = None
    status: Optional[bool] = None
    items: Optional[List[InvoiceItemUpdate]] = None

    @field_validator('invoice_date')
    @classmethod
    def validate_invoice_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

class InvoiceDB(InvoiceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    items: Optional[List[InvoiceItemDB]] = [] 