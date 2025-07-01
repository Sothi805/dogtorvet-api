"""
Audit Log Model
Tracks hard deletions and other critical actions
"""
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from .base import BaseDBModel, PyObjectId


class AuditAction(str, Enum):
    HARD_DELETE = "hard_delete"
    DATA_EXPORT = "data_export"
    PERMISSION_CHANGE = "permission_change"
    BULK_UPDATE = "bulk_update"
    SYSTEM_CONFIG_CHANGE = "system_config_change"


class AuditLog(BaseDBModel):
    """Audit log database model for tracking critical actions"""
    action: AuditAction = Field(..., description="Type of action performed")
    collection_name: str = Field(..., description="MongoDB collection affected")
    document_id: PyObjectId = Field(..., description="ID of the document affected")
    document_snapshot: Dict[str, Any] = Field(..., description="Full snapshot of document before deletion")
    user_id: PyObjectId = Field(..., description="ID of user who performed the action")
    user_email: str = Field(..., description="Email of user who performed the action")
    user_role: str = Field(..., description="Role of user who performed the action")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")
    reason: Optional[str] = Field(None, description="Reason for the action (if provided)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "hard_delete",
                "collection_name": "clients",
                "document_id": "507f1f77bcf86cd799439011",
                "document_snapshot": {
                    "_id": "507f1f77bcf86cd799439011",
                    "name": "John Doe",
                    "phone_number": "555-0123",
                    "created_at": "2023-01-01T00:00:00Z"
                },
                "user_id": "507f1f77bcf86cd799439012",
                "user_email": "admin@dogtorvet.com",
                "user_role": "admin",
                "ip_address": "192.168.1.1",
                "reason": "Client requested data deletion",
                "created_at": "2023-01-02T00:00:00Z"
            }
        } 