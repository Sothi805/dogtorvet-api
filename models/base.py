from datetime import datetime
from typing import Optional, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
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


class BaseDBModel(BaseModel):
    """Base model for all database models"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    status: bool = Field(default=True)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True


class BaseCreateModel(BaseModel):
    """Base model for creating records"""
    status: bool = True

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True


class BaseUpdateModel(BaseModel):
    """Base model for updating records"""
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    status: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True


class BaseResponseModel(BaseModel):
    """Base model for API responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    status: bool

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True


class BaseResponse(BaseModel):
    id: str
    status: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 