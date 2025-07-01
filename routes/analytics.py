from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import json

from database import get_database, get_collection, COLLECTIONS
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    period: str = Query("30", description="Period in days (7, 30, 90, 365)"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics and analytics"""
    try:
        days = int(period)
        start_date = datetime.now() - timedelta(days=days)
        
        # Basic Counts
        total_clients = await db.clients.count_documents({"status": True})
        total_pets = await db.pets.count_documents({"status": True})
        total_appointments = await db.appointments.count_documents({})
        
        # Recent data (based on period)
        recent_appointments = await db.appointments.count_documents({
            "appointment_date": {"$gte": start_date}
        })
        
        recent_revenue = await db.invoices.aggregate([
            {"$match": {"issue_date": {"$gte": start_date}, "status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        revenue = recent_revenue[0]["total"] if recent_revenue else 0
        
        # Appointment trends (daily for last period)
        appointment_trends = await db.appointments.aggregate([
            {"$match": {"appointment_date": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$appointment_date"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(None)
        
        # Revenue trends
        revenue_trends = await db.invoices.aggregate([
            {"$match": {"issue_date": {"$gte": start_date}, "status": "paid"}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$issue_date"}},
                "revenue": {"$sum": "$total_amount"}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(None)
        
        # Top services
        top_services = await db.appointments.aggregate([
            {"$match": {"appointment_date": {"$gte": start_date}}},
            {"$lookup": {
                "from": "services",
                "localField": "service_id",
                "foreignField": "_id",
                "as": "service"
            }},
            {"$unwind": "$service"},
            {"$group": {
                "_id": "$service.name",
                "count": {"$sum": 1},
                "revenue": {"$sum": "$service.price"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]).to_list(5)
        
        # Species distribution
        species_stats = await db.pets.aggregate([
            {"$match": {"status": True}},
            {"$lookup": {
                "from": "species",
                "localField": "species_id", 
                "foreignField": "_id",
                "as": "species"
            }},
            {"$unwind": "$species"},
            {"$group": {
                "_id": "$species.name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]).to_list(None)
        
        # Upcoming appointments (next 7 days)
        upcoming_date = datetime.now() + timedelta(days=7)
        upcoming_appointments = await db.appointments.count_documents({
            "appointment_date": {
                "$gte": datetime.now(),
                "$lte": upcoming_date
            }
        })
        
        # Monthly revenue comparison
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_revenue = await db.invoices.aggregate([
            {"$match": {"issue_date": {"$gte": current_month_start}, "status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        last_month_revenue = await db.invoices.aggregate([
            {"$match": {
                "issue_date": {"$gte": last_month_start, "$lt": current_month_start},
                "status": "paid"
            }},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        
        current_revenue = current_month_revenue[0]["total"] if current_month_revenue else 0
        last_revenue = last_month_revenue[0]["total"] if last_month_revenue else 0
        
        revenue_growth = 0
        if last_revenue > 0:
            revenue_growth = ((current_revenue - last_revenue) / last_revenue) * 100
        
        return {
            "overview": {
                "total_clients": total_clients,
                "total_pets": total_pets,
                "total_appointments": total_appointments,
                "recent_appointments": recent_appointments,
                "period_revenue": revenue,
                "upcoming_appointments": upcoming_appointments
            },
            "trends": {
                "appointments": appointment_trends,
                "revenue": revenue_trends
            },
            "analytics": {
                "top_services": top_services,
                "species_distribution": species_stats,
                "revenue_growth": revenue_growth,
                "current_month_revenue": current_revenue,
                "last_month_revenue": last_revenue
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    db=Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get system performance metrics (admin/vet only)"""
    try:
        # Database stats
        db_stats = await db.command("dbStats")
        
        # Collection sizes
        collections_stats = {}
        for collection_name in ["clients", "pets", "appointments", "invoices", "users"]:
            stats = await db.command("collStats", collection_name)
            collections_stats[collection_name] = {
                "documents": stats.get("count", 0),
                "size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
                "avg_obj_size": round(stats.get("avgObjSize", 0), 2)
            }
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_activity = {
            "new_clients": await db.clients.count_documents({"created_at": {"$gte": yesterday}}),
            "new_pets": await db.pets.count_documents({"created_at": {"$gte": yesterday}}),
            "new_appointments": await db.appointments.count_documents({"created_at": {"$gte": yesterday}}),
            "new_invoices": await db.invoices.count_documents({"created_at": {"$gte": yesterday}})
        }
        
        return {
            "database": {
                "total_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024 * 1024), 2),
                "indexes_size_mb": round(db_stats.get("indexSize", 0) / (1024 * 1024), 2),
                "collections": collections_stats
            },
            "activity": recent_activity,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics error: {str(e)}")


@router.get("/reports/revenue")
async def get_revenue_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    group_by: str = Query("day", description="Group by: day, week, month"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Generate revenue report for specified period"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Date format for grouping
        date_formats = {
            "day": "%Y-%m-%d",
            "week": "%Y-W%U",
            "month": "%Y-%m"
        }
        
        format_str = date_formats.get(group_by, "%Y-%m-%d")
        
        revenue_data = await db.invoices.aggregate([
            {"$match": {
                "issue_date": {"$gte": start, "$lte": end},
                "status": "paid"
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": format_str, "date": "$issue_date"}},
                "revenue": {"$sum": "$total_amount"},
                "count": {"$sum": 1},
                "avg_invoice": {"$avg": "$total_amount"}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(None)
        
        total_revenue = sum(item["revenue"] for item in revenue_data)
        total_invoices = sum(item["count"] for item in revenue_data)
        
        return {
            "period": {"start": start_date, "end": end_date, "group_by": group_by},
            "summary": {
                "total_revenue": total_revenue,
                "total_invoices": total_invoices,
                "average_invoice": total_revenue / total_invoices if total_invoices > 0 else 0
            },
            "data": revenue_data
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revenue report error: {str(e)}")


@router.get("/appointments-by-month")
async def get_appointments_by_month(
    year: int = Query(default=datetime.now().year),
    current_user: User = Depends(get_current_user)
):
    """Get appointments grouped by month for a specific year"""
    try:
        appointments_collection = get_collection(COLLECTIONS["appointments"])
        
        # Create date range for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        pipeline = [
            {
                "$match": {
                    "appointment_date": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": {"$month": "$appointment_date"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        results = await appointments_collection.aggregate(pipeline).to_list(12)
        
        # Initialize all months with 0
        months_data = {i: 0 for i in range(1, 13)}
        
        # Fill in actual data
        for result in results:
            months_data[result["_id"]] = result["count"]
        
        # Convert to list format
        monthly_data = [
            {"month": month, "appointments": count}
            for month, count in months_data.items()
        ]
        
        return {
            "year": year,
            "data": monthly_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointments by month: {str(e)}")


@router.get("/revenue-by-month")
async def get_revenue_by_month(
    year: int = Query(default=datetime.now().year),
    current_user: User = Depends(get_current_user)
):
    """Get revenue grouped by month for a specific year"""
    try:
        invoices_collection = get_collection(COLLECTIONS["invoices"])
        
        # Create date range for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        pipeline = [
            {
                "$match": {
                    "invoice_date": {
                        "$gte": start_date,
                        "$lt": end_date
                    },
                    "payment_status": "paid"
                }
            },
            {
                "$group": {
                    "_id": {"$month": "$invoice_date"},
                    "revenue": {"$sum": "$total"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        results = await invoices_collection.aggregate(pipeline).to_list(12)
        
        # Initialize all months with 0
        months_data = {i: 0 for i in range(1, 13)}
        
        # Fill in actual data
        for result in results:
            months_data[result["_id"]] = result["revenue"]
        
        # Convert to list format
        monthly_data = [
            {"month": month, "revenue": revenue}
            for month, revenue in months_data.items()
        ]
        
        return {
            "year": year,
            "data": monthly_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching revenue by month: {str(e)}") 