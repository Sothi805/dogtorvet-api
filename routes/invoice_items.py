from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from decimal import Decimal

from database import get_collection, COLLECTIONS
from models.invoice_item import InvoiceItem, InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemResponse, ItemType
from models.user import User
from models.invoice import Invoice
from models.service import Service
from models.product import Product
from utils.auth import get_current_user

router = APIRouter(prefix="/invoice-items", tags=["Invoice Items"])


@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    invoice_id: Optional[str] = Query(None),
    item_type: Optional[ItemType] = Query(None),
    search: Optional[str] = Query(None),
    include: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the invoice items"""
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    
    # Build query
    query = {"status": True}  # Only active items
    
    if invoice_id:
        if not ObjectId.is_valid(invoice_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invoice ID"
            )
        query["invoice_id"] = ObjectId(invoice_id)
    
    if item_type:
        query["item_type"] = item_type
    
    if search:
        query["$or"] = [
            {"item_name": {"$regex": search, "$options": "i"}},
            {"item_description": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * per_page
    total = await invoice_items_collection.count_documents(query)
    
    cursor = invoice_items_collection.find(query).skip(skip).limit(per_page).sort("created_at", -1)
    items_list = []
    
    async for item_doc in cursor:
        # Convert ObjectId to string
        item_data = {
            "id": str(item_doc["_id"]),
            "invoice_id": str(item_doc["invoice_id"]),
            "item_type": item_doc.get("item_type", "service"),
            "service_id": str(item_doc["service_id"]) if item_doc.get("service_id") else None,
            "product_id": str(item_doc["product_id"]) if item_doc.get("product_id") else None,
            "item_name": item_doc.get("item_name", ""),
            "item_description": item_doc.get("item_description", ""),
            "unit_price": float(item_doc.get("unit_price", 0.0)),
            "quantity": item_doc.get("quantity", 1),
            "discount_percent": float(item_doc.get("discount_percent", 0.0)),
            "net_price": float(item_doc.get("net_price", 0.0)),
            "status": item_doc.get("status", True),
            "created_at": item_doc.get("created_at", ""),
            "updated_at": item_doc.get("updated_at", "")
        }
        
        # Include related data if requested
        if include:
            includes = [i.strip() for i in include.split(',')]
            
            if 'invoice' in includes and item_doc.get("invoice_id"):
                invoices_collection = get_collection(COLLECTIONS["invoices"])
                invoice_doc = await invoices_collection.find_one({"_id": item_doc["invoice_id"]})
                if invoice_doc:
                    item_data["invoice"] = {
                        "id": str(invoice_doc["_id"]),
                        "invoice_number": invoice_doc.get("invoice_number", ""),
                        "total": float(invoice_doc.get("total", 0.0))
                    }
            
            if 'service' in includes and item_doc.get("service_id"):
                services_collection = get_collection(COLLECTIONS["services"])
                service_doc = await services_collection.find_one({"_id": item_doc["service_id"]})
                if service_doc:
                    item_data["service"] = {
                        "id": str(service_doc["_id"]),
                        "name": service_doc.get("name", ""),
                        "price": float(service_doc.get("price", 0.0))
                    }
            
            if 'product' in includes and item_doc.get("product_id"):
                products_collection = get_collection(COLLECTIONS["products"])
                product_doc = await products_collection.find_one({"_id": item_doc["product_id"]})
                if product_doc:
                    item_data["product"] = {
                        "id": str(product_doc["_id"]),
                        "name": product_doc.get("name", ""),
                        "price": float(product_doc.get("price", 0.0))
                    }
        
        items_list.append(item_data)
    
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": items_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if items_list else None,
            "to": skip + len(items_list) if items_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/invoice-items"
    }


@router.post("/", response_model=InvoiceItemResponse, status_code=status.HTTP_201_CREATED)
async def store(
    item_data: InvoiceItemCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created invoice item"""
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    
    # Validate invoice exists
    if not ObjectId.is_valid(item_data.invoice_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    invoice_doc = await invoices_collection.find_one({"_id": ObjectId(item_data.invoice_id)})
    if not invoice_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Validate service or product exists
    if item_data.item_type == ItemType.SERVICE and item_data.service_id:
        if not ObjectId.is_valid(item_data.service_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid service ID"
            )
        services_collection = get_collection(COLLECTIONS["services"])
        service_doc = await services_collection.find_one({"_id": ObjectId(item_data.service_id)})
        if not service_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    if item_data.item_type == ItemType.PRODUCT and item_data.product_id:
        if not ObjectId.is_valid(item_data.product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID"
            )
        products_collection = get_collection(COLLECTIONS["products"])
        product_doc = await products_collection.find_one({"_id": ObjectId(item_data.product_id)})
        if not product_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if product has enough stock (only if invoice is already paid)
        if invoice_doc.get("payment_status") == "paid":
            current_stock = product_doc.get("stock_quantity", 0)
            if current_stock < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Available: {current_stock}, Requested: {item_data.quantity}"
                )
    
    # Calculate net price
    unit_price = float(item_data.unit_price)
    quantity = item_data.quantity or 1
    discount_percent = float(item_data.discount_percent or 0)
    
    subtotal = unit_price * quantity
    discount_amount = subtotal * (discount_percent / 100)
    net_price = subtotal - discount_amount
    
    item_dict = item_data.dict()
    item_dict["invoice_id"] = ObjectId(item_data.invoice_id)
    if item_data.service_id:
        item_dict["service_id"] = ObjectId(item_data.service_id)
    if item_data.product_id:
        item_dict["product_id"] = ObjectId(item_data.product_id)
    
    # Override calculated values
    item_dict["net_price"] = net_price
    item_dict["unit_price"] = unit_price
    item_dict["quantity"] = quantity
    item_dict["discount_percent"] = discount_percent
    
    item_dict["created_at"] = datetime.utcnow()
    item_dict["updated_at"] = datetime.utcnow()
    item_dict["status"] = True
    
    result = await invoice_items_collection.insert_one(item_dict)
    created_item = await invoice_items_collection.find_one({"_id": result.inserted_id})
    
    # Update invoice totals
    await update_invoice_totals(item_data.invoice_id)
    
    # If invoice is already paid and item is a product, decrement stock
    if invoice_doc.get("payment_status") == "paid" and item_data.item_type == ItemType.PRODUCT and item_data.product_id:
        await products_collection.update_one(
            {"_id": ObjectId(item_data.product_id)},
            {"$inc": {"stock_quantity": -quantity}}
        )
    
    return InvoiceItemResponse(
        **created_item,
        id=str(created_item["_id"]),
        invoice_id=str(created_item["invoice_id"]),
        service_id=str(created_item["service_id"]) if created_item.get("service_id") else None,
        product_id=str(created_item["product_id"]) if created_item.get("product_id") else None,
        unit_price=float(created_item["unit_price"]),
        discount_percent=float(created_item["discount_percent"]),
        net_price=float(created_item["net_price"])
    )


