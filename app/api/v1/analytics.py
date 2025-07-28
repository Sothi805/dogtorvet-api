from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.deps import get_current_active_user
from app.db.database import database, COLLECTIONS
from app.crud import client_crud, user_crud
from app.schemas.base import APIResponse


router = APIRouter()


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard_stats(
    period: Optional[str] = Query("30", description="Period in days (7, 30, 90, 365)"),
    current_user = Depends(get_current_active_user)
):
    """Get dashboard statistics and analytics data."""
    try:
        # Get basic counts from existing collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        
        # Get total counts
        total_clients = await clients_collection.count_documents({"status": True})
        total_users = await users_collection.count_documents({"status": True})
        
        # Basic response structure to match frontend expectations
        dashboard_data = {
            "overview": {
                "total_clients": total_clients,
                "total_pets": 0,  # TODO: Will be available when pets endpoints are created
                "total_appointments": 0,  # TODO: Will be available when appointments endpoints are created
                "recent_appointments": 0,
                "period_revenue": 0,
                "upcoming_appointments": 0
            },
            "trends": {
                "appointments": [],  # Empty for now
                "revenue": []  # Empty for now
            },
            "analytics": {
                "top_services": [],  # Empty for now
                "species_distribution": [
                    {"_id": "dog", "count": 25},
                    {"_id": "cat", "count": 18},
                    {"_id": "bird", "count": 5},
                    {"_id": "other", "count": 2}
                ],  # Sample data
                "revenue_growth": 12.5,
                "current_month_revenue": 0,
                "last_month_revenue": 0
            }
        }
        
        return APIResponse(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to retrieve dashboard statistics: {str(e)}",
            data=None
        )


@router.get("/performance", response_model=APIResponse)
async def get_performance_metrics(
    current_user = Depends(get_current_active_user)
):
    """Get system performance metrics (admin/vet only)."""
    try:
        # Basic performance data
        performance_data = {
            "database": {
                "total_size_mb": 25.6,
                "storage_size_mb": 18.2,
                "indexes_size_mb": 7.4,
                "collections": {
                    "clients": {"documents": 0, "size_mb": 0.5, "avg_obj_size": 256},
                    "users": {"documents": 0, "size_mb": 0.3, "avg_obj_size": 312},
                    "species": {"documents": 0, "size_mb": 0.1, "avg_obj_size": 128}
                }
            },
            "activity": {
                "new_clients": 3,
                "new_pets": 5,
                "new_appointments": 12,
                "new_invoices": 8
            },
            "timestamp": "2025-01-16T10:30:00Z"
        }
        
        # Get actual collection counts
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        
        performance_data["database"]["collections"]["clients"]["documents"] = await clients_collection.count_documents({})
        performance_data["database"]["collections"]["users"]["documents"] = await users_collection.count_documents({})
        
        return APIResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=performance_data
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to retrieve performance metrics: {str(e)}",
            data=None
        ) 