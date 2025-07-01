from .auth import router as auth_router
from .users import router as users_router
from .clients import router as clients_router
from .species import router as species_router
from .breeds import router as breeds_router
from .pets import router as pets_router
from .services import router as services_router
from .products import router as products_router
from .appointments import router as appointments_router
from .invoices import router as invoices_router
from .invoice_items import router as invoice_items_router
from .analytics import router as analytics_router
from .allergies import router as allergies_router
from .vaccinations import router as vaccinations_router
from .audit_logs import router as audit_logs_router

__all__ = [
    "auth_router",
    "users_router", 
    "clients_router",
    "species_router",
    "breeds_router",
    "pets_router",
    "services_router", 
    "products_router",
    "appointments_router",
    "invoices_router",
    "invoice_items_router",
    "analytics_router",
    "allergies_router",
    "vaccinations_router",
    "audit_logs_router"
] 