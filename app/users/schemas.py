from pydantic import BaseModel
from datetime import datetime

#imported by Asad
from typing import Optional

# class UserMeResponse(BaseModel):
#     """Response for GET /api/users/me"""

#     id: str
#     username: str
#     email: str
#     role: str


# New User Schema Added By Asad to match the front end profile
class UserMeResponse(BaseModel):
    """Response for GET /api/users/me"""

    id: str
    username: str
    email: str
    role: str
    
    name: Optional[str] = None
    
    # Patient fields
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    bloodGroup: Optional[str] = None
    phone: Optional[str] = None
    emergencyContact: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[str] = None
    medicalHistory: Optional[list[str]] = None
    profileImage: Optional[str] = None
    
    # Dermatologist fields
    specialization: Optional[str] = None
    license: Optional[str] = None
    clinic: Optional[str] = None
    fees: Optional[float] = None
    experience: Optional[int] = None
    bio: Optional[str] = None
    
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class UpdateProfileRequest(BaseModel):
    """Request to update user profile"""
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    bloodGroup: Optional[str] = None
    phone: Optional[str] = None
    emergencyContact: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[str] = None
    profileImage: Optional[str] = None
    specialization: Optional[str] = None
    license: Optional[str] = None
    clinic: Optional[str] = None
    fees: Optional[float] = None
    experience: Optional[int] = None
    bio: Optional[str] = None

# Added by Asad

class DermatologistSummary(BaseModel):
    """Response for dermatologist list items"""
    id: str
    username: str
    email: str
    createdAt: datetime


class DermatologistListResponse(BaseModel):
    """Response for paginated dermatologist list"""
    dermatologists: list[DermatologistSummary]
    total: int
    limit: int
    offset: int
