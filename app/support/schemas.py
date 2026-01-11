# app/support/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SupportTicketCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: str  # Account, Technical, Payment, General, etc.
    message: str
    userId: Optional[str] = None  # Optional if user is logged in


class SupportTicketResponse(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    category: str
    message: str
    status: str  # open, in-progress, resolved, closed
    userId: Optional[str] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    adminResponse: Optional[str] = None
    respondedBy: Optional[str] = None
    respondedAt: Optional[datetime] = None


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    adminResponse: Optional[str] = None
