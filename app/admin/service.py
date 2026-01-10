# app/admin/service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongo import (
    get_users_collection,
    get_dermatologist_verifications_collection,
    get_predictions_collection,
    get_review_requests_collection,
    get_activity_logs_collection
)
from app.email.mailer import (
    send_dermatologist_approval_email,
    send_dermatologist_rejection_email,
    send_account_suspended_email,
    send_account_unsuspended_email,
    send_account_deleted_email
)

# ===================== Dashboard Stats ========================
async def get_admin_stats():
    users = get_users_collection()
    verifications = get_dermatologist_verifications_collection()
    predictions = get_predictions_collection()
    reviews = get_review_requests_collection()

    return {
        "totalUsers": await users.count_documents({}),
        "totalPatients": await users.count_documents({"role": "patient"}),
        "totalDermatologists": await users.count_documents({"role": "dermatologist"}),
        "pendingVerifications": await verifications.count_documents({"status": "pending"}),
        "totalPredictions": await predictions.count_documents({}),
        "totalReviewRequests": await reviews.count_documents({}),
    }

# ================= Pending Verifications ======================
async def get_pending_verifications_service():
    verifications_col = get_dermatologist_verifications_collection()
    users = get_users_collection()

    verifications = await verifications_col.find({"status": "pending"}).to_list(length=None)

    for v in verifications:
        v["id"] = str(v["_id"])
        del v["_id"]

        user = await users.find_one({"_id": ObjectId(v["dermatologistId"])})
        if user:
            v["name"] = user.get("name")
            v["email"] = user.get("email")
            v["username"] = user.get("username")

    return verifications

async def get_rejected_verifications_service():
    verifications_col = get_dermatologist_verifications_collection()
    users = get_users_collection()

    verifications = await verifications_col.find({"status": "rejected"}).to_list(length=None)

    cleaned = []
    for v in verifications:
        v["id"] = str(v["_id"])
        del v["_id"]

        user = await users.find_one({"_id": ObjectId(v["dermatologistId"])})
        if user:
            v["name"] = user.get("name")
            v["email"] = user.get("email")
            v["username"] = user.get("username")
            cleaned.append(v)
        # If user not found, skip the verification (user was deleted)

    return cleaned

# ================= Approve/Reject Dermatologist ===============
async def verify_dermatologist_service(dermatologist_id, data, current_admin):
    verifications = get_dermatologist_verifications_collection()
    users = get_users_collection()

    update_data = {
        "status": data.get("status"),
        "reviewedBy": str(current_admin.get("_id", current_admin.get("id", ""))),
        "reviewedAt": datetime.utcnow(),
    }
    
    if data.get("reviewComments"):
        update_data["reviewComments"] = data.get("reviewComments")

    result = await verifications.update_one(
        {"dermatologistId": dermatologist_id, "status": "pending"},
        {"$set": update_data}
    )

    dermatologist_email = "Unknown"

    if result.modified_count == 0:
        # No pending verification found
        if data.get('status') == "approved":
            # Directly approve the user
            await users.update_one(
                {"_id": ObjectId(dermatologist_id)},
                {"$set": {"isVerified": True, "verifiedAt": datetime.utcnow()}}
            )
            dermatologist = await users.find_one({"_id": ObjectId(dermatologist_id)}, {"email": 1, "name": 1, "username": 1})
            if dermatologist:
                await send_dermatologist_approval_email(
                    dermatologist.get("email"),
                    dermatologist.get("name") or dermatologist.get("username")
                )
            return {"message": "Dermatologist approved"}
        elif data.get('status') == "rejected":
            # Create a rejected verification document
            verification_doc = {
                "dermatologistId": dermatologist_id,
                "status": "rejected",
                "submittedAt": datetime.utcnow(),
                "reviewedBy": str(current_admin.get("_id", current_admin.get("id", ""))),
                "reviewedAt": datetime.utcnow(),
                "reviewComments": data.get("reviewComments", ""),
            }
            await verifications.insert_one(verification_doc)
            # Ensure user is not verified
            await users.update_one(
                {"_id": ObjectId(dermatologist_id)},
                {"$set": {"isVerified": False}}
            )
            dermatologist = await users.find_one({"_id": ObjectId(dermatologist_id)}, {"email": 1, "name": 1, "username": 1})
            if dermatologist:
                await send_dermatologist_rejection_email(
                    dermatologist.get("email"),
                    dermatologist.get("name") or dermatologist.get("username"),
                    data.get("reviewComments", "Your account did not meet our verification requirements")
                )
            return {"message": "Dermatologist rejected"}
    else:
        # Existing pending verification updated
        user_obj = ObjectId(dermatologist_id)
        if data.get("status") == "approved":
            await users.update_one(
                {"_id": user_obj},
                {"$set": {"isVerified": True, "verifiedAt": datetime.utcnow()}}
            )
        elif data.get("status") == "rejected":
            await users.update_one(
                {"_id": user_obj},
                {"$set": {"isVerified": False}}
            )

        # Fetch dermatologist for notification/logging
        dermatologist = await users.find_one({"_id": user_obj}, {"email": 1, "name": 1, "username": 1})
        dermatologist_email = dermatologist.get("email") if dermatologist else "Unknown"

        if data.get("status") == "approved" and dermatologist:
            await send_dermatologist_approval_email(
                dermatologist.get("email"),
                dermatologist.get("name") or dermatologist.get("username")
            )
        elif data.get("status") == "rejected" and dermatologist:
            await send_dermatologist_rejection_email(
                dermatologist.get("email"),
                dermatologist.get("name") or dermatologist.get("username"),
                data.get("reviewComments", "Your account did not meet our verification requirements")
            )
    
    action_text = f"Dermatologist verification {data.get('status')}"
    await log_admin_activity(
        str(current_admin.get("_id", current_admin.get("id", ""))), 
        action_text, 
        {"dermatologistEmail": dermatologist_email}
    )
    return {"message": f"Dermatologist {data.get('status')}"}
