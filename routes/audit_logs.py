"""
Audit Log Routes
Provides endpoints for viewing and managing audit logs (admin only)
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional
from datetime import datetime
from bson import ObjectId

from services.audit_service import AuditService
from utils.auth import get_current_user, require_admin
from models.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/deletions", response_model=dict)
async def get_deletion_history(
    collection_name: Optional[str] = Query(None, description="Filter by collection name"),
    user_id: Optional[str] = Query(None, description="Filter by user who performed deletion"),
    start_date: Optional[datetime] = Query(None, description="Filter deletions after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter deletions before this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    current_user: User = Depends(require_admin)
):
    """
    Get history of hard deletions (admin only)
    
    Returns audit log entries for all hard deletions with optional filters.
    """
    deletions = await AuditService.get_deletion_history(
        collection_name=collection_name,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        "data": deletions,
        "count": len(deletions),
        "filters": {
            "collection_name": collection_name,
            "user_id": user_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit
        }
    }


@router.get("/deletions/{audit_log_id}", response_model=dict)
async def get_deletion_details(
    audit_log_id: str,
    current_user: User = Depends(require_admin)
):
    """
    Get details of a specific deletion (admin only)
    
    Returns the full audit log entry including the document snapshot.
    """
    if not ObjectId.is_valid(audit_log_id):
        raise HTTPException(status_code=400, detail="Invalid audit log ID")
    
    from database import get_collection
    audit_collection = get_collection("audit_logs")
    
    audit_log = await audit_collection.find_one({"_id": ObjectId(audit_log_id)})
    
    if not audit_log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    
    # Convert ObjectIds to strings
    audit_log["_id"] = str(audit_log["_id"])
    audit_log["document_id"] = str(audit_log["document_id"])
    audit_log["user_id"] = str(audit_log["user_id"])
    
    # Check if restoration is possible
    can_restore, reason = await AuditService.can_restore_document(audit_log_id)
    
    return {
        "data": audit_log,
        "restoration": {
            "can_restore": can_restore,
            "reason": reason
        }
    }


@router.post("/deletions/{audit_log_id}/restore", response_model=dict)
async def restore_deleted_document(
    audit_log_id: str,
    request: Request,
    current_user: User = Depends(require_admin)
):
    """
    Restore a hard-deleted document (admin only)
    
    Attempts to restore a document from its audit log snapshot.
    Will fail if unique constraints would be violated.
    """
    if not ObjectId.is_valid(audit_log_id):
        raise HTTPException(status_code=400, detail="Invalid audit log ID")
    
    success, error_message = await AuditService.restore_deleted_document(
        audit_log_id=audit_log_id,
        user=current_user,
        request=request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    return {
        "message": "Document restored successfully",
        "audit_log_id": audit_log_id
    }


@router.post("/hard-delete/{collection}/{document_id}", response_model=dict)
async def hard_delete_with_audit(
    collection: str,
    document_id: str,
    request: Request,
    reason: Optional[str] = Query(None, description="Reason for hard deletion"),
    current_user: User = Depends(require_admin)
):
    """
    Perform a hard deletion with audit logging (admin only)
    
    This endpoint permanently deletes a document and creates an audit log entry.
    The document snapshot is preserved in the audit log for potential restoration.
    
    **WARNING**: This action is permanent and should be used with extreme caution.
    """
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    # Validate collection name
    valid_collections = [
        "users", "clients", "pets", "species", "breeds", 
        "appointments", "services", "products", "invoices", 
        "invoice_items", "allergies", "vaccinations"
    ]
    
    if collection not in valid_collections:
        raise HTTPException(status_code=400, detail="Invalid collection name")
    
    from database import get_collection
    target_collection = get_collection(collection)
    
    # Get the document before deletion
    document = await target_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create a snapshot for audit log
    document_snapshot = document.copy()
    # Convert ObjectIds to strings in snapshot
    for key, value in document_snapshot.items():
        if isinstance(value, ObjectId):
            document_snapshot[key] = str(value)
        elif isinstance(value, datetime):
            document_snapshot[key] = value.isoformat()
    
    # Log the deletion BEFORE performing it
    audit_log_id = await AuditService.log_hard_deletion(
        collection_name=collection,
        document_id=document_id,
        document_snapshot=document_snapshot,
        user=current_user,
        request=request,
        reason=reason,
        metadata={
            "original_status": document.get("status", True),
            "has_relationships": True if collection in ["clients", "pets", "users"] else False
        }
    )
    
    # Perform the actual hard deletion
    result = await target_collection.delete_one({"_id": ObjectId(document_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    return {
        "message": f"Document permanently deleted from {collection}",
        "document_id": document_id,
        "audit_log_id": audit_log_id,
        "deleted_by": current_user.email,
        "reason": reason
    }
