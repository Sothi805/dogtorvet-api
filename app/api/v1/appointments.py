from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from datetime import datetime
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import appointment_crud
from app.schemas.appointment import AppointmentDB, AppointmentCreate, AppointmentUpdate
from app.schemas.user import UserDB, UserResponse
from app.schemas.base import APIResponse
from app.schemas.client import ClientResponse
from app.schemas.pet import PetResponse
from app.schemas.service import ServiceResponse
from bson import ObjectId
import traceback

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_appointments(
    appointment_status: Optional[str] = Query(None),
    appointment_date_from: Optional[str] = Query(None),
    appointment_date_to: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    pet_id: Optional[str] = Query(None),
    veterinarian_id: Optional[str] = Query(None),
    service_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_inactive: Optional[bool] = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=1000),
    include: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("appointment_date"),
    sort_order: Optional[str] = Query("asc"),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        print(f"📥 Incoming query parameters for get_appointments: {locals()}")
        collection = database.get_collection(COLLECTIONS["appointments"])
        filters = {"status": True}
        
        if appointment_status:
            filters["appointment_status"] = appointment_status
        if client_id:
            try:
                filters["client_id"] = ObjectId(client_id)
            except Exception:
                filters["client_id"] = client_id
        if pet_id:
            try:
                filters["pet_id"] = ObjectId(pet_id)
            except Exception:
                filters["pet_id"] = pet_id
        if veterinarian_id:
            try:
                filters["veterinarian_id"] = ObjectId(veterinarian_id)
            except Exception:
                filters["veterinarian_id"] = veterinarian_id
        if service_id:
            try:
                filters["service_id"] = ObjectId(service_id)
            except Exception:
                filters["service_id"] = service_id
        if appointment_date_from and appointment_date_to:
            from datetime import datetime
            start_date = datetime.fromisoformat(appointment_date_from.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(appointment_date_to.replace('Z', '+00:00'))
            filters["appointment_date"] = {"$gte": start_date, "$lte": end_date}
            print(f"🔍 Date filter: {appointment_date_from} to {appointment_date_to}")
            print(f"🔍 Converted dates: {start_date} to {end_date}")
        
        print(f"🔎 Filters for get_appointments: {filters}")
        
        # Debug: Check total appointments in database
        total_all_appointments = await collection.count_documents({})
        print(f"🔍 Total appointments in database (no filters): {total_all_appointments}")
        
        # Debug: Show a few appointments without filters
        sample_appointments = await collection.find({}).limit(3).to_list(length=None)
        print(f"🔍 Sample appointments in database:")
        for i, appt in enumerate(sample_appointments):
            print(f"  - {i+1}: {appt.get('appointment_date')} - {appt.get('appointment_status')} - {appt.get('client_id')}")
        
        # Calculate skip from page and per_page
        skip = (page - 1) * per_page
        limit = per_page
        
        # Get total count for pagination
        total_count = await collection.count_documents(filters)
        print(f"🔍 Total appointments found with filters: {total_count}")
        
        # Get appointments with pagination
        cursor = collection.find(filters)
        
        # Apply sorting
        sort_direction = 1 if sort_order == "asc" else -1
        cursor = cursor.sort(sort_by, sort_direction)
        
        # Apply pagination
        cursor = cursor.skip(skip).limit(limit)
        
        appointments = await cursor.to_list(length=None)
        print(f"🔎 Raw appointments from DB: {len(appointments)} appointments")
        
        # Debug: Show first few appointments
        for i, appt in enumerate(appointments[:3]):
            print(f"🔍 Appointment {i+1}: {appt.get('appointment_date')} - {appt.get('appointment_status')}")
        
        # Prepare related collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        services_collection = database.get_collection(COLLECTIONS["services"])
        
        appointments_response = []
        for appt in appointments:
            print(f"🔎 appt type: {type(appt)} value: {repr(appt)}")
            if hasattr(appt, 'model_dump'):
                data = appt.model_dump()
                print(f"🔎 data after model_dump: {data}")
            else:
                data = dict(appt)
                print(f"🔎 data after dict: {data}")
                data['id'] = str(data['_id'])
            
            # Convert ObjectId fields to str
            for key in ["client_id", "pet_id", "veterinarian_id", "service_id", "id"]:
                if key in data and isinstance(data[key], ObjectId):
                    data[key] = str(data[key])
            # Convert or remove _id
            if '_id' in data and isinstance(data['_id'], ObjectId):
                data['_id'] = str(data['_id'])
            # Populate related fields if include parameter is provided
            if include:
                include_fields = include.split(',')
                
                if 'client' in include_fields and data.get('client_id'):
                    client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
                    print(f"🔎 related client_doc: {repr(client_doc)}")
                    if client_doc:
                        client_doc['id'] = str(client_doc['_id'])
                        # Convert all ObjectId fields in client_doc to str
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
                    print(f"🔎 related pet_doc: {repr(pet_doc)}")
                    if pet_doc:
                        # Convert all ObjectId fields in pet_doc to str
                        for key in pet_doc:
                            if isinstance(pet_doc[key], ObjectId):
                                pet_doc[key] = str(pet_doc[key])
                        if '_id' in pet_doc and isinstance(pet_doc['_id'], ObjectId):
                            pet_doc['_id'] = str(pet_doc['_id'])
                        # Get species info
                        species_info = None
                        if pet_doc.get('species_id'):
                            species_collection = database.get_collection(COLLECTIONS["species"])
                            species_doc = await species_collection.find_one({'_id': ObjectId(pet_doc['species_id'])})
                            print(f"🔎 related species_doc: {repr(species_doc)}")
                            if species_doc:
                                if '_id' in species_doc and isinstance(species_doc['_id'], ObjectId):
                                    species_doc['_id'] = str(species_doc['_id'])
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
                
                if 'user' in include_fields and data.get('veterinarian_id'):
                    vet_doc = await users_collection.find_one({'_id': ObjectId(data['veterinarian_id'])})
                    print(f"🔎 related vet_doc: {repr(vet_doc)}")
                    if vet_doc:
                        # Convert all ObjectId fields in vet_doc to str
                        for key in vet_doc:
                            if isinstance(vet_doc[key], ObjectId):
                                vet_doc[key] = str(vet_doc[key])
                        if '_id' in vet_doc and isinstance(vet_doc['_id'], ObjectId):
                            vet_doc['_id'] = str(vet_doc['_id'])
                        data['user'] = {
                            'id': str(vet_doc['_id']),
                            'name': f"{vet_doc.get('first_name', '')} {vet_doc.get('last_name', '')}".strip(),
                            'email': vet_doc.get('email'),
                            'role': vet_doc.get('role'),
                        }
                
                if 'service' in include_fields and data.get('service_id'):
                    service_doc = await services_collection.find_one({'_id': ObjectId(data['service_id'])})
                    print(f"🔎 related service_doc: {repr(service_doc)}")
                    if service_doc:
                        # Convert all ObjectId fields in service_doc to str
                        for key in service_doc:
                            if isinstance(service_doc[key], ObjectId):
                                service_doc[key] = str(service_doc[key])
                        if '_id' in service_doc and isinstance(service_doc['_id'], ObjectId):
                            service_doc['_id'] = str(service_doc['_id'])
                        data['service'] = {
                            'id': str(service_doc['_id']),
                            'name': service_doc.get('name'),
                            'description': service_doc.get('description'),
                            'price': service_doc.get('price'),
                        }
            
            appointments_response.append(data)
        
        # Calculate pagination metadata
        last_page = (total_count + per_page - 1) // per_page
        from_item = skip + 1
        to_item = min(skip + len(appointments_response), total_count)
        
        # Build paginated response
        paginated_response = {
            "data": appointments_response,
            "meta": {
                "current_page": page,
                "from": from_item,
                "last_page": last_page,
                "per_page": per_page,
                "to": to_item,
                "total": total_count
            },
            "links": {
                "first": f"/api/v1/appointments?page=1&per_page={per_page}",
                "last": f"/api/v1/appointments?page={last_page}&per_page={per_page}",
                "prev": f"/api/v1/appointments?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/appointments?page={page+1}&per_page={per_page}" if page < last_page else None
            }
        }
        
        return APIResponse(success=True, message="Appointments retrieved successfully", data=paginated_response)
    except Exception as e:
        print(f"❌ Error in get_appointments: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get appointments: {str(e)}")

@router.get("/{appointment_id}", response_model=APIResponse)
async def get_appointment(
    appointment_id: str = Path(..., description="Appointment ID"),
    include: Optional[str] = Query(None),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        collection = database.get_collection(COLLECTIONS["appointments"])
        appointment_doc = await collection.find_one({"_id": ObjectId(appointment_id), "status": True})
        
        if not appointment_doc:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        if hasattr(appointment_doc, 'model_dump'):
            data = appointment_doc.model_dump()
            print(f"🔎 data after model_dump: {data}")
        else:
            data = dict(appointment_doc)
            print(f"🔎 data after dict: {data}")
        data['id'] = str(data['_id'])
        
        # Convert ObjectIds to strings
        for key in ["client_id", "pet_id", "veterinarian_id", "service_id", "id"]:
            if key in data and isinstance(data[key], ObjectId):
                data[key] = str(data[key])
        print(f"🔎 data after ObjectId-to-str: {data}")
        
        # Populate related fields if include parameter is provided
        if include:
            include_fields = include.split(',')
            clients_collection = database.get_collection(COLLECTIONS["clients"])
            pets_collection = database.get_collection(COLLECTIONS["pets"])
            users_collection = database.get_collection(COLLECTIONS["users"])
            services_collection = database.get_collection(COLLECTIONS["services"])
            
            if 'client' in include_fields and data.get('client_id'):
                client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
                if client_doc:
                    client_doc['id'] = str(client_doc['_id'])
                    # Convert all ObjectId fields in client_doc to str
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
                    # Convert all ObjectId fields in pet_doc to str
                    for key in pet_doc:
                        if isinstance(pet_doc[key], ObjectId):
                            pet_doc[key] = str(pet_doc[key])
                    if '_id' in pet_doc and isinstance(pet_doc['_id'], ObjectId):
                        pet_doc['_id'] = str(pet_doc['_id'])
                    # Get species info
                    species_info = None
                    if pet_doc.get('species_id'):
                        species_collection = database.get_collection(COLLECTIONS["species"])
                        species_doc = await species_collection.find_one({'_id': ObjectId(pet_doc['species_id'])})
                        if species_doc:
                            if '_id' in species_doc and isinstance(species_doc['_id'], ObjectId):
                                species_doc['_id'] = str(species_doc['_id'])
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
            
            if 'user' in include_fields and data.get('veterinarian_id'):
                vet_doc = await users_collection.find_one({'_id': ObjectId(data['veterinarian_id'])})
                if vet_doc:
                    # Convert all ObjectId fields in vet_doc to str
                    for key in vet_doc:
                        if isinstance(vet_doc[key], ObjectId):
                            vet_doc[key] = str(vet_doc[key])
                    if '_id' in vet_doc and isinstance(vet_doc['_id'], ObjectId):
                        vet_doc['_id'] = str(vet_doc['_id'])
                    data['user'] = {
                        'id': str(vet_doc['_id']),
                        'name': f"{vet_doc.get('first_name', '')} {vet_doc.get('last_name', '')}".strip(),
                        'email': vet_doc.get('email'),
                        'role': vet_doc.get('role'),
                    }
            
            if 'service' in include_fields and data.get('service_id'):
                service_doc = await services_collection.find_one({'_id': ObjectId(data['service_id'])})
                if service_doc:
                    # Convert all ObjectId fields in service_doc to str
                    for key in service_doc:
                        if isinstance(service_doc[key], ObjectId):
                            service_doc[key] = str(service_doc[key])
                    if '_id' in service_doc and isinstance(service_doc['_id'], ObjectId):
                        service_doc['_id'] = str(service_doc['_id'])
                    data['service'] = {
                        'id': str(service_doc['_id']),
                        'name': service_doc.get('name'),
                        'description': service_doc.get('description'),
                        'price': service_doc.get('price'),
                        'duration_minutes': service_doc.get('duration_minutes'),
                    }
        
        return APIResponse(success=True, message="Appointment retrieved successfully", data=data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_appointment: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get appointment: {str(e)}")

@router.post("/", response_model=APIResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        print("📥 Incoming appointment data:", appointment_data)
        collection = database.get_collection(COLLECTIONS["appointments"])
        
        # Validate that all referenced entities exist
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        services_collection = database.get_collection(COLLECTIONS["services"])
        
        # Check if client exists
        if not await clients_collection.find_one({"_id": ObjectId(appointment_data.client_id), "status": True}):
            raise HTTPException(status_code=400, detail="Client not found")
        
        # Check if pet exists
        if not await pets_collection.find_one({"_id": ObjectId(appointment_data.pet_id), "status": True}):
            raise HTTPException(status_code=400, detail="Pet not found")
        
        # Check if veterinarian exists
        if not await users_collection.find_one({"_id": ObjectId(appointment_data.veterinarian_id), "status": True}):
            raise HTTPException(status_code=400, detail="Veterinarian not found")
        
        # Check if service exists
        if not await services_collection.find_one({"_id": ObjectId(appointment_data.service_id), "status": True}):
            raise HTTPException(status_code=400, detail="Service not found")
        
        appointment_doc = appointment_data.model_dump() if hasattr(appointment_data, 'model_dump') else dict(appointment_data)
        print(f"🔎 appointment_doc after model_dump/dict: {appointment_doc}")
        appointment_doc["status"] = True
        from datetime import datetime
        now = datetime.utcnow()
        appointment_doc["created_at"] = now
        appointment_doc["updated_at"] = now
        # Convert string IDs to ObjectIds
        appointment_doc["client_id"] = ObjectId(appointment_data.client_id)
        appointment_doc["pet_id"] = ObjectId(appointment_data.pet_id)
        appointment_doc["veterinarian_id"] = ObjectId(appointment_data.veterinarian_id)
        appointment_doc["service_id"] = ObjectId(appointment_data.service_id)
        print("📄 Appointment doc to insert:", appointment_doc)
        
        result = await collection.insert_one(appointment_doc)
        appointment_doc["_id"] = result.inserted_id
        appointment_doc["id"] = str(result.inserted_id)
        for key in ["client_id", "pet_id", "veterinarian_id", "service_id"]:
            if key in appointment_doc and isinstance(appointment_doc[key], ObjectId):
                appointment_doc[key] = str(appointment_doc[key])
        # Convert or remove _id
        if '_id' in appointment_doc and isinstance(appointment_doc['_id'], ObjectId):
            appointment_doc['_id'] = str(appointment_doc['_id'])
        print(f"🔎 appointment_doc after ObjectId-to-str: {appointment_doc}")
        return APIResponse(success=True, message="Appointment created successfully", data=appointment_doc)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Exception: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")

@router.put("/{appointment_id}", response_model=APIResponse)
async def update_appointment(
    appointment_data: AppointmentUpdate,
    appointment_id: str = Path(..., description="Appointment ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        collection = database.get_collection(COLLECTIONS["appointments"])
        
        # Check if appointment exists
        existing_appointment = await collection.find_one({"_id": ObjectId(appointment_id), "status": True})
        if not existing_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Prepare update data
        update_data = appointment_data.model_dump(exclude_unset=True)
        from datetime import datetime
        update_data["updated_at"] = datetime.utcnow()
        
        # Update appointment
        await collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": update_data}
        )
        
        # Get updated appointment with related data
        updated_appointment = await collection.find_one({"_id": ObjectId(appointment_id)})
        updated_appointment["id"] = str(updated_appointment["_id"])
        
        # Include related data like in the get_appointments endpoint
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        services_collection = database.get_collection(COLLECTIONS["services"])
        
        # Add client data
        if "client_id" in updated_appointment:
            client = await clients_collection.find_one({"_id": ObjectId(updated_appointment["client_id"])})
            if client:
                updated_appointment["client"] = {
                    "id": str(client["_id"]),
                    "name": client.get("name", ""),
                    "email": client.get("email", ""),
                    "phone": client.get("phone", "")
                }
        
        # Add pet data
        if "pet_id" in updated_appointment:
            pet = await pets_collection.find_one({"_id": ObjectId(updated_appointment["pet_id"])})
            if pet:
                # Get species data
                species_collection = database.get_collection(COLLECTIONS["species"])
                species = None
                if "species_id" in pet:
                    species = await species_collection.find_one({"_id": ObjectId(pet["species_id"])})
                
                updated_appointment["pet"] = {
                    "id": str(pet["_id"]),
                    "name": pet.get("name", ""),
                    "species": {
                        "id": str(species["_id"]) if species else "",
                        "name": species.get("name", "") if species else ""
                    } if species else None
                }
        
        # Add service data
        if "service_id" in updated_appointment:
            service = await services_collection.find_one({"_id": ObjectId(updated_appointment["service_id"])})
            if service:
                updated_appointment["service"] = {
                    "id": str(service["_id"]),
                    "name": service.get("name", ""),
                    "price": service.get("price", 0),
                    "duration_minutes": service.get("duration_minutes", 30)
                }
        
        # Add user/veterinarian data
        if "veterinarian_id" in updated_appointment:
            user = await users_collection.find_one({"_id": ObjectId(updated_appointment["veterinarian_id"])})
            if user:
                updated_appointment["user"] = {
                    "id": str(user["_id"]),
                    "name": user.get("name", ""),
                    "role": user.get("role", "")
                }
        
        # Ensure all ObjectId fields are converted to strings
        def convert_objectids_to_strings(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, ObjectId):
                        obj[key] = str(value)
                    elif isinstance(value, dict):
                        convert_objectids_to_strings(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                convert_objectids_to_strings(item)
            return obj
        
        updated_appointment = convert_objectids_to_strings(updated_appointment)
        
        # Convert ObjectId fields to str
        for key in ["client_id", "pet_id", "veterinarian_id", "service_id"]:
            if key in updated_appointment and isinstance(updated_appointment[key], ObjectId):
                updated_appointment[key] = str(updated_appointment[key])
        
        # Also convert _id to str if it exists
        if "_id" in updated_appointment and isinstance(updated_appointment["_id"], ObjectId):
            updated_appointment["_id"] = str(updated_appointment["_id"])
        
        # Ensure all datetime fields are properly formatted
        if "created_at" in updated_appointment and isinstance(updated_appointment["created_at"], datetime):
            updated_appointment["created_at"] = updated_appointment["created_at"].isoformat()
        if "updated_at" in updated_appointment and isinstance(updated_appointment["updated_at"], datetime):
            updated_appointment["updated_at"] = updated_appointment["updated_at"].isoformat()
        
        return APIResponse(success=True, message="Appointment updated successfully", data=updated_appointment)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_appointment: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update appointment: {str(e)}")

@router.delete("/{appointment_id}", response_model=APIResponse)
async def delete_appointment(
    appointment_id: str = Path(..., description="Appointment ID"),
    current_user: UserDB = Depends(get_current_active_user)
):
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        collection = database.get_collection(COLLECTIONS["appointments"])
        
        # Check if appointment exists
        existing_appointment = await collection.find_one({"_id": ObjectId(appointment_id), "status": True})
        if not existing_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Soft delete
        await collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": False}}
        )
        
        return APIResponse(success=True, message="Appointment deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in delete_appointment: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete appointment: {str(e)}") 