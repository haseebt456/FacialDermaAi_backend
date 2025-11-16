from pydantic import BaseModel
from datetime import datetime


class UserMeResponse(BaseModel):
    """Response for GET /api/users/me"""
    id: str
    username: str
    email: str
    role: str


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
