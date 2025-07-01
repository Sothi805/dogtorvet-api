"""
Audit Service
Handles logging of critical actions including hard deletions
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from fastapi import Request

from database import get_collection
from models.audit_log import AuditLog, AuditAction
from models.user import User
from utils.logging import logger


class AuditService:
    """Service for handling audit logging"""
    
    @staticmethod
    async def log_hard_deletion(
        collection_name: str,
        document_id: str,
        document_snapshot: Dict[str, Any],
        user: User,
        request: Optional[Request] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a hard deletion event
        
        Args:
            collection_name: Name of the collection where deletion occurred
            document_id: ID of the deleted document
            document_snapshot: Complete snapshot of document before deletion
            user: User who performed the deletion
            request: FastAPI request object (for IP and user agent)
            reason: Optional reason for deletion
            metadata: Additional metadata
            
        Returns:
            ID of the created audit log entry
        """
        try:
            audit_collection = get_collection("audit_logs")
            
            # Extract request information if available
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            # Create audit log entry
            audit_log = {
                "action": AuditAction.HARD_DELETE,
                "collection_name": collection_name,
                "document_id": ObjectId(document_id),
                "document_snapshot": document_snapshot,
                "user_id": ObjectId(user.id),
                "user_email": user.email,
                "user_role": user.role,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "reason": reason,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": True
            }
            
            result = await audit_collection.insert_one(audit_log)
            
            logger.warning(
                f"HARD DELETE: User {user.email} deleted document {document_id} "
                f"from {collection_name}. Audit log: {result.inserted_id}"
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create audit log for hard deletion: {str(e)}")
            # Don't fail the deletion if audit logging fails
            # But log the error prominently
            logger.critical(
                f"AUDIT FAILURE: Could not log hard deletion of {document_id} "
                f"from {collection_name} by {user.email}"
            )
            return None
    
    @staticmethod
    async def get_deletion_history(
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve deletion history with filters
        
        Args:
            collection_name: Filter by collection
            user_id: Filter by user who performed deletion
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records to return
            
        Returns:
            List of audit log entries
        """
        try:
            audit_collection = get_collection("audit_logs")
            
            # Build query
            query = {"action": AuditAction.HARD_DELETE}
            
            if collection_name:
                query["collection_name"] = collection_name
                
            if user_id:
                query["user_id"] = ObjectId(user_id)
                
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["created_at"] = date_query
            
            # Execute query
            cursor = audit_collection.find(query).sort("created_at", -1).limit(limit)
            
            results = []
            async for doc in cursor:
                # Convert ObjectIds to strings for JSON serialization
                doc["_id"] = str(doc["_id"])
                doc["document_id"] = str(doc["document_id"])
                doc["user_id"] = str(doc["user_id"])
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve deletion history: {str(e)}")
            return []
    
    @staticmethod
    async def can_restore_document(
        audit_log_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a deleted document can be restored
        
        Args:
            audit_log_id: ID of the audit log entry
            
        Returns:
            Tuple of (can_restore, reason_if_not)
        """
        try:
            audit_collection = get_collection("audit_logs")
            
            # Get the audit log entry
            audit_log = await audit_collection.find_one({
                "_id": ObjectId(audit_log_id),
                "action": AuditAction.HARD_DELETE
            })
            
            if not audit_log:
                return False, "Audit log entry not found"
            
            # Check if document still exists (was recreated)
            collection = get_collection(audit_log["collection_name"])
            existing = await collection.find_one({"_id": audit_log["document_id"]})
            
            if existing:
                return False, "A document with this ID already exists"
            
            # Check for unique constraint violations
            snapshot = audit_log["document_snapshot"]
            
            # Check specific unique fields based on collection
            if audit_log["collection_name"] == "users" and "email" in snapshot:
                existing_email = await collection.find_one({"email": snapshot["email"]})
                if existing_email:
                    return False, f"Email {snapshot['email']} is already in use"
                    
            elif audit_log["collection_name"] == "clients" and "phone_number" in snapshot:
                existing_phone = await collection.find_one({"phone_number": snapshot["phone_number"]})
                if existing_phone:
                    return False, f"Phone number {snapshot['phone_number']} is already in use"
                    
            elif audit_log["collection_name"] == "invoices" and "invoice_number" in snapshot:
                existing_invoice = await collection.find_one({"invoice_number": snapshot["invoice_number"]})
                if existing_invoice:
                    return False, f"Invoice number {snapshot['invoice_number']} is already in use"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to check if document can be restored: {str(e)}")
            return False, "Error checking restoration possibility"
    
    @staticmethod
    async def restore_deleted_document(
        audit_log_id: str,
        user: User,
        request: Optional[Request] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Restore a hard-deleted document from audit log
        
        Args:
            audit_log_id: ID of the audit log entry
            user: User performing the restoration
            request: FastAPI request object
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # First check if restoration is possible
            can_restore, reason = await AuditService.can_restore_document(audit_log_id)
            if not can_restore:
                return False, reason
            
            audit_collection = get_collection("audit_logs")
            audit_log = await audit_collection.find_one({"_id": ObjectId(audit_log_id)})
            
            # Restore the document
            collection = get_collection(audit_log["collection_name"])
            snapshot = audit_log["document_snapshot"].copy()
            
            # Update timestamps
            snapshot["updated_at"] = datetime.utcnow()
            snapshot["restored_at"] = datetime.utcnow()
            snapshot["restored_by"] = ObjectId(user.id)
            
            # Reinsert the document
            await collection.insert_one(snapshot)
            
            # Log the restoration
            logger.info(
                f"RESTORATION: User {user.email} restored document {audit_log['document_id']} "
                f"to {audit_log['collection_name']} from audit log {audit_log_id}"
            )
            
            # Create audit entry for the restoration
            restore_metadata = {
                "original_deletion_date": audit_log["created_at"],
                "original_deleted_by": audit_log["user_email"],
                "audit_log_id": audit_log_id
            }
            
            await audit_collection.insert_one({
                "action": "document_restoration",
                "collection_name": audit_log["collection_name"],
                "document_id": audit_log["document_id"],
                "user_id": ObjectId(user.id),
                "user_email": user.email,
                "user_role": user.role,
                "metadata": restore_metadata,
                "created_at": datetime.utcnow(),
                "status": True
            })
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to restore document: {str(e)}")
            return False, f"Restoration failed: {str(e)}"
