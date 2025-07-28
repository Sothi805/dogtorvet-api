from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .clients import router as clients_router
from .species import router as species_router
from .analytics import router as analytics_router
from .invoices import router as invoices_router
from .invoice_items import router as invoice_items_router
from .pets import router as pets_router
from .breeds import router as breeds_router
from .allergies import router as allergies_router
from .vaccinations import router as vaccinations_router
from .appointments import router as appointments_router
from .services import router as services_router
from .products import router as products_router


api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(species_router, prefix="/species", tags=["species"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
api_router.include_router(invoice_items_router, prefix="/invoice-items", tags=["invoice-items"])
api_router.include_router(pets_router, prefix="/pets", tags=["pets"])
api_router.include_router(breeds_router, prefix="/breeds", tags=["breeds"])
api_router.include_router(allergies_router, prefix="/allergies", tags=["allergies"])
api_router.include_router(vaccinations_router, prefix="/vaccinations", tags=["vaccinations"])
api_router.include_router(appointments_router, prefix="/appointments", tags=["appointments"])
api_router.include_router(services_router, prefix="/services", tags=["services"])
api_router.include_router(products_router, prefix="/products", tags=["products"]) 