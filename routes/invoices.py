from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
from bson import ObjectId
from datetime import datetime, date
from io import BytesIO

from database import get_collection, COLLECTIONS, get_database
from models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceResponse, PaymentStatus
from models.user import User
from models.invoice_item import InvoiceItem, InvoiceItemCreate, InvoiceItemUpdate
from models.client import Client
from models.pet import Pet
from models.product import Product
from models.service import Service
from utils.auth import get_current_user

import jinja2
# from weasyprint import HTML, CSS  # Temporarily disabled for Python 3.13 compatibility

router = APIRouter(prefix="/invoices", tags=["Invoices"])

# PDF Template
INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice #{{ invoice.invoice_number }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { display: flex; justify-content: space-between; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #2563eb; }
        .invoice-info { text-align: right; }
        .client-info { margin-bottom: 20px; }
        .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .table th, .table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .table th { background-color: #f8f9fa; }
        .total { font-weight: bold; font-size: 18px; }
        .footer { margin-top: 40px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">DogTorVet</div>
        <div class="invoice-info">
            <h2>INVOICE</h2>
            <p><strong>Invoice #:</strong> {{ invoice.invoice_number }}</p>
            <p><strong>Date:</strong> {{ invoice.issue_date.strftime('%Y-%m-%d') }}</p>
            <p><strong>Due Date:</strong> {{ invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A' }}</p>
        </div>
    </div>
    
    <div class="client-info">
        <h3>Bill To:</h3>
        <p><strong>{{ client.first_name }} {{ client.last_name }}</strong></p>
        <p>{{ client.email }}</p>
        <p>{{ client.phone }}</p>
        {% if client.address %}
        <p>{{ client.address }}</p>
        {% endif %}
    </div>
    
    {% if pet %}
    <div class="pet-info">
        <h3>Patient:</h3>
        <p><strong>{{ pet.name }}</strong> ({{ pet.species.name if pet.species else 'Unknown' }})</p>
    </div>
    {% endif %}
    
    <table class="table">
        <thead>
            <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.description }}</td>
                <td>{{ item.quantity }}</td>
                <td>${{ "%.2f"|format(item.unit_price) }}</td>
                <td>${{ "%.2f"|format(item.total_price) }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="3" class="total">Subtotal:</td>
                <td class="total">${{ "%.2f"|format(invoice.subtotal) }}</td>
            </tr>
            <tr>
                <td colspan="3" class="total">Tax ({{ invoice.tax_rate }}%):</td>
                <td class="total">${{ "%.2f"|format(invoice.tax_amount) }}</td>
            </tr>
            <tr>
                <td colspan="3" class="total">Total:</td>
                <td class="total">${{ "%.2f"|format(invoice.total_amount) }}</td>
            </tr>
        </tfoot>
    </table>
    
    {% if invoice.notes %}
    <div class="notes">
        <h3>Notes:</h3>
        <p>{{ invoice.notes }}</p>
    </div>
    {% endif %}
    
    <div class="footer">
        <p>Thank you for choosing DogTorVet!</p>
        <p>Generated on {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
"""

@router.get("/", response_model=dict)
async def index(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Display a listing of the invoices"""
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    
    query = {}
    skip = (page - 1) * per_page
    total = await invoices_collection.count_documents(query)
    
    cursor = invoices_collection.find(query).skip(skip).limit(per_page)
    invoices_list = []
    
    # Get collections for lookups
    clients_collection = get_collection(COLLECTIONS["clients"])
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    async for invoice_doc in cursor:
        # Convert ObjectId to string and provide defaults for missing fields
        invoice_data = {
            "id": str(invoice_doc["_id"]),
            "invoice_number": invoice_doc.get("invoice_number", ""),
            "client_id": str(invoice_doc["client_id"]),
            "pet_id": str(invoice_doc["pet_id"]) if invoice_doc.get("pet_id") else None,
            "invoice_date": invoice_doc.get("invoice_date").isoformat() if invoice_doc.get("invoice_date") else "",
            "due_date": invoice_doc.get("due_date").isoformat() if invoice_doc.get("due_date") else "",
            "subtotal": invoice_doc.get("subtotal", 0.0),
            "discount_percent": invoice_doc.get("discount_percent", 0.0),
            "total": invoice_doc.get("total", 0.0),
            "payment_status": invoice_doc.get("payment_status", "pending"),
            "notes": invoice_doc.get("notes", ""),
            "status": invoice_doc.get("status", True),
            "created_at": invoice_doc.get("created_at").isoformat() if invoice_doc.get("created_at") else "",
            "updated_at": invoice_doc.get("updated_at").isoformat() if invoice_doc.get("updated_at") else ""
        }
        
        # Populate client data
        if invoice_doc.get("client_id"):
            client_doc = await clients_collection.find_one({"_id": invoice_doc["client_id"]})
            if client_doc:
                invoice_data["client"] = {
                    "id": str(client_doc["_id"]),
                    "name": client_doc.get('name', '') or f"{client_doc.get('first_name', '')} {client_doc.get('last_name', '')}".strip(),
                    "email": client_doc.get("other_contact_info", "") or client_doc.get("email", ""),
                    "phone": client_doc.get("phone_number", "")
                }
        
        # Populate pet data
        if invoice_doc.get("pet_id"):
            pet_doc = await pets_collection.find_one({"_id": invoice_doc["pet_id"]})
            if pet_doc:
                invoice_data["pet"] = {
                    "id": str(pet_doc["_id"]),
                    "name": pet_doc.get("name", ""),
                    "species": pet_doc.get("species", "")
                }
        
        invoices_list.append(invoice_data)
    
    last_page = (total + per_page - 1) // per_page
    
    return {
        "data": invoices_list,
        "meta": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "from": skip + 1 if invoices_list else None,
            "to": skip + len(invoices_list) if invoices_list else None,
        },
        "links": {
            "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
            "next": f"?page={page+1}&per_page={per_page}" if page < last_page else None,
            "first": f"?page=1&per_page={per_page}",
            "last": f"?page={last_page}&per_page={per_page}",
        },
        "path": "/api/invoices"
    }


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def store(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_user)
):
    """Store a newly created invoice"""
    try:
        invoices_collection = get_collection(COLLECTIONS["invoices"])
        
        # Auto-generate invoice number: INV{YY}{MM}{DD}NO{auto-number}
        today = datetime.utcnow().date()
        date_prefix = f"INV{today.strftime('%y%m%d')}NO"
        
        # Find the last invoice number for today
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        today_invoices = await invoices_collection.find({
            "created_at": {"$gte": start_of_day, "$lt": end_of_day}
        }).sort("created_at", -1).to_list(1)
        
        if today_invoices:
            # Extract the last number and increment
            last_invoice_number = today_invoices[0].get("invoice_number", "")
            if last_invoice_number.startswith(date_prefix):
                try:
                    last_number = int(last_invoice_number.replace(date_prefix, ""))
                    next_number = last_number + 1
                except ValueError:
                    next_number = 1
            else:
                next_number = 1
        else:
            next_number = 1
        
        # Generate the new invoice number
        auto_invoice_number = f"{date_prefix}{next_number:03d}"
        
        invoice_dict = invoice_data.model_dump()
        invoice_dict["invoice_number"] = auto_invoice_number  # Override with auto-generated number
        invoice_dict["client_id"] = ObjectId(invoice_data.client_id)
        if invoice_data.pet_id:
            invoice_dict["pet_id"] = ObjectId(invoice_data.pet_id)
        
        # Convert date objects to datetime for MongoDB
        if invoice_dict.get("invoice_date"):
            invoice_dict["invoice_date"] = datetime.combine(invoice_dict["invoice_date"], datetime.min.time())
        if invoice_dict.get("due_date"):
            invoice_dict["due_date"] = datetime.combine(invoice_dict["due_date"], datetime.min.time())
        
        # Set defaults for missing fields
        invoice_dict.setdefault("subtotal", 0.0)
        invoice_dict.setdefault("discount_percent", 0.0)
        invoice_dict.setdefault("total", 0.0)
        invoice_dict.setdefault("payment_status", "pending")
        
        invoice_dict["created_at"] = datetime.utcnow()
        invoice_dict["updated_at"] = datetime.utcnow()
        invoice_dict["status"] = True  # Active by default
        
        result = await invoices_collection.insert_one(invoice_dict)
        created_invoice = await invoices_collection.find_one({"_id": result.inserted_id})
        
        # Get collections for lookups
        clients_collection = get_collection(COLLECTIONS["clients"])
        pets_collection = get_collection(COLLECTIONS["pets"])
        
        # Prepare response data with only the fields InvoiceResponse expects
        response_data = {
            "id": str(created_invoice["_id"]),
            "invoice_number": created_invoice["invoice_number"],
            "client_id": str(created_invoice["client_id"]),
            "pet_id": str(created_invoice.get("pet_id", "")) if created_invoice.get("pet_id") else None,
            "invoice_date": created_invoice["invoice_date"].isoformat() if created_invoice.get("invoice_date") else "",
            "due_date": created_invoice.get("due_date").isoformat() if created_invoice.get("due_date") else None,
            "subtotal": float(created_invoice.get("subtotal", 0)),
            "discount_percent": float(created_invoice.get("discount_percent", 0)),
            "total": float(created_invoice.get("total", 0)),
            "payment_status": created_invoice.get("payment_status", "pending"),
            "notes": created_invoice.get("notes")
        }
        
        # Populate client data
        if created_invoice.get("client_id"):
            client_doc = await clients_collection.find_one({"_id": created_invoice["client_id"]})
            if client_doc:
                response_data["client"] = {
                    "id": str(client_doc["_id"]),
                    "name": client_doc.get('name', '') or f"{client_doc.get('first_name', '')} {client_doc.get('last_name', '')}".strip(),
                    "email": client_doc.get("other_contact_info", "") or client_doc.get("email", ""),
                    "phone": client_doc.get("phone_number", "")
                }
        
        # Populate pet data
        if created_invoice.get("pet_id"):
            pet_doc = await pets_collection.find_one({"_id": created_invoice["pet_id"]})
            if pet_doc:
                response_data["pet"] = {
                    "id": str(pet_doc["_id"]),
                    "name": pet_doc.get("name", ""),
                    "species": pet_doc.get("species", "")
                }
        
        return {
            "data": response_data
        }
    except Exception as e:
        import traceback
        print(f"❌ Error in invoice creation: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return a more detailed error for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/{invoice_id}", response_model=dict)
async def show(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    """Display the specified invoice"""
    if not ObjectId.is_valid(invoice_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    invoice_doc = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
    
    if not invoice_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Get collections for lookups
    clients_collection = get_collection(COLLECTIONS["clients"])
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Prepare response data with only the fields InvoiceResponse expects
    response_data = {
        "id": str(invoice_doc["_id"]),
        "invoice_number": invoice_doc["invoice_number"],
        "client_id": str(invoice_doc["client_id"]),
        "pet_id": str(invoice_doc.get("pet_id", "")) if invoice_doc.get("pet_id") else None,
        "invoice_date": invoice_doc["invoice_date"].isoformat() if invoice_doc.get("invoice_date") else "",
        "due_date": invoice_doc.get("due_date").isoformat() if invoice_doc.get("due_date") else None,
        "subtotal": float(invoice_doc.get("subtotal", 0)),
        "discount_percent": float(invoice_doc.get("discount_percent", 0)),
        "total": float(invoice_doc.get("total", 0)),
        "payment_status": invoice_doc.get("payment_status", "pending"),
        "notes": invoice_doc.get("notes")
    }
    
    # Populate client data
    if invoice_doc.get("client_id"):
        client_doc = await clients_collection.find_one({"_id": invoice_doc["client_id"]})
        if client_doc:
            response_data["client"] = {
                "id": str(client_doc["_id"]),
                "name": client_doc.get('name', '') or f"{client_doc.get('first_name', '')} {client_doc.get('last_name', '')}".strip(),
                "email": client_doc.get("other_contact_info", "") or client_doc.get("email", ""),
                "phone": client_doc.get("phone_number", "")
            }
    
    # Populate pet data
    if invoice_doc.get("pet_id"):
        pet_doc = await pets_collection.find_one({"_id": invoice_doc["pet_id"]})
        if pet_doc:
            response_data["pet"] = {
                "id": str(pet_doc["_id"]),
                "name": pet_doc.get("name", ""),
                "species": pet_doc.get("species", "")
            }
    
    return {
        "data": response_data
    }


@router.put("/{invoice_id}", response_model=dict)
async def update(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update the specified invoice"""
    if not ObjectId.is_valid(invoice_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    
    existing_invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
    if not existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field in ["client_id", "pet_id"]:
        if field in update_data and update_data[field]:
            update_data[field] = ObjectId(update_data[field])
    update_data["updated_at"] = datetime.utcnow()
    
    # Check if payment status is changing from unpaid to paid
    old_payment_status = existing_invoice.get("payment_status", "pending")
    new_payment_status = update_data.get("payment_status", old_payment_status)
    
    await invoices_collection.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": update_data}
    )
    
    # Handle inventory when payment status changes to paid
    if old_payment_status != "paid" and new_payment_status == "paid":
        await handle_invoice_payment(invoice_id)
    
    updated_invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
    
    # Get collections for lookups
    clients_collection = get_collection(COLLECTIONS["clients"])
    pets_collection = get_collection(COLLECTIONS["pets"])
    
    # Prepare response data with only the fields InvoiceResponse expects
    response_data = {
        "id": str(updated_invoice["_id"]),
        "invoice_number": updated_invoice["invoice_number"],
        "client_id": str(updated_invoice["client_id"]),
        "pet_id": str(updated_invoice.get("pet_id", "")) if updated_invoice.get("pet_id") else None,
        "invoice_date": updated_invoice["invoice_date"].isoformat() if updated_invoice.get("invoice_date") else "",
        "due_date": updated_invoice.get("due_date").isoformat() if updated_invoice.get("due_date") else None,
        "subtotal": float(updated_invoice.get("subtotal", 0)),
        "discount_percent": float(updated_invoice.get("discount_percent", 0)),
        "total": float(updated_invoice.get("total", 0)),
        "payment_status": updated_invoice.get("payment_status", "pending"),
        "notes": updated_invoice.get("notes")
    }
    
    # Populate client data
    if updated_invoice.get("client_id"):
        client_doc = await clients_collection.find_one({"_id": updated_invoice["client_id"]})
        if client_doc:
            response_data["client"] = {
                "id": str(client_doc["_id"]),
                "name": client_doc.get('name', '') or f"{client_doc.get('first_name', '')} {client_doc.get('last_name', '')}".strip(),
                "email": client_doc.get("other_contact_info", "") or client_doc.get("email", ""),
                "phone": client_doc.get("phone_number", "")
            }
    
    # Populate pet data
    if updated_invoice.get("pet_id"):
        pet_doc = await pets_collection.find_one({"_id": updated_invoice["pet_id"]})
        if pet_doc:
            response_data["pet"] = {
                "id": str(pet_doc["_id"]),
                "name": pet_doc.get("name", ""),
                "species": pet_doc.get("species", "")
            }
    
    return {
        "data": response_data
    }


@router.delete("/{invoice_id}")
async def destroy(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove the specified invoice (soft delete)"""
    if not ObjectId.is_valid(invoice_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID"
        )
    
    invoices_collection = get_collection(COLLECTIONS["invoices"])
    
    existing_invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
    if not existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    await invoices_collection.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {"status": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Invoice deactivated successfully"}


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Generate and download invoice as PDF - Temporarily disabled for Python 3.13 compatibility"""
    raise HTTPException(
        status_code=501, 
        detail="PDF generation temporarily disabled. Will be re-enabled with compatible dependencies."
    )
    
    # TODO: Re-enable when weasyprint is compatible with Python 3.13
    # try:
    #     # Get invoice
    #     invoice = await db.invoices.find_one({"_id": invoice_id})
    #     if not invoice:
    #         raise HTTPException(status_code=404, detail="Invoice not found")
    #     
    #     # Get related data
    #     client = await db.clients.find_one({"_id": invoice["client_id"]})
    #     pet = None
    #     if invoice.get("pet_id"):
    #         pet = await db.pets.find_one({"_id": invoice["pet_id"]})
    #         if pet and pet.get("species_id"):
    #             species = await db.species.find_one({"_id": pet["species_id"]})
    #             if species:
    #                 pet["species"] = species
    #     
    #     # Get invoice items
    #     items = await db.invoice_items.find({"invoice_id": invoice_id}).to_list(None)
    #     
    #     # Render HTML
    #     template = jinja2.Template(INVOICE_TEMPLATE)
    #     html_content = template.render(
    #         invoice=invoice,
    #         client=client,
    #         pet=pet,
    #         items=items,
    #         datetime=datetime
    #     )
    #     
    #     # Generate PDF
    #     pdf = HTML(string=html_content).write_pdf()
    #     
    #     # Return PDF response
    #     return Response(
    #         content=pdf,
    #         media_type="application/pdf",
    #         headers={
    #             "Content-Disposition": f"attachment; filename=invoice_{invoice['invoice_number']}.pdf"
    #         }
    #     )
    #     
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}") 


async def handle_invoice_payment(invoice_id: str):
    """
    Handle inventory updates when an invoice is marked as paid.
    Decrements stock for all product items in the invoice.
    """
    invoice_items_collection = get_collection(COLLECTIONS["invoice_items"])
    products_collection = get_collection(COLLECTIONS["products"])
    
    # Get all active items for this invoice
    invoice_oid = ObjectId(invoice_id)
    items_cursor = invoice_items_collection.find({
        "invoice_id": invoice_oid,
        "status": True,
        "item_type": "product"  # Only process products, not services
    })
    
    async for item in items_cursor:
        if item.get("product_id"):
            # Decrement stock for this product
            await products_collection.update_one(
                {"_id": item["product_id"]},
                {"$inc": {"stock_quantity": -item.get("quantity", 1)}}
            )
            
            # Log the inventory change
            from utils.logging import logger
            logger.info(f"Inventory updated: Product {item['product_id']} decreased by {item.get('quantity', 1)} units for invoice {invoice_id}")

