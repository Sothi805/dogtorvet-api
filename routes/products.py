from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import get_collection, COLLECTIONS
from models.product import Product, ProductCreate, ProductUpdate, ProductResponse
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the products"""
    products_collection = get_collection(COLLECTIONS["products"])
    
    query = {}
    skip = (page - 1) * per_page
    total = await products_collection.count_documents(query)
    
    cursor = products_collection.find(query).skip(skip).limit(per_page)
    products_list = []
    
    async for product_doc in cursor:
        # Convert ObjectId to string and provide defaults for missing fields
        product_data = {
            "id": str(product_doc["_id"]),
            "name": product_doc.get("name", ""),
            "description": product_doc.get("description", ""),
            "sku": product_doc.get("sku", ""),
            "price": product_doc.get("price", 0.0),
            "stock_quantity": product_doc.get("stock_quantity", 0),
            "min_stock_level": product_doc.get("min_stock_level", 0),
            "category": product_doc.get("category", ""),
            "status": product_doc.get("status", True),
            "created_at": product_doc.get("created_at", ""),
            "updated_at": product_doc.get("updated_at", "")
        }
        products_list.append(product_data)
    
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": products_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if products_list else None,
            "to": skip + len(products_list) if products_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/products"
    }


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def store(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created product"""
    products_collection = get_collection(COLLECTIONS["products"])
    
    if product_data.sku:
        existing_sku = await products_collection.find_one({"sku": product_data.sku})
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )
    
    product_dict = product_data.dict()
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    
    result = await products_collection.insert_one(product_dict)
    created_product = await products_collection.find_one({"_id": result.inserted_id})
    
    return ProductResponse(**created_product, id=str(created_product["_id"]))


@router.get("/{product_id}", response_model=ProductResponse)
async def show(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Display the specified product"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_collection(COLLECTIONS["products"])
    product_doc = await products_collection.find_one({"_id": ObjectId(product_id)})
    
    if not product_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(**product_doc, id=str(product_doc["_id"]))


@router.put("/{product_id}", response_model=ProductResponse)
async def update(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified product"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_collection(COLLECTIONS["products"])
    
    existing_product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product_data.sku:
        sku_check = await products_collection.find_one({
            "sku": product_data.sku,
            "_id": {"$ne": ObjectId(product_id)}
        })
        if sku_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )
    
    update_data = product_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    
    updated_product = await products_collection.find_one({"_id": ObjectId(product_id)})
    return ProductResponse(**updated_product, id=str(updated_product["_id"]))


@router.delete("/{product_id}")
async def destroy(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified product (soft delete)"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    products_collection = get_collection(COLLECTIONS["products"])
    
    existing_product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    await products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Product deactivated successfully"} 