from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import pet_crud
from app.crud.allergy import allergy_crud
from app.crud.allergy_type import allergy_type_crud
from app.schemas.pet import PetDB, PetCreate, PetUpdate, PetResponse
from app.schemas.allergy import AllergyCreate, AllergyDB, AllergyResponse
from app.schemas.user import UserDB
from app.schemas.base import APIResponse
import traceback
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_pets(
    status: Optional[str] = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=1000),
    client_id: Optional[str] = Query(None),
    species_id: Optional[str] = Query(None),
    breed_id: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    include: Optional[str] = Query(None),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get all pets with optional filters."""
    try:
        collection = database.get_collection(COLLECTIONS["pets"])
        filters = {}
        if status and status != "all":
            if status == "active":
                filters["status"] = True
            elif status == "inactive":
                filters["status"] = False
        if client_id:
            try:
                filters["client_id"] = ObjectId(client_id)
            except Exception:
                filters["client_id"] = client_id  # fallback, but ObjectId is preferred
        # Debug print
        print("🐾 PETS FILTER:", filters)
        
        # Calculate skip from page and per_page
        skip = (page - 1) * per_page
        limit = per_page
        
        # Get total count for pagination
        total_count = await collection.count_documents(filters)
        
        pets = await pet_crud.get_multi(collection, skip=skip, limit=limit, filters=filters)
        print("🐾 PETS FOUND:", len(pets))
        
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        species_collection = database.get_collection(COLLECTIONS["species"])
        breeds_collection = database.get_collection(COLLECTIONS["breeds"])
        pets_response = []
        for pet in pets:
            data = pet.model_dump()
            data['id'] = str(pet.id)
            for key in ['species_id', 'breed_id', 'client_id']:
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
            # Fetch client info
            client = None
            if include and 'client' in include.split(','):
                clients_collection = database.get_collection(COLLECTIONS["clients"])
                if data.get('client_id'):
                    client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
                    if client_doc:
                        client_doc['id'] = str(client_doc['_id'])
                        client = {
                            'id': client_doc['id'],
                            'name': client_doc.get('name'),
                            'gender': client_doc.get('gender'),
                            'phone_number': client_doc.get('phone_number'),
                            'other_contact_info': client_doc.get('other_contact_info'),
                            'status': client_doc.get('status'),
                            'created_at': client_doc.get('created_at'),
                            'updated_at': client_doc.get('updated_at'),
                        }
            data['client'] = client
            
            # Fetch species info
            species = None
            if include and 'species' in include.split(','):
                species_collection = database.get_collection(COLLECTIONS["species"])
                if data.get('species_id'):
                    species_doc = await species_collection.find_one({'_id': ObjectId(data['species_id'])})
                    if species_doc:
                        species = {
                            'id': str(species_doc['_id']),
                            'name': species_doc.get('name'),
                            'description': species_doc.get('description'),
                            'created_at': species_doc.get('created_at'),
                            'updated_at': species_doc.get('updated_at'),
                            'status': species_doc.get('status'),
                        }
            data['species'] = species
            
            # Fetch breed info
            breed = None
            if include and 'breed' in include.split(','):
                breeds_collection = database.get_collection(COLLECTIONS["breeds"])
                if data.get('breed_id'):
                    breed_doc = await breeds_collection.find_one({'_id': ObjectId(data['breed_id'])})
                    if breed_doc:
                        breed = {
                            'id': str(breed_doc['_id']),
                            'name': breed_doc.get('name'),
                            'species_id': str(breed_doc.get('species_id')) if breed_doc.get('species_id') else None,
                            'created_at': breed_doc.get('created_at'),
                            'updated_at': breed_doc.get('updated_at'),
                            'status': breed_doc.get('status'),
                        }
            data['breed'] = breed
            
            # Handle allergies - either populate full objects or remove from response
            if include and 'allergies' in include.split(','):
                allergies = []
                allergies_collection = database.get_collection(COLLECTIONS["allergies"])
                if data.get('allergies'):
                    for allergy_id in data['allergies']:
                        allergy_doc = await allergies_collection.find_one({'_id': ObjectId(allergy_id)})
                        if allergy_doc:
                            allergies.append({
                                'id': str(allergy_doc['_id']),
                                'name': allergy_doc.get('name'),
                                'description': allergy_doc.get('description'),
                                'created_at': allergy_doc.get('created_at'),
                                'updated_at': allergy_doc.get('updated_at'),
                                'status': allergy_doc.get('status'),
                            })
                    data['allergies'] = allergies
            else:
                # Remove allergies from response if not requested
                data.pop('allergies', None)
            
            # Handle vaccinations - either populate full objects or remove from response
            if include and 'vaccinations' in include.split(','):
                vaccinations = []
                vaccinations_collection = database.get_collection(COLLECTIONS["vaccinations"])
                if data.get('vaccinations'):
                    for vaccination_record in data['vaccinations']:
                        vaccination_id = vaccination_record.get('vaccination_id')
                        if vaccination_id:
                            vaccination_doc = await vaccinations_collection.find_one({'_id': ObjectId(vaccination_id)})
                            if vaccination_doc:
                                vaccination_detail = {
                                    'id': str(vaccination_doc['_id']),
                                    'name': vaccination_doc.get('name'),
                                    'description': vaccination_doc.get('description'),
                                    'created_at': vaccination_doc.get('created_at'),
                                    'updated_at': vaccination_doc.get('updated_at'),
                                    'status': vaccination_doc.get('status'),
                                }
                                # Merge vaccination details with the record
                                vaccination_record.update(vaccination_detail)
                        vaccinations.append(vaccination_record)
                    data['vaccinations'] = vaccinations
            else:
                # Remove vaccinations from response if not requested
                data.pop('vaccinations', None)
            pets_response.append(PetResponse(**data))
        
        # Calculate pagination metadata
        last_page = (total_count + per_page - 1) // per_page
        from_item = skip + 1
        to_item = min(skip + len(pets_response), total_count)
        
        # Build paginated response
        paginated_response = {
            "data": pets_response,
            "meta": {
                "current_page": page,
                "from": from_item,
                "last_page": last_page,
                "per_page": per_page,
                "to": to_item,
                "total": total_count
            },
            "links": {
                "first": f"/api/v1/pets?page=1&per_page={per_page}",
                "last": f"/api/v1/pets?page={last_page}&per_page={per_page}",
                "prev": f"/api/v1/pets?page={page-1}&per_page={per_page}" if page > 1 else None,
                "next": f"/api/v1/pets?page={page+1}&per_page={per_page}" if page < last_page else None
            }
        }
        
        return APIResponse(success=True, message="Pets retrieved successfully", data=paginated_response)
    except Exception as e:
        print(f"❌ Error in get_pets: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get pets: {str(e)}")

@router.post("/", response_model=APIResponse)
async def create_pet(
    pet_create: PetCreate,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Create a new pet."""
    try:
        collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.create(collection, pet_create)
        data = pet.model_dump()
        data['id'] = str(pet.id)
        for key in ['species_id', 'breed_id', 'client_id']:
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        # Fetch client info
        client = None
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        if data.get('client_id'):
            client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
            if client_doc:
                client_doc['id'] = str(client_doc['_id'])
                client = {
                    'id': client_doc['id'],
                    'name': client_doc.get('name'),
                    'gender': client_doc.get('gender'),
                    'phone_number': client_doc.get('phone_number'),
                    'other_contact_info': client_doc.get('other_contact_info'),
                    'status': client_doc.get('status'),
                    'created_at': client_doc.get('created_at'),
                    'updated_at': client_doc.get('updated_at'),
                }
        data['client'] = client
        # Fetch species info
        species = None
        species_collection = database.get_collection(COLLECTIONS["species"])
        if data.get('species_id'):
            species_doc = await species_collection.find_one({'_id': ObjectId(data['species_id'])})
            if species_doc:
                species = {
                    'id': str(species_doc['_id']),
                    'name': species_doc.get('name'),
                    'description': species_doc.get('description'),
                    'created_at': species_doc.get('created_at'),
                    'updated_at': species_doc.get('updated_at'),
                    'status': species_doc.get('status'),
                }
        data['species'] = species
        # Fetch breed info
        breed = None
        breeds_collection = database.get_collection(COLLECTIONS["breeds"])
        if data.get('breed_id'):
            breed_doc = await breeds_collection.find_one({'_id': ObjectId(data['breed_id'])})
            if breed_doc:
                breed = {
                    'id': str(breed_doc['_id']),
                    'name': breed_doc.get('name'),
                    'species_id': str(breed_doc.get('species_id')) if breed_doc.get('species_id') else None,
                    'created_at': breed_doc.get('created_at'),
                    'updated_at': breed_doc.get('updated_at'),
                    'status': breed_doc.get('status'),
                }
        data['breed'] = breed
        return APIResponse(success=True, message="Pet created successfully", data=PetResponse(**data))
    except Exception as e:
        print(f"❌ Error in create_pet: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create pet: {str(e)}")

