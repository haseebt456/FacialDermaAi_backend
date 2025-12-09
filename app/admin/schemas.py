# app/admin/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DermatologistVerificationResponse(BaseModel):
    id: str
    dermatologistId: str
    documentUrl: Optional[str] = None
    status: str
    submittedAt: datetime
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    license: Optional[str] = None
    specialization: Optional[str] = None
    clinic: Optional[str] = None
    experience: Optional[int] = None
    bio: Optional[str] = None
    reviewComments: Optional[str] = None
    createdAt: Optional[datetime] = None

class DermatologistVerificationRequest(BaseModel):
    status: str
    reviewComments: Optional[str] = None

class AdminDashboardStats(BaseModel):
    totalUsers: int
    totalPatients: int
    totalDermatologists: int
    pendingVerifications: int
    totalPredictions: int
    totalReviewRequests: int
