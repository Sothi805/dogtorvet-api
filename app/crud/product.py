from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas.product import ProductDB, ProductCreate, ProductUpdate
from .base import CRUDBase


class CRUDProduct(CRUDBase[ProductDB, ProductCreate, ProductUpdate]):
    """CRUD operations for Product."""
    
    async def get_by_name(self, collection: AsyncIOMotorCollection, name: str) -> Optional[ProductDB]:
        """Get product by name."""
        document = await collection.find_one({"name": name, "status": True})
        if document:
            return ProductDB(**document)
        return None
    
    async def get_by_sku(self, collection: AsyncIOMotorCollection, sku: str) -> Optional[ProductDB]:
        """Get product by SKU."""
        document = await collection.find_one({"sku": sku, "status": True})
        if document:
            return ProductDB(**document)
        return None
    
    async def get_by_category(self, collection: AsyncIOMotorCollection, category: str) -> List[ProductDB]:
        """Get products by category."""
        cursor = collection.find({"category": category, "status": True})
        documents = await cursor.to_list(length=None)
        return [ProductDB(**doc) for doc in documents]
    
    async def get_low_stock(self, collection: AsyncIOMotorCollection, threshold: int = 10) -> List[ProductDB]:
        """Get products with low stock."""
        cursor = collection.find({"stock_quantity": {"$lte": threshold}, "status": True})
        documents = await cursor.to_list(length=None)
        return [ProductDB(**doc) for doc in documents]
    
    async def name_exists(self, collection: AsyncIOMotorCollection, name: str) -> bool:
        """Check if product name already exists."""
        count = await collection.count_documents({"name": name, "status": True})
        return count > 0
    
    async def sku_exists(self, collection: AsyncIOMotorCollection, sku: str) -> bool:
        """Check if SKU already exists."""
        count = await collection.count_documents({"sku": sku, "status": True})
        return count > 0


# Create instance
product_crud = CRUDProduct(ProductDB) 