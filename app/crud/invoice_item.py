from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from app.schemas.invoice import InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemDB

class CRUDInvoiceItem:
    async def create(self, collection: AsyncIOMotorCollection, item_data: InvoiceItemCreate, 
                    services_collection: AsyncIOMotorCollection = None, 
                    products_collection: AsyncIOMotorCollection = None) -> InvoiceItemDB:
        now = datetime.utcnow()
        item_doc = item_data.model_dump(exclude_unset=True)
        
        # Calculate net price
        item_doc['net_price'] = item_data.unit_price * item_data.quantity * (1 - item_data.discount_percent / 100)
        
        # Capture historical snapshot of service/product data
        if item_data.service_id and services_collection is not None:
            try:
                service_doc = await services_collection.find_one({'_id': ObjectId(item_data.service_id)})
                if service_doc:
                    # Store snapshot of service data at time of creation
                    item_doc['original_service_data'] = {
                        'id': str(service_doc['_id']),
                        'name': service_doc.get('name', ''),
                        'description': service_doc.get('description', ''),
                        'price': service_doc.get('price', 0.0),
                        'category': service_doc.get('category', ''),
                        'status': service_doc.get('status', True),
                        'snapshot_date': now.isoformat()
                    }
            except Exception as e:
                print(f"⚠️ Warning: Could not capture service snapshot: {e}")
        
        if item_data.product_id and products_collection is not None:
            try:
                product_doc = await products_collection.find_one({'_id': ObjectId(item_data.product_id)})
                if product_doc:
                    # Store snapshot of product data at time of creation
                    item_doc['original_product_data'] = {
                        'id': str(product_doc['_id']),
                        'name': product_doc.get('name', ''),
                        'description': product_doc.get('description', ''),
                        'price': product_doc.get('price', 0.0),
                        'category': product_doc.get('category', ''),
                        'stock_quantity': product_doc.get('stock_quantity', 0),
                        'status': product_doc.get('status', True),
                        'snapshot_date': now.isoformat()
                    }
            except Exception as e:
                print(f"⚠️ Warning: Could not capture product snapshot: {e}")
        
        item_doc['created_at'] = now
        item_doc['updated_at'] = now
        
        # Insert item
        result = await collection.insert_one(item_doc)
        item_doc['_id'] = result.inserted_id
        item_doc['id'] = str(result.inserted_id)
        
        # Convert ObjectId fields to str
        for key in ['_id', 'id', 'invoice_id', 'service_id', 'product_id']:
            if key in item_doc and isinstance(item_doc[key], ObjectId):
                item_doc[key] = str(item_doc[key])
        
        return InvoiceItemDB(**item_doc)

    async def get(self, collection: AsyncIOMotorCollection, item_id: str) -> Optional[InvoiceItemDB]:
        doc = await collection.find_one({'_id': ObjectId(item_id)})
        if not doc:
            return None
        doc['id'] = str(doc['_id'])
        for key in ['_id', 'id', 'invoice_id', 'service_id', 'product_id']:
            if key in doc and isinstance(doc[key], ObjectId):
                doc[key] = str(doc[key])
        return InvoiceItemDB(**doc)

    async def get_by_invoice(self, collection: AsyncIOMotorCollection, invoice_id: str) -> List[InvoiceItemDB]:
        # Try both ObjectId and string formats for invoice_id
        cursor = collection.find({'invoice_id': ObjectId(invoice_id)})
        docs = await cursor.to_list(length=None)
        
        # If no items found with ObjectId, try with string
        if not docs:
            cursor = collection.find({'invoice_id': invoice_id})
            docs = await cursor.to_list(length=None)
        
        result = []
        for doc in docs:
            doc['id'] = str(doc['_id'])
            for key in ['_id', 'id', 'invoice_id', 'service_id', 'product_id']:
                if key in doc and isinstance(doc[key], ObjectId):
                    doc[key] = str(doc[key])
            result.append(InvoiceItemDB(**doc))
        return result

    async def update(self, collection: AsyncIOMotorCollection, item_id: str, item_update: InvoiceItemUpdate) -> Optional[InvoiceItemDB]:
        update_data = item_update.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        # Recalculate net price if price, quantity, or discount changed
        if any(key in update_data for key in ['unit_price', 'quantity', 'discount_percent']):
            current_item = await self.get(collection, item_id)
            if current_item:
                unit_price = update_data.get('unit_price', current_item.unit_price)
                quantity = update_data.get('quantity', current_item.quantity)
                discount_percent = update_data.get('discount_percent', current_item.discount_percent)
                update_data['net_price'] = unit_price * quantity * (1 - discount_percent / 100)
        
        await collection.update_one({'_id': ObjectId(item_id)}, {'$set': update_data})
        return await self.get(collection, item_id)

    async def delete(self, collection: AsyncIOMotorCollection, item_id: str) -> bool:
        result = await collection.delete_one({'_id': ObjectId(item_id)})
        return result.deleted_count > 0

invoice_items_crud = CRUDInvoiceItem() 