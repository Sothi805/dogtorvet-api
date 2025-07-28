# Import all schemas for easy access
from .base import BaseSchema, BaseDBSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema, APIResponse
from .user import UserDB, UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenData, UserRole
from .client import ClientDB, ClientCreate, ClientUpdate, ClientResponse, Gender
from .pet import PetDB, PetCreate, PetUpdate, PetResponse, PetGender
from .species import SpeciesDB, SpeciesCreate, SpeciesUpdate, SpeciesResponse
from .breed import BreedDB, BreedCreate, BreedUpdate, BreedResponse
from .appointment import AppointmentDB, AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentStatus
from .service import ServiceDB, ServiceCreate, ServiceUpdate, ServiceResponse
from .product import ProductDB, ProductCreate, ProductUpdate, ProductResponse
from .invoice import InvoiceDB, InvoiceCreate, InvoiceUpdate
from .vaccination import VaccinationDB, VaccinationCreate, VaccinationUpdate, VaccinationResponse
from .allergy import AllergyDB, AllergyCreate, AllergyUpdate, AllergyResponse, AllergySeverity

__all__ = [
    # Base schemas
    "BaseSchema",
    "BaseDBSchema", 
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseResponseSchema",
    "APIResponse",
    
    # User schemas
    "UserDB",
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    "UserRole",
    
    # Client schemas
    "ClientDB",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "Gender",
    
    # Pet schemas
    "PetDB",
    "PetCreate",
    "PetUpdate",
    "PetResponse",
    "PetGender",
    
    # Species schemas
    "SpeciesDB",
    "SpeciesCreate",
    "SpeciesUpdate",
    "SpeciesResponse",
    
    # Breed schemas
    "BreedDB",
    "BreedCreate",
    "BreedUpdate",
    "BreedResponse",
    
    # Appointment schemas
    "AppointmentDB",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AppointmentStatus",
    
    # Service schemas
    "ServiceDB",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    
    # Product schemas
    "ProductDB",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    
    # Invoice schemas
    "InvoiceDB",
    "InvoiceCreate",
    "InvoiceUpdate",
    
    # Vaccination schemas
    "VaccinationDB",
    "VaccinationCreate",
    "VaccinationUpdate",
    "VaccinationResponse",
    
    # Allergy schemas
    "AllergyDB",
    "AllergyCreate",
    "AllergyUpdate",
    "AllergyResponse",
    "AllergySeverity"
] 