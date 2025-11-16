from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class Notification(BaseModel):
    """Schema for notification response"""
    id: str
    userId: str
    type: Literal["review_requested", "review_submitted"]
    message: str
    ref: dict  # Contains requestId, predictionId, etc.
    isRead: bool
    createdAt: datetime


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list"""
    notifications: list[Notification]
    total: int
    unreadCount: int
    limit: int
    offset: int
