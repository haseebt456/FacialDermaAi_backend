from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.deps.auth import get_current_user
from app.users.schemas import (
    DermatologistVerificationResponse, 
    AdminDashboardStats,
    DermatologistVerificationRequest
)
from app.db.mongo import get_users_collection, get_dermatologist_verifications_collection
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Dependency to check if user is admin
async def get_current_admin_user(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(current_admin = Depends(get_current_admin_user)):
    """Get admin dashboard statistics"""
    users_collection = get_users_collection()
    
    # Get user counts
    total_users = await users_collection.count_documents({})
    total_patients = await users_collection.count_documents({"role": "patient"})
    total_dermatologists = await users_collection.count_documents({"role": "dermatologist"})
    
    # Get pending verifications
    verifications_collection = get_dermatologist_verifications_collection()
    pending_verifications = await verifications_collection.count_documents({"status": "pending"})
    
    # Get predictions and review requests counts (you'll need to implement these)
    total_predictions = 0  # Implement based on your predictions collection
    total_review_requests = 0  # Implement based on your review_requests collection
    
    return {
        "totalUsers": total_users,
        "totalPatients": total_patients,
        "totalDermatologists": total_dermatologists,
        "pendingVerifications": pending_verifications,
        "totalPredictions": total_predictions,
        "totalReviewRequests": total_review_requests
    }

@router.get("/dermatologists/pending", response_model=List[DermatologistVerificationResponse])
async def get_pending_dermatologist_verifications(current_admin = Depends(get_current_admin_user)):
    """Get all pending dermatologist verifications with user details"""
    verifications_collection = get_dermatologist_verifications_collection()
    users_collection = get_users_collection()
    
    verifications = await verifications_collection.find({"status": "pending"}).to_list(length=None)
    
    # Enrich verifications with user details
    for verification in verifications:
        verification["id"] = str(verification["_id"])
        del verification["_id"]
        
        # Get user details
        from bson import ObjectId
        user = await users_collection.find_one({"_id": ObjectId(verification["dermatologistId"])})
        if user:
            verification["name"] = user.get("name", "N/A")
            verification["email"] = user.get("email", "N/A")
            verification["username"] = user.get("username", "N/A")
    
    return verifications

@router.post("/dermatologists/{dermatologist_id}/verify")
async def verify_dermatologist(
    dermatologist_id: str,
    verification_data: DermatologistVerificationRequest,
    current_admin = Depends(get_current_admin_user)
):
    """Approve or reject dermatologist verification"""
    verifications_collection = get_dermatologist_verifications_collection()
    users_collection = get_users_collection()
    
    # Update verification status
    update_data = {
        "status": verification_data.status,
        "reviewedBy": current_admin["id"],
        "reviewedAt": datetime.utcnow()
    }
    
    if verification_data.reviewComments:
        update_data["reviewComments"] = verification_data.reviewComments
    
    result = await verifications_collection.update_one(
        {"dermatologistId": dermatologist_id, "status": "pending"},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending verification not found"
        )
    
    # If approved, update user verification status
    if verification_data.status == "approved":
        await users_collection.update_one(
            {"_id": dermatologist_id},
            {"$set": {"isVerified": True, "verifiedAt": datetime.utcnow()}}
        )
    elif verification_data.status == "rejected":
        # For rejected, we might want to mark as not verified or keep the status
        await users_collection.update_one(
            {"_id": dermatologist_id},
            {"$set": {"isVerified": False}}
        )
    
    return {"message": f"Dermatologist {verification_data.status}"}

@router.get("/users")
async def get_all_users(
    current_admin = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
):
    """Get all users with pagination and filtering"""
    users_collection = get_users_collection()
    
    query = {}
    if role:
        query["role"] = role
    
    users = await users_collection.find(query).skip(skip).limit(limit).to_list(length=None)
    
    # Convert ObjectId to string and remove sensitive data
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
        # Remove password hash and sensitive tokens
        if "password" in user:
            del user["password"]
        if "verification_token" in user:
            del user["verification_token"]
        if "token_expiry" in user:
            del user["token_expiry"]
        if "emailLower" in user:
            del user["emailLower"]
    
    return {"users": users, "total": len(users)}

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_admin = Depends(get_current_admin_user)
):
    """Suspend a user account"""
    users_collection = get_users_collection()
    
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"isSuspended": True, "suspendedAt": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User suspended successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin = Depends(get_current_admin_user)
):
    """Delete a user account"""
    users_collection = get_users_collection()
    
    result = await users_collection.delete_one({"_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.put("/profile")
async def update_admin_profile(
    profile_data: dict,
    current_admin = Depends(get_current_admin_user)
):
    """Update admin profile (email, name, etc.)"""
    users_collection = get_users_collection()
    
    # Only allow updating certain fields
    allowed_fields = ["name", "email"]
    update_data = {}
    
    for field in allowed_fields:
        if field in profile_data:
            update_data[field] = profile_data[field]
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    update_data["updatedAt"] = datetime.utcnow()
    
    result = await users_collection.update_one(
        {"_id": current_admin["_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return {"message": "Admin profile updated successfully"}


@router.post("/change-password")
async def change_admin_password(
    password_data: dict,
    current_admin = Depends(get_current_admin_user)
):
    """Change admin password"""
    from app.auth.service import verify_password, hash_password
    
    users_collection = get_users_collection()
    
    # Get current admin data
    admin = await users_collection.find_one({"_id": current_admin["_id"]})
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Verify current password
    if not verify_password(password_data["currentPassword"], admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data["newPassword"]) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash and update password
    hashed_password = hash_password(password_data["newPassword"])
    await users_collection.update_one(
        {"_id": current_admin["_id"]},
        {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
    )
    
    return {"message": "Admin password changed successfully"}
