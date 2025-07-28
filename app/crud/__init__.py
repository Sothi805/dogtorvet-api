# Import all CRUD instances
from .base import CRUDBase
from .user import user_crud
from .client import client_crud
from .pet import pet_crud
from .species import species_crud
from .breed import breed_crud
from .appointment import appointment_crud
from .service import service_crud
from .product import product_crud
from .invoice import invoices_crud
from .invoice_item import invoice_items_crud
from .vaccination import vaccination_crud
from .allergy import allergy_crud

__all__ = [
    "CRUDBase",
    "user_crud",
    "client_crud",
    "pet_crud",
    "species_crud",
    "breed_crud",
    "appointment_crud",
    "service_crud",
    "product_crud",
    "invoices_crud",
    "invoice_items_crud",
    "vaccination_crud",
    "allergy_crud"
] 