# ================= Get All Users ===============================
async def get_all_users_service(skip, limit, role):
    users = get_users_collection()
    query = {"role": role} if role else {}

    results = await users.find(query).skip(skip).limit(limit).to_list(None)

    cleaned = []
    for u in results:
        u["id"] = str(u["_id"])
        del u["_id"]
        u.pop("password", None)
        u.pop("verification_token", None)
        u.pop("token_expiry", None)
        u.pop("emailLower", None)
        
        # Transform field names to match frontend expectations
        if "is_verified" in u:
            u["isVerified"] = u.pop("is_verified")
        
        cleaned.append(u)

    return {"users": cleaned, "total": len(cleaned)}

# ================= Suspend / Unsuspend / Delete ===============
async def suspend_user_service(user_id, current_admin):
    users = get_users_collection()
    obj = ObjectId(user_id)

    # Fetch user before suspension to get email and name
    user = await users.find_one({"_id": obj}, {"email": 1, "name": 1, "username": 1})
    
    result = await users.update_one(
        {"_id": obj},
        {"$set": {"isSuspended": True, "suspendedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Send suspension notification email
    if user:
        await send_account_suspended_email(
            user.get("email"),
            user.get("name") or user.get("username")
        )

    await log_admin_activity(str(current_admin.get("_id", current_admin.get("id", ""))), "Suspended user", {"userId": user_id})
    return {"message": "User suspended successfully"}

async def unsuspend_user_service(user_id, current_admin):
    users = get_users_collection()
    obj = ObjectId(user_id)

    # Fetch user before unsuspending to get email and name
    user = await users.find_one({"_id": obj}, {"email": 1, "name": 1, "username": 1})

    result = await users.update_one(
        {"_id": obj},
        {"$set": {"isSuspended": False, "unsuspendedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Send unsuspension notification email
    if user:
        await send_account_unsuspended_email(
            user.get("email"),
            user.get("name") or user.get("username")
        )

    await log_admin_activity(str(current_admin.get("_id", current_admin.get("id", ""))), "Unsuspended user", {"userId": user_id})
    return {"message": "User unsuspended successfully"}

async def delete_user_service(user_id, current_admin):
    users = get_users_collection()
    verifications = get_dermatologist_verifications_collection()
    obj = ObjectId(user_id)

    # Fetch user before deletion to get email and name
    user = await users.find_one({"_id": obj}, {"email": 1, "name": 1, "username": 1})

    result = await users.delete_one({"_id": obj})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Send deletion notification email
    if user:
        await send_account_deleted_email(
            user.get("email"),
            user.get("name") or user.get("username")
        )

    # Also delete any associated verification requests
    await verifications.delete_many({"dermatologistId": user_id})

    await log_admin_activity(str(current_admin["_id"]), "Deleted user", {"userId": user_id})
    return {"message": "User deleted successfully"}

# ================= Update Profile =============================
async def update_admin_profile_service(current_admin, data):
    users = get_users_collection()

    allowed = {k: v for k, v in data.items() if k in ["name", "email"]}
    allowed["updatedAt"] = datetime.utcnow()

    await users.update_one(
        {"_id": current_admin["_id"]},
        {"$set": allowed}
    )

    await log_admin_activity(str(current_admin["_id"]), "Updated profile", allowed)
    return {"message": "Admin profile updated successfully"}

# ================= Change Password ============================
async def change_password_service(current_admin, data):
    from app.auth.service import verify_password, hash_password

    users = get_users_collection()
    admin = await users.find_one({"_id": current_admin["_id"]})

    if not verify_password(data["currentPassword"], admin["password"]):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    if len(data["newPassword"]) < 8:
        raise HTTPException(status_code=400, detail="Password too short")

    hashed = hash_password(data["newPassword"])

    await users.update_one(
        {"_id": current_admin["_id"]},
        {"$set": {"password": hashed, "updatedAt": datetime.utcnow()}}
    )

    await log_admin_activity(str(current_admin["_id"]), "Changed password")
    return {"message": "Password changed successfully"}

# ================= Activity Logging ============================
async def log_admin_activity(admin_id, action, details=None):
    activity_logs = get_activity_logs_collection()
    log_entry = {
        "adminId": admin_id,
        "action": action,
        "details": details or {},
        "timestamp": datetime.utcnow()
    }
    await activity_logs.insert_one(log_entry)

async def log_user_activity(user_id, action, details=None):
    activity_logs = get_activity_logs_collection()
    log_entry = {
        "userId": user_id,
        "action": action,
        "details": details or {},
        "timestamp": datetime.utcnow()
    }
    await activity_logs.insert_one(log_entry)

async def get_admin_activity_logs_service(skip=0, limit=50):
    activity_logs = get_activity_logs_collection()
    users = get_users_collection()
    predictions = get_predictions_collection()
    
    # Fetch all logs (admin and user)
    all_logs = await activity_logs.find({}).sort("timestamp", -1).skip(skip).limit(limit * 2).to_list(length=None)  # Fetch more to combine
    
    # Fetch user predictions as additional activities
    user_predictions = await predictions.find({}).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=None)
    
    # Format logs
    formatted_logs = []
    for log in all_logs:
        log["id"] = str(log["_id"])
        del log["_id"]
        
        if "adminId" in log:
            admin = await users.find_one({"_id": ObjectId(log["adminId"])})
            if admin:
                log["adminName"] = admin.get("name") or admin.get("username")
                log["adminEmail"] = admin.get("email")
            else:
                log["adminName"] = "Unknown"
                log["adminEmail"] = "N/A"
            log["userType"] = "Admin"
            log["userName"] = log["adminName"]
            log["userEmail"] = log["adminEmail"]
        elif "userId" in log:
            user = await users.find_one({"_id": ObjectId(log["userId"])})
            if user:
                log["userName"] = user.get("name") or user.get("username")
                log["userEmail"] = user.get("email")
                # Determine user type based on role
                user_role = user.get("role", "patient")
                if user_role == "dermatologist":
                    log["userType"] = "Dermatologist"
                else:
                    log["userType"] = "Patient"
            else:
                log["userName"] = "Unknown"
                log["userEmail"] = "N/A"
                log["userType"] = "User"
        formatted_logs.append(log)
    
    # Format user predictions as logs
    formatted_user_logs = []
    for pred in user_predictions:
        user = await users.find_one({"_id": ObjectId(pred["userId"])})
        if user:
            log_entry = {
                "id": str(pred["_id"]),
                "action": "Skin Analysis Prediction",
                "details": {
                    "prediction": pred.get("prediction", "N/A"),
                    "confidence": pred.get("confidence", "N/A")
                },
                "timestamp": pred["createdAt"],
                "userType": "User",
                "userName": user.get("name") or user.get("username"),
                "userEmail": user.get("email")
            }
            formatted_user_logs.append(log_entry)
    
    # Combine all
    all_combined_logs = formatted_logs + formatted_user_logs
    all_combined_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Apply limit
    return all_combined_logs[:limit]
