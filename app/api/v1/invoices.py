from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.schemas.user import UserDB
from app.schemas.base import APIResponse
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceDB
from app.crud.invoice import invoices_crud
from bson import ObjectId
from datetime import datetime

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

router = APIRouter()

@router.get("/debug", response_model=APIResponse)
async def debug_invoices(
    current_user: UserDB = Depends(get_current_active_user)
):
    """Debug endpoint to check invoice data"""
    try:
        collection = database.get_collection(COLLECTIONS["invoices"])
        
        # Check for invoices with null invoice_number
        null_invoices = await collection.find({'invoice_number': None}).to_list(length=None)
        print(f"🔍 Found {len(null_invoices)} invoices with null invoice_number")
        
        # Check for invoices with missing invoice_number field
        missing_invoices = await collection.find({'invoice_number': {'$exists': False}}).to_list(length=None)
        print(f"🔍 Found {len(missing_invoices)} invoices with missing invoice_number field")
        
        # Check for invoices with empty invoice_number
        empty_invoices = await collection.find({'invoice_number': ''}).to_list(length=None)
        print(f"🔍 Found {len(empty_invoices)} invoices with empty invoice_number")
        
        # Get total count
        total_invoices = await collection.count_documents({})
        print(f"🔍 Total invoices in collection: {total_invoices}")
        
        return APIResponse(
            success=True, 
            message="Debug information retrieved",
            data={
                "null_invoices_count": len(null_invoices),
                "missing_invoices_count": len(missing_invoices),
                "empty_invoices_count": len(empty_invoices),
                "total_invoices": total_invoices,
                "null_invoices": [str(inv.get('_id')) for inv in null_invoices],
                "missing_invoices": [str(inv.get('_id')) for inv in missing_invoices],
                "empty_invoices": [str(inv.get('_id')) for inv in empty_invoices]
            }
        )
    except Exception as e:
        print(f"❌ Error in debug endpoint: {e}")
        import traceback
        print(f"❌ Debug Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.post("/debug/fix-null-invoices", response_model=APIResponse)
async def fix_null_invoices(
    current_user: UserDB = Depends(get_current_active_user)
):
    """Fix invoices with null invoice numbers"""
    try:
        collection = database.get_collection(COLLECTIONS["invoices"])
        
        # Find invoices with null or missing invoice_number
        null_invoices = await collection.find({
            '$or': [
                {'invoice_number': None},
                {'invoice_number': {'$exists': False}},
                {'invoice_number': ''}
            ]
        }).to_list(length=None)
        
        print(f"🔍 Found {len(null_invoices)} invoices to fix")
        
        fixed_count = 0
        for invoice in null_invoices:
            try:
                # Generate new invoice number
                now = datetime.utcnow()
                month_prefix = f'INV-00{now.strftime("%y%m")}'
                
                # Find the last invoice number for this month
                last_invoice = await collection.find_one(
                    {'invoice_number': {'$regex': f'^{month_prefix}'}}, 
                    sort=[('invoice_number', -1)]
                )
                
                if last_invoice and last_invoice.get('invoice_number'):
                    last_number_str = last_invoice['invoice_number'].replace(month_prefix, '')
                    if last_number_str.isdigit():
                        auto_number = int(last_number_str) + 1
                    else:
                        auto_number = 1
                else:
                    auto_number = 1
                
                new_invoice_number = f'{month_prefix}{str(auto_number).zfill(3)}'
                
                # Update the invoice
                result = await collection.update_one(
                    {'_id': invoice['_id']},
                    {'$set': {'invoice_number': new_invoice_number}}
                )
                
                if result.modified_count > 0:
                    fixed_count += 1
                    print(f"✅ Fixed invoice {invoice['_id']} with new number: {new_invoice_number}")
                
            except Exception as e:
                print(f"❌ Failed to fix invoice {invoice['_id']}: {e}")
        
        return APIResponse(
            success=True,
            message=f"Fixed {fixed_count} invoices with null invoice numbers",
            data={"fixed_count": fixed_count}
        )
        
    except Exception as e:
        print(f"❌ Error fixing null invoices: {e}")
        import traceback
        print(f"❌ Fix Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fix invoices: {str(e)}")

@router.get("/", response_model=APIResponse)
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=1000),
    client_id: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include: Optional[str] = Query(None),
    include_deleted: Optional[bool] = Query(False, description="Include deleted invoices"),
    sort_by: Optional[str] = Query("invoice_date"),
    sort_order: Optional[str] = Query("desc"),
    auto_fix_totals: Optional[bool] = Query(True, description="Automatically fix $0.00 totals"),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        print(f"📥 Incoming query parameters for get_invoices: {locals()}")
        collection = database.get_collection(COLLECTIONS["invoices"])
        
        # Build filters - only include active invoices unless include_deleted is True
        filters = {}
        if not include_deleted:
            filters["status"] = True
        
        if client_id:
            filters["client_id"] = client_id
        if payment_status:
            filters["payment_status"] = payment_status
        
        # Calculate skip from page and per_page
        skip = (page - 1) * per_page
        limit = per_page
        
        # Get invoices with basic filters first
        cursor = collection.find(filters)
        
        # Apply sorting
        sort_direction = 1 if sort_order == "asc" else -1
        cursor = cursor.sort(sort_by, sort_direction)
        
        # Apply pagination
        cursor = cursor.skip(skip).limit(limit)
        
        invoices = await cursor.to_list(length=None)
        print(f"🔎 Raw invoices from DB: {invoices}")
        
        # Prepare related collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        
        invoices_response = []
        for inv in invoices:
            print(f"🔎 Processing invoice: {inv}")
            if hasattr(inv, 'model_dump'):
                data = inv.model_dump()
            else:
                data = dict(inv)
            data['id'] = str(data['_id'])
            
            # Convert ObjectId fields to str
            for key in ["client_id", "pet_id", "id"]:
                if key in data and isinstance(data[key], ObjectId):
                    data[key] = str(data[key])
            if '_id' in data and isinstance(data['_id'], ObjectId):
                data['_id'] = str(data['_id'])
            
            # Get client and pet names for search
            client_name = None
            pet_name = None
            
            if data.get('client_id'):
                client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
                if client_doc:
                    client_name = client_doc.get('name')
                    print(f"🔎 Client name for invoice {data['id']}: {client_name}")
            
            if data.get('pet_id'):
                pet_doc = await pets_collection.find_one({'_id': ObjectId(data['pet_id'])})
                if pet_doc:
                    pet_name = pet_doc.get('name')
                    print(f"🔎 Pet name for invoice {data['id']}: {pet_name}")
            
            # Apply search filter if search term is provided
            if search:
                search_lower = search.lower()
                invoice_number_match = data.get('invoice_number', '').lower().find(search_lower) != -1
                client_name_match = client_name and client_name.lower().find(search_lower) != -1
                pet_name_match = pet_name and pet_name.lower().find(search_lower) != -1
                
                print(f"🔎 Search: '{search}' -> invoice_number: {invoice_number_match}, client: {client_name_match}, pet: {pet_name_match}")
                
                if not (invoice_number_match or client_name_match or pet_name_match):
                    print(f"🔎 Skipping invoice {data['id']} - no match")
                    continue
            
            # Populate related fields if include parameter is provided
            if include:
                include_fields = include.split(',')
                
                if 'client' in include_fields and data.get('client_id'):
                    client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
                    if client_doc:
                        client_doc['id'] = str(client_doc['_id'])
                        for key in client_doc:
                            if isinstance(client_doc[key], ObjectId):
                                client_doc[key] = str(client_doc[key])
                        if '_id' in client_doc and isinstance(client_doc['_id'], ObjectId):
                            client_doc['_id'] = str(client_doc['_id'])
                        data['client'] = {
                            'id': client_doc['id'],
                            'name': client_doc.get('name'),
                            'email': client_doc.get('email'),
                            'phone': client_doc.get('phone_number'),
                            'other_contact_info': client_doc.get('other_contact_info'),
                        }
                
                if 'pet' in include_fields and data.get('pet_id'):
                    pet_doc = await pets_collection.find_one({'_id': ObjectId(data['pet_id'])})
                    if pet_doc:
                        for key in pet_doc:
                            if isinstance(pet_doc[key], ObjectId):
                                pet_doc[key] = str(pet_doc[key])
                        if '_id' in pet_doc and isinstance(pet_doc['_id'], ObjectId):
                            pet_doc['_id'] = str(pet_doc['_id'])
                        species_info = None
                        if pet_doc.get('species_id'):
                            species_collection = database.get_collection(COLLECTIONS["species"])
                            species_doc = await species_collection.find_one({'_id': ObjectId(pet_doc['species_id'])})
                            if species_doc:
                                species_info = {
                                    'id': str(species_doc['_id']),
                                    'name': species_doc.get('name')
                                }
                        data['pet'] = {
                            'id': str(pet_doc['_id']),
                            'name': pet_doc.get('name'),
                            'species': species_info,
                            'breed_id': str(pet_doc.get('breed_id')) if pet_doc.get('breed_id') else None,
                        }
            
            # Auto-fix totals if enabled
            if auto_fix_totals:
                print(f"🔧 Checking invoice totals for: {data['id']} (current total: ${data.get('total', 0)})")
                try:
                    # Get items for this invoice
                    items_collection = database.get_collection(COLLECTIONS["invoice_items"])
                    items_with_objectid = await items_collection.find({"invoice_id": ObjectId(data['id'])}).to_list(length=None)
                    items_with_string = await items_collection.find({"invoice_id": data['id']}).to_list(length=None)
                    
                    # Combine both results
                    all_items = items_with_objectid + items_with_string
                    
                    if all_items:
                        # Calculate what the total should be
                        calculated_subtotal = 0
                        for item in all_items:
                            unit_price = float(item.get('unit_price', 0))
                            quantity = float(item.get('quantity', 0))
                            discount_percent = float(item.get('discount_percent', 0))
                            item_total = unit_price * quantity * (1 - discount_percent / 100)
                            calculated_subtotal += item_total
                        
                        # Apply invoice discount
                        discount_percent = float(data.get('discount_percent', 0))
                        discount_amount = calculated_subtotal * (discount_percent / 100)
                        calculated_total = calculated_subtotal - discount_amount
                        
                        current_total = float(data.get('total', 0))
                        
                        # If totals don't match, recalculate
                        if abs(calculated_total - current_total) > 0.01:  # Allow for small rounding differences
                            print(f"🔧 Total mismatch for invoice {data['id']}: current=${current_total}, calculated=${calculated_total}")
                            
                            # Convert string format to ObjectId format if needed
                            for item in items_with_string:
                                await items_collection.update_one(
                                    {"_id": item["_id"]},
                                    {"$set": {"invoice_id": ObjectId(data['id'])}}
                                )
                            
                            # Recalculate totals
                            await recalculate_invoice_totals(data['id'])
                            
                            # Get the updated invoice data
                            updated_invoice = await collection.find_one({"_id": ObjectId(data['id'])})
                            if updated_invoice:
                                data['total'] = updated_invoice.get('total', 0)
                                data['subtotal'] = updated_invoice.get('subtotal', 0)
                                data['discount_amount'] = updated_invoice.get('discount_amount', 0)
                                print(f"✅ Auto-fixed invoice {data['id']}: total=${data['total']}")
                        else:
                            print(f"✅ Invoice {data['id']} totals are correct: ${current_total}")
                    else:
                        print(f"📭 Invoice {data['id']} has no items")
                        
                except Exception as e:
                    print(f"❌ Error auto-fixing invoice {data['id']}: {e}")
            
            invoices_response.append(data)
        
        # Calculate total count for pagination
        if search:
            # For search, we need to count the filtered results
            total_count = len(invoices_response)
        else:
            total_count = await collection.count_documents(filters)
        
        # Calculate pagination metadata
        last_page = (total_count + per_page - 1) // per_page
        from_item = skip + 1
        to_item = min(skip + len(invoices_response), total_count)
        
        # Build paginated response
        paginated_response = {
            "data": invoices_response,
            "meta": {
                "current_page": page,
                "from": from_item,
                "last_page": last_page,
                "per_page": per_page,
                "to": to_item,
                "total": total_count
            },
            "links": {
                "first": f"/api/v1/invoices?page=1&per_page={per_page}",
                "last": f"/api/v1/invoices?page={last_page}&per_page={per_page}",
                "prev": f"/api/v1/invoices?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/invoices?page={page+1}&per_page={per_page}" if page < last_page else None
            }
        }
        
        print(f"🔎 Final response: {len(invoices_response)} invoices found")
        return APIResponse(success=True, message="Invoices retrieved successfully", data=paginated_response)
    except Exception as e:
        print(f"❌ Error in get_invoices: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{invoice_id}", response_model=APIResponse)
