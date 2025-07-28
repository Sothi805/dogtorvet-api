from datetime import datetime, timezone
from typing import Optional, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict, field_serializer
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    """Validate ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Create a type alias for MongoDB ObjectId
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class BaseSchema(BaseModel):
    """Base schema for all models"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        use_enum_values=True
    )


class BaseDBSchema(BaseSchema):
    """Base schema for database models"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: bool = Field(default=True)


class BaseCreateSchema(BaseSchema):
    """Base schema for creating records"""
    status: bool = True


class BaseUpdateSchema(BaseSchema):
    """Base schema for updating records"""
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Optional[bool] = None


class BaseResponseSchema(BaseSchema):
    """Base schema for API responses"""
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        use_enum_values=True
    )
    
    id: str
    created_at: datetime
    updated_at: datetime
    status: bool
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format string"""
        return value.isoformat() if value else None


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
    errors: Optional[list] = None 