from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

# from app.users.schemas import UserMeResponse, DermatologistSummary, DermatologistListResponse //commented by Asad
from app.users.schemas import (
    UserMeResponse,
    DermatologistSummary,
    DermatologistListResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.deps.auth import get_current_user, get_current_user_allow_suspended
from app.db.mongo import get_users_collection
from app.auth.service import verify_password, hash_password
from datetime import datetime


router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/check-username")
async def check_username(username: str = Query(..., min_length=2, max_length=50)):
    """
    Check if a username is available.

    Returns:
        { "available": true } when no existing user has this username (case-insensitive)
        { "available": false } when taken
    """
    collection = get_users_collection()
    existing = await collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    return {"available": existing is None}


# commented by Asad
# @router.get("/me", response_model=UserMeResponse)
# async def get_me(current_user: dict = Depends(get_current_user)):
#     """
#     Get current authenticated user information

#     Requires: Bearer token in Authorization header
#     Returns: User data excluding password
#     """
#     return UserMeResponse(
#         id=str(current_user["_id"]),
#         username=current_user["username"],
#         email=current_user["email"],
#         role=current_user["role"],
#     )


# Added by Asad
@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: dict = Depends(get_current_user_allow_suspended)):
    """
    Get current authenticated user's complete profile.
    This endpoint works even for suspended users to allow the frontend to show suspension screen.

    Requires: Bearer token in Authorization header
    Returns: Complete user profile including suspension status
    """
    collection = get_users_collection()
    user = await collection.find_one({"_id": current_user["_id"]})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserMeResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        isSuspended=user.get("isSuspended", False),
        isVerified=user.get("is_verified", False),
        name=user.get("name"),
        gender=user.get("gender"),
        age=user.get("age"),
        height=user.get("height"),
        weight=user.get("weight"),
        bloodGroup=user.get("bloodGroup"),
        phone=user.get("phone"),
        emergencyContact=user.get("emergencyContact"),
        address=user.get("address"),
        allergies=user.get("allergies"),
        medicalHistory=user.get("medicalHistory", []),
        profileImage=user.get("profileImage"),
        specialization=user.get("specialization"),
        license=user.get("license"),
        clinic=user.get("clinic"),
        fees=user.get("fees"),
        experience=user.get("experience"),
        bio=user.get("bio"),
        createdAt=user.get("createdAt"),
        updatedAt=user.get("updatedAt"),
    )