async def get_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    include: Optional[str] = Query(None, description="Include related data (client,pet)"),
    include_deleted: Optional[bool] = Query(False, description="Include deleted invoice"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoices"])
    invoice = await invoices_crud.get(collection, invoice_id, include_deleted=include_deleted)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Convert to dict for manipulation
    invoice_data = invoice.model_dump()
    
    # Handle include parameter to populate related data
    if include:
        include_fields = [field.strip() for field in include.split(',')]
        print(f"🔍 Including fields for invoice: {include_fields}")
        
        # Prepare related collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        
        # Populate client data
        if 'client' in include_fields and invoice_data.get('client_id'):
            print(f"🔍 Fetching client with ID: {invoice_data['client_id']}")
            client_doc = await clients_collection.find_one({'_id': ObjectId(invoice_data['client_id'])})
            if client_doc:
                print(f"🔍 Found client: {client_doc}")
                # Convert all ObjectId fields to strings
                for key in client_doc:
                    if isinstance(client_doc[key], ObjectId):
                        client_doc[key] = str(client_doc[key])
                client_doc['id'] = str(client_doc['_id'])
                client_doc['_id'] = str(client_doc['_id'])
                invoice_data['client'] = client_doc
            else:
                print(f"❌ Client not found for ID: {invoice_data['client_id']}")
        
        # Populate pet data
        if 'pet' in include_fields and invoice_data.get('pet_id'):
            print(f"🔍 Fetching pet with ID: {invoice_data['pet_id']}")
            pet_doc = await pets_collection.find_one({'_id': ObjectId(invoice_data['pet_id'])})
            if pet_doc:
                print(f"🔍 Found pet: {pet_doc}")
                # Convert all ObjectId fields to strings
                for key in pet_doc:
                    if isinstance(pet_doc[key], ObjectId):
                        pet_doc[key] = str(pet_doc[key])
                pet_doc['id'] = str(pet_doc['_id'])
                pet_doc['_id'] = str(pet_doc['_id'])
                invoice_data['pet'] = pet_doc
            else:
                print(f"❌ Pet not found for ID: {invoice_data['pet_id']}")
    
    return APIResponse(success=True, message="Invoice retrieved successfully", data=invoice_data)

@router.post("/", response_model=APIResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        print(f"📥 Creating invoice with data: {invoice_data}")
        collection = database.get_collection(COLLECTIONS["invoices"])
        invoice = await invoices_crud.create(collection, invoice_data)
        print(f"✅ Invoice created successfully: {invoice}")
        return APIResponse(success=True, message="Invoice created successfully", data=invoice.model_dump())
    except Exception as e:
        print(f"❌ Error creating invoice: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")

@router.put("/{invoice_id}", response_model=APIResponse)
async def update_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    invoice_update: InvoiceUpdate = ...,
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoices"])
    invoice = await invoices_crud.update(collection, invoice_id, invoice_update)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Recalculate totals if discount_percent was updated
    if hasattr(invoice_update, 'discount_percent') and invoice_update.discount_percent is not None:
        await recalculate_invoice_totals(invoice_id)
    
    return APIResponse(success=True, message="Invoice updated successfully", data=invoice.model_dump())

@router.delete("/{invoice_id}", response_model=APIResponse)
async def delete_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoices"])
    success = await invoices_crud.delete(collection, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice not found or already deleted")
    return APIResponse(success=True, message="Invoice deleted successfully")

@router.post("/{invoice_id}/mark-paid", response_model=APIResponse)
async def mark_invoice_paid(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    collection = database.get_collection(COLLECTIONS["invoices"])
    update = InvoiceUpdate(payment_status="paid")
    invoice = await invoices_crud.update(collection, invoice_id, update)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return APIResponse(success=True, message="Invoice marked as paid", data=invoice.model_dump())

@router.post("/{invoice_id}/restore", response_model=APIResponse)
async def restore_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Restore a soft-deleted invoice"""
    collection = database.get_collection(COLLECTIONS["invoices"])
    update = InvoiceUpdate(status=True)
    invoice = await invoices_crud.update(collection, invoice_id, update)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return APIResponse(success=True, message="Invoice restored successfully", data=invoice.model_dump())

@router.post("/{invoice_id}/recalculate-totals", response_model=APIResponse)
async def recalculate_invoice_totals_endpoint(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Manually recalculate invoice totals"""
    try:
        await recalculate_invoice_totals(invoice_id)
        return APIResponse(success=True, message="Invoice totals recalculated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate totals: {str(e)}")

@router.post("/{invoice_id}/fix-invoice-id-format", response_model=APIResponse)
async def fix_invoice_id_format(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Fix invoice_id format in invoice items to ensure consistency"""
    try:
        print(f"🔧 Fixing invoice_id format for invoice: {invoice_id}")
        
        items_collection = database.get_collection(COLLECTIONS["invoice_items"])
        
        # Find all items for this invoice (both formats)
        items_with_objectid = await items_collection.find({"invoice_id": ObjectId(invoice_id)}).to_list(length=None)
        items_with_string = await items_collection.find({"invoice_id": invoice_id}).to_list(length=None)
        
        print(f"🔧 Found {len(items_with_objectid)} items with ObjectId format")
        print(f"🔧 Found {len(items_with_string)} items with string format")
        
        # Convert string format to ObjectId format
        updated_count = 0
        for item in items_with_string:
            await items_collection.update_one(
                {"_id": item["_id"]},
                {"$set": {"invoice_id": ObjectId(invoice_id)}}
            )
            updated_count += 1
        
        print(f"🔧 Updated {updated_count} items to ObjectId format")
        
        # Recalculate totals after fixing
        await recalculate_invoice_totals(invoice_id)
        
        return APIResponse(
            success=True, 
            message=f"Fixed invoice_id format for {updated_count} items and recalculated totals"
        )
    except Exception as e:
        print(f"❌ Error fixing invoice_id format: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fix invoice_id format: {str(e)}")

@router.post("/{invoice_id}/fix-item-prices", response_model=APIResponse)
async def fix_invoice_item_prices(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Fix invoice item prices by getting them from original service/product data"""
    try:
        print(f"🔧 Fixing item prices for invoice: {invoice_id}")
        
        # Get items for this invoice
        items_collection = database.get_collection(COLLECTIONS["invoice_items"])
        items_with_objectid = await items_collection.find({"invoice_id": ObjectId(invoice_id)}).to_list(length=None)
        items_with_string = await items_collection.find({"invoice_id": invoice_id}).to_list(length=None)
        
        # Combine both results
        all_items = items_with_objectid + items_with_string
        
        if not all_items:
            return APIResponse(
                success=False, 
                message="No items found for this invoice"
            )
        
        print(f"📦 Found {len(all_items)} items to fix")
        
        # Get services and products collections
        services_collection = database.get_collection(COLLECTIONS["services"])
        products_collection = database.get_collection(COLLECTIONS["products"])
        
        updated_count = 0
        for item in all_items:
            item_id = item["_id"]
            current_unit_price = float(item.get('unit_price', 0))
            
            # Skip if price is already correct
            if current_unit_price > 0:
                print(f"✅ Item {item.get('item_name', 'Unknown')} already has correct price: ${current_unit_price}")
                continue
            
            new_unit_price = 0
            
            # Try to get price from service
            if item.get('service_id'):
                try:
                    service_doc = await services_collection.find_one({'_id': ObjectId(item['service_id'])})
                    if service_doc:
                        new_unit_price = float(service_doc.get('price', 0))
                        print(f"💰 Found service price for {item.get('item_name', 'Unknown')}: ${new_unit_price}")
                except Exception as e:
                    print(f"⚠️ Error getting service price: {e}")
            
            # Try to get price from product if service didn't work
            if new_unit_price == 0 and item.get('product_id'):
                try:
                    product_doc = await products_collection.find_one({'_id': ObjectId(item['product_id'])})
                    if product_doc:
                        new_unit_price = float(product_doc.get('price', 0))
                        print(f"💰 Found product price for {item.get('item_name', 'Unknown')}: ${new_unit_price}")
                except Exception as e:
                    print(f"⚠️ Error getting product price: {e}")
            
            # Update the item if we found a price
            if new_unit_price > 0:
                quantity = float(item.get('quantity', 1))
                discount_percent = float(item.get('discount_percent', 0))
                new_net_price = new_unit_price * quantity * (1 - discount_percent / 100)
                
                await items_collection.update_one(
                    {"_id": item_id},
                    {
                        "$set": {
                            "unit_price": new_unit_price,
                            "net_price": new_net_price,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                print(f"✅ Updated item {item.get('item_name', 'Unknown')}: unit_price=${new_unit_price}, net_price=${new_net_price}")
                updated_count += 1
            else:
                print(f"❌ Could not find price for item {item.get('item_name', 'Unknown')}")
        
        if updated_count > 0:
            # Recalculate invoice totals
            await recalculate_invoice_totals(invoice_id)
            print(f"✅ Recalculated invoice totals after fixing {updated_count} items")
        
        return APIResponse(
            success=True, 
            message=f"Fixed prices for {updated_count} items and recalculated totals"
        )
        
    except Exception as e:
        print(f"❌ Error fixing item prices: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fix item prices: {str(e)}")

@router.post("/{invoice_id}/force-recalculate", response_model=APIResponse)
async def force_recalculate_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Force recalculation of invoice totals"""
    try:
        print(f"🔄 Force recalculating invoice: {invoice_id}")
        
        # Get items for this invoice
        items_collection = database.get_collection(COLLECTIONS["invoice_items"])
        items_with_objectid = await items_collection.find({"invoice_id": ObjectId(invoice_id)}).to_list(length=None)
        items_with_string = await items_collection.find({"invoice_id": invoice_id}).to_list(length=None)
        
        print(f"🔍 Found {len(items_with_objectid)} items with ObjectId format")
        print(f"🔍 Found {len(items_with_string)} items with string format")
        
        # Combine both results
        all_items = items_with_objectid + items_with_string
        
        if all_items:
            print(f"📦 Total items found: {len(all_items)}")
            for item in all_items:
                print(f"📦 Item: {item.get('item_name', 'Unknown')} - Qty: {item.get('quantity', 0)} - Price: ${item.get('unit_price', 0)}")
            
            # Convert string format to ObjectId format if needed
            for item in items_with_string:
                await items_collection.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"invoice_id": ObjectId(invoice_id)}}
                )
                print(f"🔧 Converted item {item['_id']} to ObjectId format")
            
            # Recalculate totals
            await recalculate_invoice_totals(invoice_id)
            
            # Get the updated invoice
            collection = database.get_collection(COLLECTIONS["invoices"])
            updated_invoice = await collection.find_one({"_id": ObjectId(invoice_id)})
            
            if updated_invoice:
                result = {
                    "id": str(updated_invoice["_id"]),
                    "invoice_number": updated_invoice.get("invoice_number"),
                    "total": updated_invoice.get("total", 0),
                    "subtotal": updated_invoice.get("subtotal", 0),
                    "discount_amount": updated_invoice.get("discount_amount", 0),
                    "items_count": len(all_items)
                }
                print(f"✅ Force recalculation completed: {result}")
                return APIResponse(
                    success=True, 
                    message=f"Force recalculation completed. Found {len(all_items)} items.",
                    data=result
                )
            else:
                return APIResponse(
                    success=False, 
                    message="Invoice not found after recalculation"
                )
        else:
            print(f"📭 No items found for invoice {invoice_id}")
            return APIResponse(
                success=False, 
                message="No items found for this invoice"
            )
            
    except Exception as e:
        print(f"❌ Error force recalculating invoice: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to force recalculate invoice: {str(e)}")

@router.get("/{invoice_id}/debug", response_model=APIResponse)
async def debug_invoice(
    invoice_id: str = Path(..., description="Invoice ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Debug endpoint to check specific invoice data"""
    try:
        print(f"🔍 Debugging invoice: {invoice_id}")
        
        # Get invoice data
        invoices_collection = database.get_collection(COLLECTIONS["invoices"])
        invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
        
        if not invoice:
            return APIResponse(success=False, message="Invoice not found", data=None)
        
        # Get invoice items - try both ObjectId and string formats
        items_collection = database.get_collection(COLLECTIONS["invoice_items"])
        
        # First try with ObjectId
        items = await items_collection.find({"invoice_id": ObjectId(invoice_id)}).to_list(length=None)
        print(f"🔍 Found {len(items)} items with ObjectId invoice_id")
        
        # If no items found, try with string
        if not items:
            items = await items_collection.find({"invoice_id": invoice_id}).to_list(length=None)
            print(f"🔍 Found {len(items)} items with string invoice_id")
        
        # Calculate what the totals should be
        subtotal = 0
        for item in items:
            unit_price = float(item.get('unit_price', 0))
            quantity = float(item.get('quantity', 0))
            discount_percent = float(item.get('discount_percent', 0))
            item_total = unit_price * quantity * (1 - discount_percent / 100)
            subtotal += item_total
        
        discount_percent = float(invoice.get('discount_percent', 0))
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        debug_data = {
            "invoice_id": invoice_id,
            "invoice_number": invoice.get('invoice_number'),
            "current_totals": {
                "subtotal": invoice.get('subtotal'),
                "total": invoice.get('total'),
                "discount_percent": invoice.get('discount_percent'),
                "discount_amount": invoice.get('discount_amount')
            },
            "calculated_totals": {
                "subtotal": round(subtotal, 2),
                "total": round(total, 2),
                "discount_amount": round(discount_amount, 2)
            },
            "items_count": len(items),
            "items": [
                {
                    "item_name": item.get('item_name'),
                    "unit_price": item.get('unit_price'),
                    "quantity": item.get('quantity'),
                    "discount_percent": item.get('discount_percent'),
                    "calculated_total": round(float(item.get('unit_price', 0)) * float(item.get('quantity', 0)) * (1 - float(item.get('discount_percent', 0)) / 100), 2)
                }
                for item in items
            ]
        }
        
        print(f"🔍 Debug data: {debug_data}")
        return APIResponse(success=True, message="Invoice debug data retrieved", data=debug_data)
        
    except Exception as e:
        print(f"❌ Error in debug endpoint: {e}")
        import traceback
        print(f"❌ Debug Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}") 