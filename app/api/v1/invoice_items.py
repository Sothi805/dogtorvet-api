from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.schemas.user import UserDB
from app.schemas.base import APIResponse
from app.schemas.invoice import InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemDB
from app.crud.invoice_item import invoice_items_crud
from bson import ObjectId
from datetime import datetime

router = APIRouter()

async def recalculate_invoice_totals(invoice_id: str):
    """Recalculate invoice totals based on its items"""
    try:
        print(f"🔄 Recalculating totals for invoice: {invoice_id}")
        
        # Get all items for this invoice - try both ObjectId and string formats
        items_collection = database.get_collection(COLLECTIONS["invoice_items"])
        
        # First try with ObjectId
        items = await items_collection.find({"invoice_id": ObjectId(invoice_id)}).to_list(length=None)
        print(f"🔍 Found {len(items)} items with ObjectId invoice_id")
        
        # If no items found, try with string
        if not items:
            items = await items_collection.find({"invoice_id": invoice_id}).to_list(length=None)
            print(f"🔍 Found {len(items)} items with string invoice_id")
        
        # Calculate subtotal from items
        subtotal = 0
        for item in items:
            unit_price = float(item.get('unit_price', 0))
            quantity = float(item.get('quantity', 0))
            discount_percent = float(item.get('discount_percent', 0))
            
            # Calculate item total with discount
            item_total = unit_price * quantity * (1 - discount_percent / 100)
            subtotal += item_total
        
        # Get invoice to apply discount
        invoices_collection = database.get_collection(COLLECTIONS["invoices"])
        invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
        
        if invoice:
            discount_percent = float(invoice.get('discount_percent', 0))
            discount_amount = subtotal * (discount_percent / 100)
            total = subtotal - discount_amount
            
            # Update invoice with new totals
            await invoices_collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {
                    "$set": {
                        "subtotal": round(subtotal, 2),
                        "total": round(total, 2),
                        "discount_amount": round(discount_amount, 2),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            print(f"💰 Updated invoice {invoice_id}: subtotal=${subtotal:.2f}, total=${total:.2f}, discount=${discount_amount:.2f}")
        else:
            print(f"❌ Invoice {invoice_id} not found for total recalculation")
            
    except Exception as e:
        print(f"❌ Error recalculating invoice totals: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

@router.get("/", response_model=APIResponse)
async def get_invoice_items(
    invoice_id: Optional[str] = Query(None),
    include: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoice_items"])
    
    if invoice_id:
        print(f"🔍 Getting items for invoice: {invoice_id}")
        items = await invoice_items_crud.get_by_invoice(collection, invoice_id)
        print(f"📦 Found {len(items)} items for invoice {invoice_id}")
        for item in items:
            print(f"📦 Item: {item.id} - {item.item_name} - invoice_id: {item.invoice_id}")
    else:
        # Get all items with pagination
        cursor = collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        items = []
        for doc in docs:
            doc['id'] = str(doc['_id'])
            for key in ['_id', 'id', 'invoice_id', 'service_id', 'product_id']:
                if key in doc and isinstance(doc[key], ObjectId):
                    doc[key] = str(doc[key])
            items.append(InvoiceItemDB(**doc))
    
    # Handle include parameter to populate related data
    if include and items:
        print(f"🔍 Including fields: {include}")
        include_fields = [field.strip() for field in include.split(',')]
        print(f"🔍 Include fields: {include_fields}")
        
        for item in items:
            item_dict = item.model_dump()
            print(f"🔍 Processing item: {item.id}, service_id: {item.service_id}, product_id: {item.product_id}")
            
            # Populate service data
            if 'service' in include_fields and item.service_id:
                print(f"🔍 Fetching service with ID: {item.service_id}")
                service_collection = database.get_collection(COLLECTIONS["services"])
                service_doc = await service_collection.find_one({'_id': ObjectId(item.service_id)})
                if service_doc:
                    print(f"🔍 Found service: {service_doc}")
                    service_doc['id'] = str(service_doc['_id'])
                    service_doc['_id'] = str(service_doc['_id'])
                    item_dict['service'] = service_doc
                else:
                    print(f"❌ Service not found for ID: {item.service_id}")
            
            # Populate product data
            if 'product' in include_fields and item.product_id:
                print(f"🔍 Fetching product with ID: {item.product_id}")
                product_collection = database.get_collection(COLLECTIONS["products"])
                product_doc = await product_collection.find_one({'_id': ObjectId(item.product_id)})
                if product_doc:
                    print(f"🔍 Found product: {product_doc}")
                    product_doc['id'] = str(product_doc['_id'])
                    product_doc['_id'] = str(product_doc['_id'])
                    item_dict['product'] = product_doc
                else:
                    print(f"❌ Product not found for ID: {item.product_id}")
            
            # Update the item with populated data
            items[items.index(item)] = InvoiceItemDB(**item_dict)
    
    return APIResponse(success=True, message="Invoice items retrieved successfully", data=[item.model_dump() for item in items])

@router.get("/{item_id}", response_model=APIResponse)
async def get_invoice_item(
    item_id: str = Path(..., description="Invoice Item ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoice_items"])
    item = await invoice_items_crud.get(collection, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Invoice item not found")
    return APIResponse(success=True, message="Invoice item retrieved successfully", data=item.model_dump())

@router.post("/", response_model=APIResponse)
async def create_invoice_item(
    item_data: InvoiceItemCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        print(f"🔄 Creating invoice item for invoice: {item_data.invoice_id}")
        print(f"📦 Item data: {item_data.model_dump()}")
        
        collection = database.get_collection(COLLECTIONS["invoice_items"])
        
        # Get services and products collections for historical snapshots
        services_collection = database.get_collection(COLLECTIONS["services"])
        products_collection = database.get_collection(COLLECTIONS["products"])
        
        item = await invoice_items_crud.create(
            collection, 
            item_data, 
            services_collection, 
            products_collection
        )
        
        print(f"✅ Invoice item created successfully: {item.model_dump()}")
        
        # Recalculate invoice totals after creating item
        await recalculate_invoice_totals(item_data.invoice_id)
        
        return APIResponse(success=True, message="Invoice item created successfully", data=item.model_dump())
    except Exception as e:
        print(f"❌ Error creating invoice item: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create invoice item: {str(e)}")

@router.put("/{item_id}", response_model=APIResponse)
async def update_invoice_item(
    item_id: str = Path(..., description="Invoice Item ID"),
    item_update: InvoiceItemUpdate = ...,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoice_items"])
    item = await invoice_items_crud.update(collection, item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Invoice item not found")
    
    # Recalculate invoice totals after updating item
    await recalculate_invoice_totals(item.invoice_id)
    
    return APIResponse(success=True, message="Invoice item updated successfully", data=item.model_dump())

@router.delete("/{item_id}", response_model=APIResponse)
async def delete_invoice_item(
    item_id: str = Path(..., description="Invoice Item ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoice_items"])
    
    # Get the item first to get the invoice_id for recalculation
    item = await invoice_items_crud.get(collection, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Invoice item not found")
    
    success = await invoice_items_crud.delete(collection, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice item not found or already deleted")
    
    # Recalculate invoice totals after deleting item
    await recalculate_invoice_totals(item.invoice_id)
    
    return APIResponse(success=True, message="Invoice item deleted successfully") 