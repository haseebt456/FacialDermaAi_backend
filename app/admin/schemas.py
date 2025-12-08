# app/admin/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DermatologistVerificationResponse(BaseModel):
    id: str
    dermatologistId: str
    documentUrl: str
    status: str
    submittedAt: datetime
    name: Optional[str]
    email: Optional[str]
    username: Optional[str]
    reviewComments: Optional[str] = None

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
