"""
Database Index Configuration
Defines unique constraints and indexes for MongoDB collections
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING
from utils.logging import logger


async def create_indexes(db: AsyncIOMotorDatabase):
    """Create all database indexes and unique constraints"""
    
    # Users collection - unique email
    users_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
        IndexModel([("phone", ASCENDING)], sparse=True, name="phone_index")  # sparse allows null values
    ]
    await db.users.create_indexes(users_indexes)
    logger.info("✅ Created indexes for users collection")
    
    # Clients collection - unique phone_number
    clients_indexes = [
        IndexModel([("phone_number", ASCENDING)], unique=True, name="phone_number_unique"),
        IndexModel([("name", ASCENDING)], name="name_index"),
        IndexModel([("status", ASCENDING)], name="status_index")
    ]
    await db.clients.create_indexes(clients_indexes)
    logger.info("✅ Created indexes for clients collection")
    
    # Invoices collection - unique invoice_number
    invoices_indexes = [
        IndexModel([("invoice_number", ASCENDING)], unique=True, name="invoice_number_unique"),
        IndexModel([("client_id", ASCENDING)], name="client_id_index"),
        IndexModel([("payment_status", ASCENDING)], name="payment_status_index"),
        IndexModel([("invoice_date", ASCENDING)], name="invoice_date_index")
    ]
    await db.invoices.create_indexes(invoices_indexes)
    logger.info("✅ Created indexes for invoices collection")
    
    # Products collection - unique SKU (optional)
    products_indexes = [
        IndexModel([("sku", ASCENDING)], unique=True, sparse=True, name="sku_unique"),  # sparse allows null
        IndexModel([("name", ASCENDING)], name="name_index"),
        IndexModel([("status", ASCENDING)], name="status_index")
    ]
    await db.products.create_indexes(products_indexes)
    logger.info("✅ Created indexes for products collection")
    
    # Species collection - unique name (case insensitive)
    species_indexes = [
        IndexModel([("name", ASCENDING)], unique=True, name="name_unique", 
                  collation={"locale": "en", "strength": 2})  # case insensitive
    ]
    await db.species.create_indexes(species_indexes)
    logger.info("✅ Created indexes for species collection")
    
    # Breeds collection - composite unique (name + species_id)
    breeds_indexes = [
        IndexModel([("name", ASCENDING), ("species_id", ASCENDING)], 
                  unique=True, name="name_species_unique"),
        IndexModel([("species_id", ASCENDING)], name="species_id_index")
    ]
    await db.breeds.create_indexes(breeds_indexes)
    logger.info("✅ Created indexes for breeds collection")
    
    # Audit logs collection - indexes for query performance
    audit_logs_indexes = [
        IndexModel([("action", ASCENDING)], name="action_index"),
        IndexModel([("collection_name", ASCENDING)], name="collection_name_index"),
        IndexModel([("user_id", ASCENDING)], name="user_id_index"),
        IndexModel([("created_at", ASCENDING)], name="created_at_index"),
        IndexModel([("document_id", ASCENDING)], name="document_id_index"),
        IndexModel([("action", ASCENDING), ("created_at", ASCENDING)], name="action_date_compound")
    ]
    await db.audit_logs.create_indexes(audit_logs_indexes)
    logger.info("✅ Created indexes for audit_logs collection")
    
    # Common indexes for better query performance
    common_collections = ["pets", "appointments", "services", "invoice_items", "allergies", "vaccinations"]
    for collection_name in common_collections:
        common_indexes = [
            IndexModel([("status", ASCENDING)], name="status_index"),
            IndexModel([("created_at", ASCENDING)], name="created_at_index"),
            IndexModel([("updated_at", ASCENDING)], name="updated_at_index")
        ]
        await db[collection_name].create_indexes(common_indexes)
        logger.info(f"✅ Created indexes for {collection_name} collection")
    
    logger.success("✅ All database indexes created successfully!")


async def drop_all_indexes(db: AsyncIOMotorDatabase):
    """Drop all custom indexes (use with caution!)"""
    collections = await db.list_collection_names()
    
    for collection_name in collections:
        # Get all indexes
        indexes = await db[collection_name].list_indexes().to_list(None)
        
        # Drop all except _id index
        for index in indexes:
            if index["name"] != "_id_":
                await db[collection_name].drop_index(index["name"])
                logger.warning(f"Dropped index {index['name']} from {collection_name}")
    
    logger.warning("⚠️  All custom indexes dropped!") 