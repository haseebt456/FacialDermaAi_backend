from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from typing import Optional
import logging

from app.notifications.schemas import Notification, NotificationListResponse
from app.notifications.repo import (
    get_notifications_for_user,
    mark_notification_read
)
from app.deps.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def format_notification(doc: dict) -> Notification:
    """Convert MongoDB document to Notification schema"""
    return Notification(
        id=str(doc["_id"]),
        userId=str(doc["userId"]),
        type=doc["type"],
        message=doc["message"],
        ref=doc["ref"],
        isRead=doc["isRead"],
        createdAt=doc["createdAt"]
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unreadOnly: bool = Query(False, description="Return only unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Get notifications for the current user.
    
    Query params:
        unreadOnly: If true, return only unread notifications
        limit: Max results (1-100, default 50)
        offset: Skip count for pagination
    
    Returns:
        200: Paginated list of notifications with counts
    """
    user_id = ObjectId(str(current_user["_id"]))
    
    notifications, total, unread_count = await get_notifications_for_user(
        user_id, unreadOnly, limit, offset
    )
    
    return NotificationListResponse(
        notifications=[format_notification(n) for n in notifications],
        total=total,
        unreadCount=unread_count,
        limit=limit,
        offset=offset
    )


@router.patch("/{id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a notification as read.
    
    Requires: Must be the owner of the notification
    
    Returns:
        204: Notification marked as read
        404: Notification not found or not owned by user
    """
    try:
        notification_id = ObjectId(id)
        user_id = ObjectId(str(current_user["_id"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid notification ID"}
        )
    
    updated = await mark_notification_read(notification_id, user_id)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Notification not found"}
        )
    
    return None
