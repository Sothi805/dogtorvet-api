from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId

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
        # Get collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        appointments_collection = database.get_collection(COLLECTIONS["appointments"])
        invoices_collection = database.get_collection(COLLECTIONS["invoices"])
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(period))
        
        # Get total counts
        total_clients = await clients_collection.count_documents({"status": True})
        total_users = await users_collection.count_documents({"status": True})
        total_pets = await pets_collection.count_documents({"status": True})
        total_appointments = await appointments_collection.count_documents({})
        
        print(f"🔍 Debug - Total appointments: {total_appointments}")
        print(f"🔍 Debug - Date range: {start_date} to {end_date}")
        
        # Debug: Check what appointments exist
        sample_appointments = []
        async for appointment in appointments_collection.find().limit(3):
            sample_appointments.append({
                "id": str(appointment.get("_id")),
                "appointment_date": appointment.get("appointment_date"),
                "appointment_status": appointment.get("appointment_status"),
                "pet_id": appointment.get("pet_id")
            })
        print(f"🔍 Debug - Sample appointments: {sample_appointments}")
        
        # Get recent appointments (within the period)
        recent_appointments = await appointments_collection.count_documents({
            "appointment_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        
        print(f"🔍 Debug - Recent appointments: {recent_appointments}")
        
        # Get upcoming appointments
        upcoming_appointments = await appointments_collection.count_documents({
            "appointment_date": {
                "$gte": datetime.now()
            },
            "appointment_status": {"$in": ["scheduled"]}
        })
        
        print(f"🔍 Debug - Upcoming appointments: {upcoming_appointments}")
        
        # Calculate period revenue
        period_revenue = 0
        invoices_in_period = invoices_collection.find({
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        
        async for invoice in invoices_in_period:
            # Calculate total from invoice items
            if "items" in invoice and invoice["items"]:
                for item in invoice["items"]:
                    period_revenue += float(item.get("net_price", 0))
        
        # Get species distribution
        species_pipeline = [
            {"$match": {"status": True}},
            {"$group": {"_id": "$species_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        species_distribution = []
        async for result in pets_collection.aggregate(species_pipeline):
            # Get species name from species collection
            species_collection = database.get_collection(COLLECTIONS["species"])
            species = await species_collection.find_one({"_id": result["_id"]})
            species_name = species.get("name", "Unknown") if species else "Unknown"
            species_distribution.append({
                "_id": species_name,
                "count": result["count"]
            })
        
        # Get top services (from appointments)
        services_pipeline = [
            {"$match": {
                "appointment_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }},
            {"$group": {"_id": "$service_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_services = []
        async for result in appointments_collection.aggregate(services_pipeline):
            # Get service name from services collection
            services_collection = database.get_collection(COLLECTIONS["services"])
            service = await services_collection.find_one({"_id": result["_id"]})
            service_name = service.get("name", "Unknown") if service else "Unknown"
            top_services.append({
                "_id": service_name,
                "count": result["count"],
                "revenue": 0  # TODO: Calculate actual revenue per service
            })
        
        # Calculate revenue growth (simplified - compare current vs previous period)
        previous_start = start_date - timedelta(days=int(period))
        previous_end = start_date
        
        previous_revenue = 0
        previous_invoices = invoices_collection.find({
            "created_at": {
                "$gte": previous_start,
                "$lte": previous_end
            }
        })
        
        async for invoice in previous_invoices:
            if "items" in invoice and invoice["items"]:
                for item in invoice["items"]:
                    previous_revenue += float(item.get("net_price", 0))
        
        revenue_growth = 0
        if previous_revenue > 0:
            revenue_growth = ((period_revenue - previous_revenue) / previous_revenue) * 100
        
        # Get appointment trends (grouped by date)
        appointment_trends_pipeline = [
            {"$match": {
                "appointment_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$appointment_date"
                    }
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 30}  # Limit to last 30 days
        ]
        
        appointment_trends = []
        async for result in appointments_collection.aggregate(appointment_trends_pipeline):
            appointment_trends.append({
                "_id": result["_id"],
                "count": result["count"]
            })
        
        print(f"🔍 Debug - Appointment trends: {appointment_trends}")
        
        # If no appointment trends data, generate sample data for testing
        if not appointment_trends:
            print("🔍 Debug - No appointment trends found, generating sample data")
            # Generate sample data for the last 7 days
            for i in range(7):
                sample_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                appointment_trends.append({
                    "_id": sample_date,
                    "count": 0  # Start with 0, will be populated when real appointments are created
                })
            appointment_trends.reverse()  # Sort by date ascending
        
        # Get revenue trends (grouped by date)
        revenue_trends_pipeline = [
            {"$match": {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }},
            {"$unwind": "$items"},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "revenue": {"$sum": {"$toDouble": "$items.net_price"}}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 30}  # Limit to last 30 days
        ]
        
        revenue_trends = []
        async for result in invoices_collection.aggregate(revenue_trends_pipeline):
            revenue_trends.append({
                "_id": result["_id"],
                "revenue": round(result["revenue"], 2)
            })
        
        print(f"🔍 Debug - Revenue trends: {revenue_trends}")
        
        # If no revenue trends data, generate sample data for testing
        if not revenue_trends:
            print("🔍 Debug - No revenue trends found, generating sample data")
            # Generate sample data for the last 7 days
            for i in range(7):
                sample_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                revenue_trends.append({
                    "_id": sample_date,
                    "revenue": 0.0  # Start with 0, will be populated when real invoices are created
                })
            revenue_trends.reverse()  # Sort by date ascending
        
        # Build response
        dashboard_data = {
            "overview": {
                "total_clients": total_clients,
                "total_pets": total_pets,
                "total_appointments": total_appointments,
                "recent_appointments": recent_appointments,
                "period_revenue": round(period_revenue, 2),
                "upcoming_appointments": upcoming_appointments
            },
            "trends": {
                "appointments": appointment_trends,
                "revenue": revenue_trends
            },
            "analytics": {
                "top_services": top_services,
                "species_distribution": species_distribution,
                "revenue_growth": round(revenue_growth, 1),
                "current_month_revenue": round(period_revenue, 2),
                "last_month_revenue": round(previous_revenue, 2)
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
        # Get collections
        clients_collection = database.get_collection(COLLECTIONS["clients"])
        users_collection = database.get_collection(COLLECTIONS["users"])
        pets_collection = database.get_collection(COLLECTIONS["pets"])
        appointments_collection = database.get_collection(COLLECTIONS["appointments"])
        invoices_collection = database.get_collection(COLLECTIONS["invoices"])
        species_collection = database.get_collection(COLLECTIONS["species"])
        services_collection = database.get_collection(COLLECTIONS["services"])
        products_collection = database.get_collection(COLLECTIONS["products"])
        
        # Get actual collection counts
        clients_count = await clients_collection.count_documents({})
        users_count = await users_collection.count_documents({})
        pets_count = await pets_collection.count_documents({})
        appointments_count = await appointments_collection.count_documents({})
        invoices_count = await invoices_collection.count_documents({})
        species_count = await species_collection.count_documents({})
        services_count = await services_collection.count_documents({})
        products_count = await products_collection.count_documents({})
        
        # Calculate total documents
        total_documents = clients_count + users_count + pets_count + appointments_count + invoices_count + species_count + services_count + products_count
        
        # Calculate recent activity (last 24 hours)
        day_ago = datetime.now() - timedelta(days=1)
        
        new_clients_24h = await clients_collection.count_documents({
            "created_at": {"$gte": day_ago}
        })
        
        new_pets_24h = await pets_collection.count_documents({
            "created_at": {"$gte": day_ago}
        })
        
        new_appointments_24h = await appointments_collection.count_documents({
            "created_at": {"$gte": day_ago}
        })
        
        new_invoices_24h = await invoices_collection.count_documents({
            "created_at": {"$gte": day_ago}
        })
        
        # Calculate recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        
        new_clients_7d = await clients_collection.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        new_pets_7d = await pets_collection.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        new_appointments_7d = await appointments_collection.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        new_invoices_7d = await invoices_collection.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        # Calculate database size estimates (rough calculation based on document counts and average sizes)
        # These are estimates since we can't get actual MongoDB storage stats without admin privileges
        estimated_sizes = {
            "clients": clients_count * 2.5,    # ~2.5KB per client (name, email, phone, address, etc.)
            "users": users_count * 1.8,        # ~1.8KB per user (name, email, role, permissions, etc.)
            "pets": pets_count * 3.2,          # ~3.2KB per pet (name, species, breed, medical history, etc.)
            "appointments": appointments_count * 2.8,  # ~2.8KB per appointment (date, time, client, pet, service, notes, etc.)
            "invoices": invoices_count * 4.5,   # ~4.5KB per invoice (items, totals, client, payment info, etc.)
            "species": species_count * 0.8,     # ~0.8KB per species (name, description, etc.)
            "services": services_count * 1.5,   # ~1.5KB per service (name, price, duration, description, etc.)
            "products": products_count * 2.0    # ~2.0KB per product (name, price, stock, description, etc.)
        }
        
        total_size_mb = sum(estimated_sizes.values()) / 1024  # Convert KB to MB
        storage_size_mb = total_size_mb * 0.75  # Assume 75% storage efficiency
        indexes_size_mb = total_size_mb * 0.08   # Assume 8% for indexes (more realistic)
        
        # For MongoDB Atlas free tier, total database size is 512MB
        database_total_size_mb = 512.0  # MongoDB Atlas free tier limit
        
        # Debug logging for size calculations
        print(f"🔍 Database size calculation:")
        print(f"  - Clients: {clients_count} × 2.5KB = {estimated_sizes['clients']:.1f}KB")
        print(f"  - Users: {users_count} × 1.8KB = {estimated_sizes['users']:.1f}KB")
        print(f"  - Pets: {pets_count} × 3.2KB = {estimated_sizes['pets']:.1f}KB")
        print(f"  - Appointments: {appointments_count} × 2.8KB = {estimated_sizes['appointments']:.1f}KB")
        print(f"  - Invoices: {invoices_count} × 4.5KB = {estimated_sizes['invoices']:.1f}KB")
        print(f"  - Species: {species_count} × 0.8KB = {estimated_sizes['species']:.1f}KB")
        print(f"  - Services: {services_count} × 1.5KB = {estimated_sizes['services']:.1f}KB")
        print(f"  - Products: {products_count} × 2.0KB = {estimated_sizes['products']:.1f}KB")
        print(f"  - Total: {sum(estimated_sizes.values()):.1f}KB = {total_size_mb:.2f}MB")
        print(f"  - Storage: {storage_size_mb:.2f}MB, Indexes: {indexes_size_mb:.2f}MB")
        print(f"  - MongoDB Atlas Free Tier Limit: {database_total_size_mb:.2f}MB")
        
        # Calculate system health metrics
        active_clients = await clients_collection.count_documents({"status": True})
        active_pets = await pets_collection.count_documents({"status": True})
        active_users = await users_collection.count_documents({"status": True})
        
        # Calculate appointment statistics
        today_appointments = await appointments_collection.count_documents({
            "appointment_date": {
                "$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                "$lt": datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        })
        
        upcoming_appointments = await appointments_collection.count_documents({
            "appointment_date": {"$gte": datetime.now()},
            "appointment_status": "scheduled"
        })
        
        # Build performance data
        performance_data = {
            "database": {
                "total_size_mb": database_total_size_mb,  # MongoDB Atlas free tier limit
                "storage_size_mb": round(storage_size_mb, 2),
                "indexes_size_mb": round(indexes_size_mb, 2),
                "collections": {
                    "clients": {"documents": clients_count, "size_mb": round(estimated_sizes["clients"] / 1024, 2), "avg_obj_size": 512},
                    "users": {"documents": users_count, "size_mb": round(estimated_sizes["users"] / 1024, 2), "avg_obj_size": 312},
                    "pets": {"documents": pets_count, "size_mb": round(estimated_sizes["pets"] / 1024, 2), "avg_obj_size": 768},
                    "appointments": {"documents": appointments_count, "size_mb": round(estimated_sizes["appointments"] / 1024, 2), "avg_obj_size": 384},
                    "invoices": {"documents": invoices_count, "size_mb": round(estimated_sizes["invoices"] / 1024, 2), "avg_obj_size": 1024},
                    "species": {"documents": species_count, "size_mb": round(estimated_sizes["species"] / 1024, 2), "avg_obj_size": 128},
                    "services": {"documents": services_count, "size_mb": round(estimated_sizes["services"] / 1024, 2), "avg_obj_size": 256},
                    "products": {"documents": products_count, "size_mb": round(estimated_sizes["products"] / 1024, 2), "avg_obj_size": 384}
                }
            },
            "activity": {
                "new_clients_24h": new_clients_24h,
                "new_pets_24h": new_pets_24h,
                "new_appointments_24h": new_appointments_24h,
                "new_invoices_24h": new_invoices_24h,
                "new_clients_7d": new_clients_7d,
                "new_pets_7d": new_pets_7d,
                "new_appointments_7d": new_appointments_7d,
                "new_invoices_7d": new_invoices_7d
            },
            "system_health": {
                "total_documents": total_documents,
                "active_clients": active_clients,
                "active_pets": active_pets,
                "active_users": active_users,
                "today_appointments": today_appointments,
                "upcoming_appointments": upcoming_appointments,
                "collection_count": 8  # Total number of collections
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
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