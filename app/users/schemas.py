from pydantic import BaseModel, field_validator
from typing import Optional, List
import re


class UserMeResponse(BaseModel):
    """Response for GET /api/users/me"""

    id: str
    username: str
    email: str
    role: str


class MedicalReport(BaseModel):
    """Medical report or history entry"""

    id: int
    title: str
    date: str


class UserProfileResponse(BaseModel):
    """Complete user profile with medical information"""

    # FROM AUTH (read-only)
    id: str
    username: str
    email: str
    role: str
    name: Optional[str] = None

    # EDITABLE PROFILE FIELDS
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
    medicalHistory: List[str] = []
    recentReports: List[MedicalReport] = []
    history: List[MedicalReport] = []


class UpdateProfileRequest(BaseModel):
    """Request to update user profile - EXCLUDES username, email, role"""

    # NOTE: username, email, role are NOT here - they come from auth

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

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["Male", "Female", "Other"]:
            raise ValueError("Gender must be Male, Female, or Other")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        if v and (v < 0 or v > 150):
            raise ValueError("Age must be between 0 and 150")
        return v

    @field_validator("phone", "emergencyContact")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\+?[\d\s\-()]+$", v):
            raise ValueError("Invalid phone number format")
        return v


class UpdateProfileResponse(BaseModel):
    """Response after updating profile"""

    message: str
    user: UserProfileResponse


class AddMedicalHistoryRequest(BaseModel):
    """Request to add medical history entry"""

    entry: str
