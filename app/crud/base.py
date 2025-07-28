from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime, timezone, date, time
from decimal import Decimal

from app.schemas.base import BaseDBSchema

ModelType = TypeVar("ModelType", bound=BaseDBSchema)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(self, collection: AsyncIOMotorCollection, id: str) -> Optional[ModelType]:
        """Get a single record by ID."""
        if not ObjectId.is_valid(id):
            return None
        
        document = await collection.find_one({"_id": ObjectId(id)})
        if document is not None:
            try:
                return self.model(**document)
            except Exception as e:
                print(f"⚠️ Invalid document found for ID {id}: {e}")
                return None
        return None
    
    async def get_multi(
        self, 
        collection: AsyncIOMotorCollection, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records."""
        query = {}
        if filters:
            # Convert string IDs to ObjectId for MongoDB queries
            processed_filters = {}
            for key, value in filters.items():
                if key.endswith('_id') and isinstance(value, str) and ObjectId.is_valid(value):
                    processed_filters[key] = ObjectId(value)
                else:
                    processed_filters[key] = value
            query.update(processed_filters)
        
        cursor = collection.find(query).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Filter out invalid documents that don't have required fields
        valid_documents = []
        for doc in documents:
            try:
                # Try to create the model instance
                model_instance = self.model(**doc)
                valid_documents.append(model_instance)
            except Exception as e:
                # Log the invalid document and skip it
                print(f"⚠️ Skipping invalid document: {e}")
                continue
        
        return valid_documents
    
    async def create(self, collection: AsyncIOMotorCollection, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump()
        obj_data["created_at"] = datetime.now(timezone.utc)
        obj_data["updated_at"] = datetime.now(timezone.utc)
        
        # Convert string IDs to ObjectId for MongoDB
        for key, value in obj_data.items():
            if key.endswith('_id') and isinstance(value, str) and ObjectId.is_valid(value):
                obj_data[key] = ObjectId(value)
        
        # Convert all datetime.date to datetime.datetime
        for key, value in obj_data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                obj_data[key] = datetime.combine(value, time.min, tzinfo=timezone.utc)
        
        # Convert Decimal objects to float for MongoDB compatibility
        for key, value in obj_data.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                obj_data[key] = float(value)
        
        # Convert empty string to None for nullable unique fields (like sku)
        for key, value in obj_data.items():
            if key in ["sku"] and (value is None or value == ""):
                obj_data[key] = None
        
        result = await collection.insert_one(obj_data)
        created_document = await collection.find_one({"_id": result.inserted_id})
        if created_document is not None:
            return self.model(**created_document)
        raise RuntimeError("Failed to create document")
    
    async def update(
        self, 
        collection: AsyncIOMotorCollection, 
        id: str, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """Update a record."""
        if not ObjectId.is_valid(id):
            return None
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Convert Decimal objects to float for MongoDB compatibility
            for key, value in update_data.items():
                if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                    update_data[key] = float(value)
            # Convert empty string to None for nullable unique fields (like sku)
            for key, value in update_data.items():
                if key in ["sku"] and (value is None or value == ""):
                    update_data[key] = None
            
            result = await collection.update_one(
                {"_id": ObjectId(id)}, 
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                updated_document = await collection.find_one({"_id": ObjectId(id)})
                if updated_document is not None:
                    return self.model(**updated_document)
        
        return None
    
    async def delete(self, collection: AsyncIOMotorCollection, id: str) -> bool:
        """Soft delete a record."""
        if not ObjectId.is_valid(id):
            return False
        
        result = await collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"status": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        return result.modified_count > 0
    
    async def count(self, collection: AsyncIOMotorCollection, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count valid records."""
        query = {}
        if filters:
            query.update(filters)
        
        cursor = collection.find(query)
        documents = await cursor.to_list(length=None)
        
        # Count only valid documents
        valid_count = 0
        for doc in documents:
            try:
                self.model(**doc)
                valid_count += 1
            except Exception:
                continue
        
        return valid_count
    
    async def exists(self, collection: AsyncIOMotorCollection, id: str) -> bool:
        """Check if record exists and is valid."""
        if not ObjectId.is_valid(id):
            return False
        
        document = await collection.find_one({"_id": ObjectId(id)})
        if document is not None:
            try:
                self.model(**document)
                return True
            except Exception:
                return False
        return False 