@router.put("/me")
async def update_me(
    profile: UpdateProfileRequest, current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    collection = get_users_collection()

    update_data = {}
    if profile.name is not None:
        update_data["name"] = profile.name
    if profile.gender is not None:
        update_data["gender"] = profile.gender
    if profile.age is not None:
        update_data["age"] = profile.age
    if profile.height is not None:
        update_data["height"] = profile.height
    if profile.weight is not None:
        update_data["weight"] = profile.weight
    if profile.bloodGroup is not None:
        update_data["bloodGroup"] = profile.bloodGroup
    if profile.phone is not None:
        update_data["phone"] = profile.phone
    if profile.emergencyContact is not None:
        update_data["emergencyContact"] = profile.emergencyContact
    if profile.address is not None:
        update_data["address"] = profile.address
    if profile.allergies is not None:
        update_data["allergies"] = profile.allergies
    if profile.profileImage is not None:
        update_data["profileImage"] = profile.profileImage
    if profile.specialization is not None:
        update_data["specialization"] = profile.specialization
    if profile.license is not None:
        # Check if license is unique among dermatologists
        existing = await collection.find_one({
            "role": "dermatologist",
            "license": profile.license,
            "_id": {"$ne": current_user["_id"]}
        })
        if existing:
            raise HTTPException(status_code=400, detail="License number already exists")
        update_data["license"] = profile.license
    if profile.clinic is not None:
        update_data["clinic"] = profile.clinic
    if profile.fees is not None:
        update_data["fees"] = profile.fees
    if profile.experience is not None:
        update_data["experience"] = profile.experience
    if profile.bio is not None:
        update_data["bio"] = profile.bio

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updatedAt"] = datetime.utcnow()
    await collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})

    user = await collection.find_one({"_id": current_user["_id"]})
    # return UserMeResponse(
    #     id=str(user["_id"]),
    #     username=user["username"],
    #     email=user["email"],
    #     role=user["role"],
    #     name=user.get("name"),
    #     gender=user.get("gender"),
    #     age=user.get("age"),
    #     height=user.get("height"),
    #     weight=user.get("weight"),
    #     bloodGroup=user.get("bloodGroup"),
    #     phone=user.get("phone"),
    #     emergencyContact=user.get("emergencyContact"),
    #     address=user.get("address"),
    #     allergies=user.get("allergies"),
    #     medicalHistory=user.get("medicalHistory", []),
    #     profileImage=user.get("profileImage"),
    #     specialization=user.get("specialization"),
    #     license=user.get("license"),
    #     clinic=user.get("clinic"),
    #     fees=user.get("fees"),
    #     experience=user.get("experience"),
    #     bio=user.get("bio"),
    #     createdAt=user.get("createdAt"),
    #     updatedAt=user.get("updatedAt")
    # )
    updated_user = await collection.find_one({"_id": current_user["_id"]})

    return {
        "message": "Profile updated successfully",
        "user": UserMeResponse(
            id=str(updated_user["_id"]),
            username=updated_user["username"],
            email=updated_user["email"],
            role=updated_user["role"],
            name=updated_user.get("name"),
            gender=updated_user.get("gender"),
            age=updated_user.get("age"),
            height=updated_user.get("height"),
            weight=updated_user.get("weight"),
            bloodGroup=updated_user.get("bloodGroup"),
            phone=updated_user.get("phone"),
            emergencyContact=updated_user.get("emergencyContact"),
            address=updated_user.get("address"),
            allergies=updated_user.get("allergies"),
            medicalHistory=updated_user.get("medicalHistory", []),
            profileImage=updated_user.get("profileImage"),
            specialization=updated_user.get("specialization"),
            license=updated_user.get("license"),
            clinic=updated_user.get("clinic"),
            fees=updated_user.get("fees"),
            experience=updated_user.get("experience"),
            bio=updated_user.get("bio"),
            createdAt=updated_user.get("createdAt"),
            updatedAt=updated_user.get("updatedAt"),
        ),
    }


@router.post("/change-password")
async def change_password(
    password_req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password
    
    Requires:
    - Bearer token in Authorization header
    - Current password (for verification)
    - New password (min 8 characters)
    
    Returns:
    - Success message on password change
    """
    collection = get_users_collection()
    
    # Get user with password
    user = await collection.find_one({"_id": current_user["_id"]})
    if not user:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    
    # Verify current password
    if not verify_password(password_req.currentPassword, user["password"]):
        raise HTTPException(
            status_code=400,
            detail={"error": "Current password is incorrect"}
        )
    
    # Validate new password
    if len(password_req.newPassword) < 8:
        raise HTTPException(
            status_code=400,
            detail={"error": "New password must be at least 8 characters long"}
        )
    
    # Check if new password is same as current
    if verify_password(password_req.newPassword, user["password"]):
        raise HTTPException(
            status_code=400,
            detail={"error": "New password must be different from current password"}
        )
    
    # Hash and update password
    hashed_password = hash_password(password_req.newPassword)
    await collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
    )
    
    return {"message": "Password changed successfully"}

# Added by Asad


@router.get("/dermatologists", response_model=DermatologistListResponse)
async def list_dermatologists(
    q: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """
    List all dermatologists in the system.

    Requires: Any authenticated user

    Query params:
        q: Optional search string (filters by username or email prefix)
        limit: Max results (1-100, default 50)
        offset: Skip count for pagination

    Returns:
        200: Paginated list of dermatologists
    """
    collection = get_users_collection()

    # Build query
    query = {"role": "dermatologist"}

    if q:
        # Case-insensitive prefix search on username or email
        query["$or"] = [
            {"username": {"$regex": f"^{q}", "$options": "i"}},
            {"email": {"$regex": f"^{q}", "$options": "i"}},
        ]

    # Count total
    total = await collection.count_documents(query)

    # Fetch paginated results
    cursor = (
        collection.find(query, {"password": 0})
        .sort("createdAt", -1)
        .skip(offset)
        .limit(limit)
    )
    dermatologists = await cursor.to_list(length=limit)

    return DermatologistListResponse(
        dermatologists=[
            DermatologistSummary(
                id=str(d["_id"]),
                username=d["username"],
                email=d["email"],
                createdAt=d["createdAt"],
            )
            for d in dermatologists
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
