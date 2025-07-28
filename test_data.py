import asyncio
from app.db.database import database, COLLECTIONS
from datetime import datetime
from bson import ObjectId

async def test_data():
    try:
        # Check available data
        clients_collection = database.get_collection(COLLECTIONS['clients'])
        pets_collection = database.get_collection(COLLECTIONS['pets'])
        users_collection = database.get_collection(COLLECTIONS['users'])
        services_collection = database.get_collection(COLLECTIONS['services'])
        appointments_collection = database.get_collection(COLLECTIONS['appointments'])
        
        # Count existing data
        clients_count = await clients_collection.count_documents({"status": True})
        pets_count = await pets_collection.count_documents({"status": True})
        users_count = await users_collection.count_documents({"status": True})
        services_count = await services_collection.count_documents({"status": True})
        appointments_count = await appointments_collection.count_documents({})
        
        print(f'Available data:')
        print(f'  - Clients: {clients_count}')
        print(f'  - Pets: {pets_count}')
        print(f'  - Users: {users_count}')
        print(f'  - Services: {services_count}')
        print(f'  - Appointments: {appointments_count}')
        
        # If we have data, create a test appointment
        if clients_count > 0 and pets_count > 0 and users_count > 0 and services_count > 0:
            # Get first available data
            client = await clients_collection.find_one({"status": True})
            pet = await pets_collection.find_one({"status": True})
            user = await users_collection.find_one({"status": True})
            service = await services_collection.find_one({"status": True})
            
            if client and pet and user and service:
                print(f'\nCreating test appointment...')
                
                # Create test appointment for June 5, 2025
                test_appointment = {
                    "client_id": client["_id"],
                    "pet_id": pet["_id"],
                    "veterinarian_id": user["_id"],
                    "service_id": service["_id"],
                    "appointment_date": datetime(2025, 6, 5, 10, 0, 0),  # June 5, 2025 at 10:00 AM
                    "duration_minutes": 30,
                    "appointment_status": "scheduled",
                    "notes": "Test appointment for calendar",
                    "status": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = await appointments_collection.insert_one(test_appointment)
                print(f'Test appointment created with ID: {result.inserted_id}')
                
                # Verify it was created
                new_count = await appointments_collection.count_documents({})
                print(f'Total appointments after creation: {new_count}')
                
            else:
                print('Missing required data to create test appointment')
        else:
            print('Not enough data to create test appointment')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_data()) 