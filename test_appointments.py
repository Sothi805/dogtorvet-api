import asyncio
from app.db.database import database, COLLECTIONS

async def test_appointments():
    try:
        collection = database.get_collection(COLLECTIONS['appointments'])
        count = await collection.count_documents({})
        print(f'Total appointments: {count}')
        
        if count > 0:
            appointments = await collection.find({}).limit(3).to_list(length=None)
            print('Sample appointments:')
            for i, apt in enumerate(appointments):
                print(f'  - {i+1}: {apt.get("appointment_date")} - {apt.get("appointment_status")} - {apt.get("client_id")}')
        else:
            print('No appointments found in database')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_appointments()) 