@router.get("/{pet_id}", response_model=APIResponse)
async def get_pet(
    pet_id: str,
    include: Optional[str] = Query(None),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get a specific pet."""
    try:
        collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.get(collection, pet_id)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        data = pet.model_dump()
        data['id'] = str(pet.id)
        
        # Debug: Log the original data structure
        print(f"🔍 Original data from pet.model_dump():")
        print(f"🔍 Allergies: {data.get('allergies')}")
        print(f"🔍 Vaccinations: {data.get('vaccinations')}")
        
        for key in ['species_id', 'breed_id', 'client_id']:
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        # Fetch client info
        client = None
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        if data.get('client_id'):
            client_doc = await clients_collection.find_one({'_id': ObjectId(data['client_id'])})
            if client_doc:
                client_doc['id'] = str(client_doc['_id'])
                client = {
                    'id': client_doc['id'],
                    'name': client_doc.get('name'),
                    'gender': client_doc.get('gender'),
                    'phone_number': client_doc.get('phone_number'),
                    'other_contact_info': client_doc.get('other_contact_info'),
                    'status': client_doc.get('status'),
                    'created_at': client_doc.get('created_at'),
                    'updated_at': client_doc.get('updated_at'),
                }
        data['client'] = client
        # Fetch species info
        species = None
        species_collection = database.get_collection(COLLECTIONS["species"])
        if data.get('species_id'):
            species_doc = await species_collection.find_one({'_id': ObjectId(data['species_id'])})
            if species_doc:
                species = {
                    'id': str(species_doc['_id']),
                    'name': species_doc.get('name'),
                    'description': species_doc.get('description'),
                    'created_at': species_doc.get('created_at'),
                    'updated_at': species_doc.get('updated_at'),
                    'status': species_doc.get('status'),
                }
        data['species'] = species
        # Fetch breed info
        breed = None
        breeds_collection = database.get_collection(COLLECTIONS["breeds"])
        if data.get('breed_id'):
            breed_doc = await breeds_collection.find_one({'_id': ObjectId(data['breed_id'])})
            if breed_doc:
                breed = {
                    'id': str(breed_doc['_id']),
                    'name': breed_doc.get('name'),
                    'species_id': str(breed_doc.get('species_id')) if breed_doc.get('species_id') else None,
                    'created_at': breed_doc.get('created_at'),
                    'updated_at': breed_doc.get('updated_at'),
                    'status': breed_doc.get('status'),
                }
        data['breed'] = breed
        
        # Handle allergies if requested
        if include and 'allergies' in include.split(','):
            allergies_collection = database.get_collection(COLLECTIONS["allergies"])
            allergies = []
            if data.get('allergies'):
                for allergy_id in data['allergies']:
                    try:
                        allergy_doc = await allergies_collection.find_one({'_id': ObjectId(allergy_id)})
                        if allergy_doc:
                            allergies.append({
                                'id': str(allergy_doc['_id']),
                                'name': allergy_doc.get('name'),
                                'description': allergy_doc.get('description'),
                                'status': allergy_doc.get('status', True)
                            })
                    except Exception as e:
                        print(f"❌ Error processing allergy {allergy_id}: {e}")
                        continue
            data['allergies'] = allergies
        else:
            # If allergies not requested, ensure it's an empty list
            data['allergies'] = []
        
        # Handle vaccinations if requested
        if include and 'vaccinations' in include.split(','):
            vaccinations_collection = database.get_collection(COLLECTIONS["vaccinations"])
            vaccinations = []
            if data.get('vaccinations'):
                for vaccination_record in data['vaccinations']:
                    try:
                        vaccination_id = vaccination_record.get('vaccination_id')
                        if vaccination_id:
                            vaccination_doc = await vaccinations_collection.find_one({'_id': ObjectId(vaccination_id)})
                            if vaccination_doc:
                                vaccination_detail = {
                                    'id': str(vaccination_doc['_id']),
                                    'name': vaccination_doc.get('name'),
                                    'description': vaccination_doc.get('description'),
                                    'vaccination_date': vaccination_record.get('vaccination_date'),
                                    'next_due_date': vaccination_record.get('next_due_date'),
                                    'status': vaccination_doc.get('status', True)
                                }
                                vaccinations.append(vaccination_detail)
                    except Exception as e:
                        print(f"❌ Error processing vaccination {vaccination_record}: {e}")
                        continue
            data['vaccinations'] = vaccinations
        else:
            # If vaccinations not requested, ensure it's an empty list
            data['vaccinations'] = []
        
        # Ensure we always have the correct structure for PetResponse
        # Remove any raw allergy IDs or vaccination records that might still be in the data
        if 'allergies' not in data or not isinstance(data['allergies'], list):
            data['allergies'] = []
        if 'vaccinations' not in data or not isinstance(data['vaccinations'], list):
            data['vaccinations'] = []
        
        # Debug: Log the data structure before validation
        print(f"🔍 Data structure before PetResponse validation:")
        print(f"🔍 Allergies: {data.get('allergies')}")
        print(f"🔍 Vaccinations: {data.get('vaccinations')}")
        
        try:
            return APIResponse(success=True, message="Pet retrieved successfully", data=PetResponse(**data))
        except Exception as validation_error:
            print(f"❌ PetResponse validation error: {validation_error}")
            print(f"🔍 Full data structure: {data}")
            # Return a simplified response without the problematic fields
            safe_data = {k: v for k, v in data.items() if k not in ['allergies', 'vaccinations']}
            safe_data['allergies'] = []
            safe_data['vaccinations'] = []
            return APIResponse(success=True, message="Pet retrieved successfully", data=PetResponse(**safe_data))
        
    except Exception as e:
        print(f"❌ Error in get_pet: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get pet: {str(e)}")

@router.put("/{pet_id}", response_model=APIResponse)
async def update_pet(
    pet_id: str,
    pet_update: PetUpdate,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Update a pet."""
    try:
        collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.update(collection, pet_id, pet_update)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        data = pet.model_dump()
        data['id'] = str(pet.id)
        for key in ['species_id', 'breed_id', 'client_id']:
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return APIResponse(success=True, message="Pet updated successfully", data=PetResponse(**data))
    except Exception as e:
        print(f"❌ Error in update_pet: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update pet: {str(e)}")

@router.delete("/{pet_id}", response_model=APIResponse)
async def delete_pet(
    pet_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Delete a pet."""
    try:
        collection = database.get_collection(COLLECTIONS["pets"])
        success = await pet_crud.delete(collection, pet_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        return APIResponse(success=True, message="Pet deleted successfully", data=None)
    except Exception as e:
        print(f"❌ Error in delete_pet: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete pet: {str(e)}")

@router.post("/{pet_id}/allergies", response_model=APIResponse)
async def add_pet_allergy(
    pet_id: str,
    allergy_data: dict,  # Changed from AllergyCreate to dict to accept {allergy_id: string}
    current_user: UserDB = Depends(get_current_active_user)
):
    """Add an allergy to a pet."""
    try:
        # Verify pet exists
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.get(pets_collection, pet_id)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        
        # Get allergy_id from request
        allergy_id = allergy_data.get("allergy_id")
        if not allergy_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="allergy_id is required")
        
        # Verify allergy type exists
        allergies_collection = database.get_collection(COLLECTIONS["allergies"])
        print(f"🔍 Looking for allergy type with ID: {allergy_id}")
        print(f"🔍 ObjectId valid: {ObjectId.is_valid(allergy_id)}")
        
        # First, let's check what's actually in the collection
        all_allergies = await allergies_collection.find({}).to_list(length=None)
        print(f"🔍 All allergies in collection: {len(all_allergies)}")
        for allergy in all_allergies:
            print(f"🔍 Allergy: {allergy.get('_id')} - {allergy.get('name')} - {allergy.get('description', 'No description')}")
        
        # Try to find the specific allergy
        try:
            allergy_doc = await allergies_collection.find_one({"_id": ObjectId(allergy_id)})
            print(f"🔍 Direct MongoDB query result: {allergy_doc}")
            if allergy_doc:
                print(f"🔍 Allergy document fields: {list(allergy_doc.keys())}")
        except Exception as e:
            print(f"🔍 Error in direct query: {e}")
        
        # Try the CRUD method first
        allergy_type = await allergy_type_crud.get(allergies_collection, allergy_id)
        print(f"🔍 Found allergy type via CRUD: {allergy_type}")
        
        # If CRUD method fails, try direct query and create a simple object
        if not allergy_type:
            print(f"🔍 CRUD method failed, trying direct query...")
            allergy_doc = await allergies_collection.find_one({"_id": ObjectId(allergy_id)})
            if allergy_doc:
                print(f"🔍 Found allergy via direct query: {allergy_doc}")
                # Create a simple allergy type object with the required fields
                allergy_type = type('AllergyType', (), {
                    'id': allergy_doc['_id'],
                    'name': allergy_doc.get('name', ''),
                    'description': allergy_doc.get('description', ''),
                    'created_at': allergy_doc.get('created_at'),
                    'updated_at': allergy_doc.get('updated_at'),
                    'status': allergy_doc.get('status', True)
                })()
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy type not found")
        
        # Check if this allergy is already assigned to this pet
        # We'll store this as a simple relationship in the pet document
        pet_data = pet.model_dump()
        pet_allergies = pet_data.get("allergies", [])
        
        # Check if allergy is already assigned
        if allergy_id in pet_allergies:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This allergy is already assigned to this pet")
        
        # Add allergy to pet's allergies list
        pet_allergies.append(allergy_id)
        pet_data["allergies"] = pet_allergies
        pet_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the pet document
        await pets_collection.update_one(
            {"_id": ObjectId(pet_id)},
            {"$set": {"allergies": pet_allergies, "updated_at": pet_data["updated_at"]}}
        )
        
        return APIResponse(success=True, message="Allergy added to pet successfully", data={
            "pet_id": pet_id,
            "allergy_id": allergy_id,
            "allergy_name": allergy_type.name
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in add_pet_allergy: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to add allergy to pet: {str(e)}")

@router.delete("/{pet_id}/allergies/{allergy_id}", response_model=APIResponse)
async def remove_pet_allergy(
    pet_id: str,
    allergy_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Remove an allergy from a pet."""
    try:
        # Verify pet exists
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.get(pets_collection, pet_id)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        
        # Get pet data and allergies
        pet_data = pet.model_dump()
        pet_allergies = pet_data.get("allergies", [])
        
        # Check if allergy is assigned to this pet
        if allergy_id not in pet_allergies:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found on this pet")
        
        # Remove allergy from pet's allergies list
        pet_allergies = [aid for aid in pet_allergies if aid != allergy_id]
        pet_data["allergies"] = pet_allergies
        pet_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the pet document
        await pets_collection.update_one(
            {"_id": ObjectId(pet_id)},
            {"$set": {"allergies": pet_allergies, "updated_at": pet_data["updated_at"]}}
        )
        
        return APIResponse(success=True, message="Allergy removed from pet successfully", data=None)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in remove_pet_allergy: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to remove allergy from pet: {str(e)}")


@router.post("/{pet_id}/vaccinations", response_model=APIResponse)
async def add_pet_vaccination(
    pet_id: str,
    vaccination_data: dict,  # Expects {"vaccination_id": "...", "vaccination_date": "...", "next_due_date": "..."}
    current_user: UserDB = Depends(get_current_active_user)
):
    """Add a vaccination to a pet."""
    try:
        # Verify pet exists
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.get(pets_collection, pet_id)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        
        # Get vaccination_id from request
        vaccination_id = vaccination_data.get("vaccination_id")
        vaccination_date = vaccination_data.get("vaccination_date")
        next_due_date = vaccination_data.get("next_due_date")
        
        if not vaccination_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vaccination_id is required")
        
        # Verify vaccination type exists
        vaccinations_collection = database.get_collection(COLLECTIONS["vaccinations"])
        print(f"🔍 Looking for vaccination type with ID: {vaccination_id}")
        print(f"🔍 ObjectId valid: {ObjectId.is_valid(vaccination_id)}")
        
        # First, let's check what's actually in the collection
        all_vaccinations = await vaccinations_collection.find({}).to_list(length=None)
        print(f"🔍 All vaccinations in collection: {len(all_vaccinations)}")
        for vaccination in all_vaccinations:
            print(f"🔍 Vaccination: {vaccination.get('_id')} - {vaccination.get('name')} - {vaccination.get('description', 'No description')}")
        
        # Try direct query first
        vaccination_doc = await vaccinations_collection.find_one({"_id": ObjectId(vaccination_id)})
        if vaccination_doc:
            print(f"🔍 Found vaccination via direct query: {vaccination_doc}")
            vaccination_type = type('VaccinationType', (), {
                'id': vaccination_doc['_id'],
                'name': vaccination_doc.get('name', ''),
                'description': vaccination_doc.get('description', ''),
                'created_at': vaccination_doc.get('created_at'),
                'updated_at': vaccination_doc.get('updated_at'),
                'status': vaccination_doc.get('status', True)
            })()
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination type not found")
        
        # Get pet data and vaccinations
        pet_data = pet.model_dump()
        pet_vaccinations = pet_data.get("vaccinations", [])
        
        # Check if this vaccination is already assigned to this pet
        existing_vaccination = next((v for v in pet_vaccinations if v.get("vaccination_id") == vaccination_id), None)
        if existing_vaccination:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This vaccination is already assigned to this pet")
        
        # Add vaccination to pet's vaccinations list
        new_vaccination = {
            "vaccination_id": vaccination_id,
            "vaccination_date": vaccination_date,
            "next_due_date": next_due_date,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        pet_vaccinations.append(new_vaccination)
        pet_data["vaccinations"] = pet_vaccinations
        pet_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the pet document
        await pets_collection.update_one(
            {"_id": ObjectId(pet_id)},
            {"$set": {"vaccinations": pet_vaccinations, "updated_at": pet_data["updated_at"]}}
        )
        
        return APIResponse(success=True, message="Vaccination added to pet successfully", data={
            "pet_id": pet_id,
            "vaccination_id": vaccination_id,
            "vaccination_name": vaccination_type.name,
            "vaccination_date": vaccination_date,
            "next_due_date": next_due_date
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in add_pet_vaccination: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to add vaccination to pet: {str(e)}")


@router.delete("/{pet_id}/vaccinations/{vaccination_id}", response_model=APIResponse)
async def remove_pet_vaccination(
    pet_id: str,
    vaccination_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Remove a vaccination from a pet."""
    try:
        # Verify pet exists
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        pet = await pet_crud.get(pets_collection, pet_id)
        if not pet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
        
        # Get pet data and vaccinations
        pet_data = pet.model_dump()
        pet_vaccinations = pet_data.get("vaccinations", [])
        
        # Check if vaccination is assigned to this pet
        vaccination_exists = any(v.get("vaccination_id") == vaccination_id for v in pet_vaccinations)
        if not vaccination_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found on this pet")
        
        # Remove vaccination from pet's vaccinations list
        pet_vaccinations = [v for v in pet_vaccinations if v.get("vaccination_id") != vaccination_id]
        pet_data["vaccinations"] = pet_vaccinations
        pet_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update the pet document
        await pets_collection.update_one(
            {"_id": ObjectId(pet_id)},
            {"$set": {"vaccinations": pet_vaccinations, "updated_at": pet_data["updated_at"]}}
        )
        
        return APIResponse(success=True, message="Vaccination removed from pet successfully", data=None)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in remove_pet_vaccination: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to remove vaccination from pet: {str(e)}") 