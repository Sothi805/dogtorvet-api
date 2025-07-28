from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceDB, InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemDB

class CRUDInvoice:
    async def create(self, collection: AsyncIOMotorCollection, invoice_data: InvoiceCreate) -> InvoiceDB:
        try:
            now = datetime.utcnow()
            invoice_doc = invoice_data.model_dump(exclude_unset=True)
            
            # Auto-generate invoice number with format INV-00YYMM{AUTONUMBER}
            # Auto number resets each month
            month_prefix = f'INV-00{now.strftime("%y%m")}'  # YYMM format for monthly reset
            
            print(f"🔍 Generating invoice number with prefix: {month_prefix}")
            
            # Find the last invoice number for this month
            last_invoice = await collection.find_one(
                {'invoice_number': {'$regex': f'^{month_prefix}'}}, 
                sort=[('invoice_number', -1)]
            )
            
            if last_invoice and last_invoice.get('invoice_number'):
                # Extract the auto number from the last invoice
                last_number_str = last_invoice['invoice_number'].replace(month_prefix, '')
                if last_number_str.isdigit():
                    auto_number = int(last_number_str) + 1
                else:
                    auto_number = 1
            else:
                auto_number = 1
            
            invoice_number = f'{month_prefix}{str(auto_number).zfill(3)}'
            print(f"🔍 Generated invoice number: {invoice_number}")
            
            # Ensure invoice_number is never null
            if not invoice_number:
                raise ValueError("Failed to generate invoice number")
            
            invoice_doc['invoice_number'] = invoice_number
            
            # Calculate totals from items (if any)
            subtotal = 0.0
            items = getattr(invoice_data, 'items', None)
            if items and len(items) > 0:
                for item in items:
                    item_total = item.unit_price * item.quantity * (1 - item.discount_percent / 100)
                    subtotal += item_total
            
            invoice_doc['subtotal'] = subtotal
            invoice_doc['total'] = subtotal * (1 - invoice_data.discount_percent / 100)
            
            # Remove payment_status since we calculate it dynamically
            if 'payment_status' in invoice_doc:
                del invoice_doc['payment_status']
            
            invoice_doc['created_at'] = now
            invoice_doc['updated_at'] = now
            invoice_doc['status'] = True
            
            print(f"🔍 Invoice doc before insert: {invoice_doc}")
            
            # Insert invoice
            result = await collection.insert_one(invoice_doc)
            invoice_doc['_id'] = result.inserted_id
            invoice_doc['id'] = str(result.inserted_id)
            
            # Convert ObjectId fields to str
            for key in ['_id', 'id', 'client_id', 'pet_id']:
                if key in invoice_doc and isinstance(invoice_doc[key], ObjectId):
                    invoice_doc[key] = str(invoice_doc[key])
            
            print(f"🔍 Invoice doc after insert: {invoice_doc}")
            
            return InvoiceDB(**invoice_doc)
        except Exception as e:
            print(f"❌ Error in CRUD create: {e}")
            import traceback
            print(f"❌ CRUD Traceback: {traceback.format_exc()}")
            raise e

    async def get(self, collection: AsyncIOMotorCollection, invoice_id: str, include_deleted: bool = False) -> Optional[InvoiceDB]:
        filters = {'_id': ObjectId(invoice_id)}
        if not include_deleted:
            filters['status'] = True
        doc = await collection.find_one(filters)
        if not doc:
            return None
        doc['id'] = str(doc['_id'])
        for key in ['_id', 'id', 'client_id', 'pet_id']:
            if key in doc and isinstance(doc[key], ObjectId):
                doc[key] = str(doc[key])
        return InvoiceDB(**doc)

    async def get_multi(self, collection: AsyncIOMotorCollection, skip: int = 0, limit: int = 100, filters: dict = None) -> List[InvoiceDB]:
        filters = filters or {'status': True}
        cursor = collection.find(filters).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        result = []
        for doc in docs:
            doc['id'] = str(doc['_id'])
            for key in ['_id', 'id', 'client_id', 'pet_id']:
                if key in doc and isinstance(doc[key], ObjectId):
                    doc[key] = str(doc[key])
            result.append(InvoiceDB(**doc))
        return result

    async def update(self, collection: AsyncIOMotorCollection, invoice_id: str, invoice_update: InvoiceUpdate) -> Optional[InvoiceDB]:
        update_data = invoice_update.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        await collection.update_one({'_id': ObjectId(invoice_id)}, {'$set': update_data})
        return await self.get(collection, invoice_id)

    async def delete(self, collection: AsyncIOMotorCollection, invoice_id: str) -> bool:
        result = await collection.update_one({'_id': ObjectId(invoice_id)}, {'$set': {'status': False}})
        return result.modified_count > 0

invoices_crud = CRUDInvoice() 