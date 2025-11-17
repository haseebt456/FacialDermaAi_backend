from fastapi import APIRouter, Depends, HTTPException, status
from app.users.schemas import (
    UserMeResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    AddMedicalHistoryRequest,
)
from app.deps.auth import get_current_user
from app.db.mongo import get_users_collection
from bson import ObjectId

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires: Bearer token in Authorization header
    Returns: User data excluding password
    """
    return UserMeResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
    )


# ADD THIS NEW ENDPOINT
@router.get("/profile", response_model=UserProfileResponse)
async def get_full_profile(current_user: dict = Depends(get_current_user)):
    """
    Get complete user profile with medical information

    Requires: Bearer token in Authorization header
    Returns: Full user profile data
    """
    return UserProfileResponse(
        # FROM AUTH
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        name=current_user.get("name"),
        # FROM PROFILE
        gender=current_user.get("gender"),
        age=current_user.get("age"),
        height=current_user.get("height"),
        weight=current_user.get("weight"),
        bloodGroup=current_user.get("bloodGroup"),
        phone=current_user.get("phone"),
        emergencyContact=current_user.get("emergencyContact"),
        address=current_user.get("address"),
        allergies=current_user.get("allergies"),
        profileImage=current_user.get("profileImage"),
        medicalHistory=current_user.get("medicalHistory", []),
        recentReports=current_user.get("recentReports", []),
        history=current_user.get("history", []),
    )


@router.put("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    update_data: UpdateProfileRequest, current_user: dict = Depends(get_current_user)
):
    """
    Update user profile information

    NOTE: username, email, role CANNOT be updated here
    They are set during signup and fetched from JWT token

    Requires: Bearer token in Authorization header
    Returns: Updated user profile
    """
    users = get_users_collection()

    # Build update document (ONLY editable fields)
    update_doc = {}

    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.gender is not None:
        update_doc["gender"] = update_data.gender
    if update_data.age is not None:
        update_doc["age"] = update_data.age
    if update_data.height is not None:
        update_doc["height"] = update_data.height
    if update_data.weight is not None:
        update_doc["weight"] = update_data.weight
    if update_data.bloodGroup is not None:
        update_doc["bloodGroup"] = update_data.bloodGroup
    if update_data.phone is not None:
        update_doc["phone"] = update_data.phone
    if update_data.emergencyContact is not None:
        update_doc["emergencyContact"] = update_data.emergencyContact
    if update_data.address is not None:
        update_doc["address"] = update_data.address
    if update_data.allergies is not None:
        update_doc["allergies"] = update_data.allergies
    if update_data.profileImage is not None:
        update_doc["profileImage"] = update_data.profileImage

    if not update_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    # Update ONLY the profile fields (username, email, role stay unchanged)
    await users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": update_doc})

    # Fetch updated user
    updated_user = await users.find_one({"_id": ObjectId(current_user["_id"])})

    return UpdateProfileResponse(
        message="Profile updated successfully",
        user=UserProfileResponse(
            # FROM AUTH (unchanged)
            id=str(updated_user["_id"]),
            username=updated_user["username"],
            email=updated_user["email"],
            role=updated_user["role"],
            name=updated_user.get("name"),
            # FROM PROFILE (updated)
            gender=updated_user.get("gender"),
            age=updated_user.get("age"),
            height=updated_user.get("height"),
            weight=updated_user.get("weight"),
            bloodGroup=updated_user.get("bloodGroup"),
            phone=updated_user.get("phone"),
            emergencyContact=updated_user.get("emergencyContact"),
            address=updated_user.get("address"),
            allergies=updated_user.get("allergies"),
            profileImage=updated_user.get("profileImage"),
            medicalHistory=updated_user.get("medicalHistory", []),
            recentReports=updated_user.get("recentReports", []),
            history=updated_user.get("history", []),
        ),
    )


# ADD THIS NEW ENDPOINT - ADD MEDICAL HISTORY
@router.post("/profile/medical-history")
async def add_medical_history(
    data: AddMedicalHistoryRequest, current_user: dict = Depends(get_current_user)
):
    """
    Add a medical history entry

    Requires: Bearer token in Authorization header
    """
    users = get_users_collection()

    await users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$push": {"medicalHistory": data.entry}},
    )

    return {"message": "Medical history entry added successfully"}
