from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
# from app.users.schemas import UserMeResponse, DermatologistSummary, DermatologistListResponse //commented by Asad
from app.users.schemas import (
    UserMeResponse, 
    DermatologistSummary, 
    DermatologistListResponse,
    UpdateProfileRequest,
    AddMedicalHistoryRequest
)
from app.deps.auth import get_current_user
from app.db.mongo import get_users_collection
from datetime import datetime


router = APIRouter(prefix="/api/users", tags=["users"])


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
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's complete profile

    Requires: Bearer token in Authorization header
    Returns: Complete user profile
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
        updatedAt=user.get("updatedAt")
    )

@router.put("/me", response_model=UserMeResponse)
async def update_me(profile: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    collection = get_users_collection()
    
    update_data = {}
    if profile.name is not None: update_data["name"] = profile.name
    if profile.gender is not None: update_data["gender"] = profile.gender
    if profile.age is not None: update_data["age"] = profile.age
    if profile.height is not None: update_data["height"] = profile.height
    if profile.weight is not None: update_data["weight"] = profile.weight
    if profile.bloodGroup is not None: update_data["bloodGroup"] = profile.bloodGroup
    if profile.phone is not None: update_data["phone"] = profile.phone
    if profile.emergencyContact is not None: update_data["emergencyContact"] = profile.emergencyContact
    if profile.address is not None: update_data["address"] = profile.address
    if profile.allergies is not None: update_data["allergies"] = profile.allergies
    if profile.profileImage is not None: update_data["profileImage"] = profile.profileImage
    if profile.specialization is not None: update_data["specialization"] = profile.specialization
    if profile.license is not None: update_data["license"] = profile.license
    if profile.clinic is not None: update_data["clinic"] = profile.clinic
    if profile.fees is not None: update_data["fees"] = profile.fees
    if profile.experience is not None: update_data["experience"] = profile.experience
    if profile.bio is not None: update_data["bio"] = profile.bio
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updatedAt"] = datetime.utcnow()
    await collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    
    user = await collection.find_one({"_id": current_user["_id"]})
    return UserMeResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
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
        updatedAt=user.get("updatedAt")
    )

@router.post("/me/medical-history", response_model=UserMeResponse)
async def add_medical_history(request: AddMedicalHistoryRequest, current_user: dict = Depends(get_current_user)):
    """Add medical history entry"""
    collection = get_users_collection()
    
    await collection.update_one(
        {"_id": current_user["_id"]},
        {"$push": {"medicalHistory": request.entry}, "$set": {"updatedAt": datetime.utcnow()}}
    )
    
    user = await collection.find_one({"_id": current_user["_id"]})
    return UserMeResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
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
        updatedAt=user.get("updatedAt")
    )

@router.delete("/me/medical-history/{index}", response_model=UserMeResponse)
async def delete_medical_history(index: int, current_user: dict = Depends(get_current_user)):
    """Delete medical history entry by index"""
    collection = get_users_collection()
    
    user = await collection.find_one({"_id": current_user["_id"]})
    medical_history = user.get("medicalHistory", [])
    
    if index < 0 or index >= len(medical_history):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    medical_history.pop(index)
    await collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"medicalHistory": medical_history, "updatedAt": datetime.utcnow()}}
    )
    
    user = await collection.find_one({"_id": current_user["_id"]})
    return UserMeResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
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
        updatedAt=user.get("updatedAt")
    )

#Added by Asad

@router.get("/dermatologists", response_model=DermatologistListResponse)
async def list_dermatologists(
    q: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
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
            {"email": {"$regex": f"^{q}", "$options": "i"}}
        ]
    
    # Count total
    total = await collection.count_documents(query)
    
    # Fetch paginated results
    cursor = collection.find(query, {"password": 0}).sort("createdAt", -1).skip(offset).limit(limit)
    dermatologists = await cursor.to_list(length=limit)
    
    return DermatologistListResponse(
        dermatologists=[
            DermatologistSummary(
                id=str(d["_id"]),
                username=d["username"],
                email=d["email"],
                createdAt=d["createdAt"]
            )
            for d in dermatologists
        ],
        total=total,
        limit=limit,
        offset=offset
    )