@router.get("/{item_id}", response_model=InvoiceItemResponse)
async def show(
    item_id: str,
    include: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Display the specified invoice item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID"
        )
    
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    item_doc = await invoice_items_collection.find_one({"_id": ObjectId(item_id)})
    
    if not item_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found"
        )
    
    return InvoiceItemResponse(
        **item_doc,
        id=str(item_doc["_id"]),
        invoice_id=str(item_doc["invoice_id"]),
        service_id=str(item_doc["service_id"]) if item_doc.get("service_id") else None,
        product_id=str(item_doc["product_id"]) if item_doc.get("product_id") else None,
        unit_price=float(item_doc["unit_price"]),
        discount_percent=float(item_doc["discount_percent"]),
        net_price=float(item_doc["net_price"])
    )


@router.put("/{item_id}", response_model=InvoiceItemResponse)
async def update(
    item_id: str,
    item_data: InvoiceItemUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified invoice item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID"
        )
    
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    
    existing_item = await invoice_items_collection.find_one({"_id": ObjectId(item_id)})
    if not existing_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found"
        )
    
    update_data = item_data.dict(exclude_unset=True)
    
    # Recalculate if pricing fields changed
    if any(field in update_data for field in ["unit_price", "quantity", "discount_percent"]):
        unit_price = float(update_data.get("unit_price", existing_item.get("unit_price", 0)))
        quantity = update_data.get("quantity", existing_item.get("quantity", 1))
        discount_percent = float(update_data.get("discount_percent", existing_item.get("discount_percent", 0)))
        
        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount_percent / 100)
        net_price = subtotal - discount_amount
        
        update_data["net_price"] = net_price
    
    update_data["updated_at"] = datetime.utcnow()
    
    await invoice_items_collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_data}
    )
    
    updated_item = await invoice_items_collection.find_one({"_id": ObjectId(item_id)})
    
    # Update invoice totals
    invoice_id = str(existing_item["invoice_id"])
    await update_invoice_totals(invoice_id)
    
    return InvoiceItemResponse(
        **updated_item,
        id=str(updated_item["_id"]),
        invoice_id=str(updated_item["invoice_id"]),
        service_id=str(updated_item["service_id"]) if updated_item.get("service_id") else None,
        product_id=str(updated_item["product_id"]) if updated_item.get("product_id") else None,
        unit_price=float(updated_item["unit_price"]),
        discount_percent=float(updated_item["discount_percent"]),
        net_price=float(updated_item["net_price"])
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified invoice item (soft delete)"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID"
        )
    
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    
    existing_item = await invoice_items_collection.find_one({"_id": ObjectId(item_id)})
    if not existing_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found"
        )
    
    await invoice_items_collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    # Update invoice totals after deactivating the item
    invoice_id = str(existing_item["invoice_id"])
    await update_invoice_totals(invoice_id)
    
    return


async def update_invoice_totals(invoice_id: str):
    """
    Recalculates and updates the subtotal and total for a given invoice
    based on its active items.
    """
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    
    # 1. Fetch the parent invoice document first
    invoice_oid = ObjectId(invoice_id)
    invoice_doc = await invoices_collection.find_one({"_id": invoice_oid})
    if not invoice_doc:
        print(f"Invoice {invoice_id} not found during totals update.")
        return

    # 2. Get all active items for this invoice
    items_cursor = invoice_items_collection.find({
        "invoice_id": invoice_oid,
        "status": True
    })
    
    # 3. Calculate subtotal (sum of all item totals before invoice-level discount)
    subtotal = Decimal(0)
    async for item in items_cursor:
        # Each item's net_price already accounts for item-level discounts
        subtotal += Decimal(str(item.get("net_price", "0")))

    # 4. Get invoice-level discount and calculate final total
    invoice_discount_percent = Decimal(str(invoice_doc.get("discount_percent", "0")))
    
    # The subtotal is the sum of all item net_prices. The final total applies the overall invoice discount.
    invoice_discount_amount = subtotal * (invoice_discount_percent / Decimal(100))
    total = subtotal - invoice_discount_amount
    
    # 5. Update the invoice document
    await invoices_collection.update_one(
        {"_id": invoice_oid},
        {"$set": {
            "subtotal": float(subtotal), # Store as float in DB
            "total": float(total),       # Store as float in DB
            "updated_at": datetime.utcnow()
        }}
    ) 