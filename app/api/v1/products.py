import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import product_crud
from app.schemas.product import ProductDB, ProductCreate, ProductUpdate, ProductResponse
from app.schemas.user import UserDB
from app.schemas.base import APIResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=APIResponse)
async def get_products(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["products"])
    filters = {}
    if status and status != "all":
        if status == "active":
            filters["status"] = True
        elif status == "inactive":
            filters["status"] = False
    products = await product_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
    products_response = [
        ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            category=product.category,
            sku=product.sku,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
        for product in products
    ]
    return APIResponse(success=True, message="Products retrieved successfully", data=products_response)

@router.post("/", response_model=APIResponse)
async def create_product(
    product_create: ProductCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["products"])
    try:
        # Check if product name already exists
        if await product_crud.name_exists(collection, product_create.name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product name already exists")
        product = await product_crud.create(collection, product_create)
        return APIResponse(success=True, message="Product created successfully", data=ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            category=product.category,
            sku=product.sku,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at
        ))
    except Exception as e:
        import traceback
        logger.error(f"Error creating product: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.put("/{product_id}", response_model=APIResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["products"])
    product = await product_crud.get(collection, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    updated_product = await product_crud.update(collection, product_id, product_update)
    if not updated_product:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product")
    return APIResponse(success=True, message="Product updated successfully", data=ProductResponse(
        id=str(updated_product.id),
        name=updated_product.name,
        description=updated_product.description,
        price=updated_product.price,
        stock_quantity=updated_product.stock_quantity,
        category=updated_product.category,
        sku=updated_product.sku,
        status=updated_product.status,
        created_at=updated_product.created_at,
        updated_at=updated_product.updated_at
    )) 