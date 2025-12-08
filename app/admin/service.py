# app/admin/service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongo import (
    get_users_collection,
    get_dermatologist_verifications_collection,
    get_predictions_collection,
    get_review_requests_collection
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

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pending verification not found")

    user_obj = ObjectId(dermatologist_id)

    # Update user verification field
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
        cleaned.append(u)

    return {"users": cleaned, "total": len(cleaned)}

# ================= Suspend / Unsuspend / Delete ===============
async def suspend_user_service(user_id):
    users = get_users_collection()
    obj = ObjectId(user_id)

    result = await users.update_one(
        {"_id": obj},
        {"$set": {"isSuspended": True, "suspendedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User suspended successfully"}

async def unsuspend_user_service(user_id):
    users = get_users_collection()
    obj = ObjectId(user_id)

    result = await users.update_one(
        {"_id": obj},
        {"$set": {"isSuspended": False, "unsuspendedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User unsuspended successfully"}

async def delete_user_service(user_id):
    users = get_users_collection()
    obj = ObjectId(user_id)

    result = await users.delete_one({"_id": obj})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

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

    return {"message": "Password changed successfully"}
