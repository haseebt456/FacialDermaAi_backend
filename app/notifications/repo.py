from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.db.mongo import get_notifications_collection
import logging

logger = logging.getLogger(__name__)


async def create_notification(
    user_id: ObjectId,
    notification_type: str,
    message: str,
    ref_data: dict
) -> dict:
    """
    Create a new notification for a user.
    
    Args:
        user_id: ObjectId of the recipient
        notification_type: "review_requested" or "review_submitted"
        message: Notification text
        ref_data: Dict with requestId, predictionId, etc.
    
    Returns:
        Created notification document
    """
    collection = get_notifications_collection()
    
    doc = {
        "userId": user_id,
        "type": notification_type,
        "message": message,
        "ref": ref_data,
        "isRead": False,
        "createdAt": datetime.utcnow()
    }
    
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    
    logger.info(f"Created notification {result.inserted_id} for user {user_id}")
    
    return doc


async def get_notifications_for_user(
    user_id: ObjectId,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[dict], int, int]:
    """
    Get notifications for a user.
    
    Args:
        user_id: ObjectId of the user
        unread_only: If True, return only unread notifications
        limit: Max results per page
        offset: Skip count for pagination
    
    Returns:
        (list of notifications, total count, unread count)
    """
    collection = get_notifications_collection()
    
    # Build query
    query = {"userId": user_id}
    if unread_only:
        query["isRead"] = False
    
    # Count total matching query
    total = await collection.count_documents(query)
    
    # Count unread
    unread_count = await collection.count_documents({"userId": user_id, "isRead": False})
    
    # Fetch paginated results
    cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    return notifications, total, unread_count


async def mark_notification_read(
    notification_id: ObjectId,
    user_id: ObjectId
) -> Optional[dict]:
    """
    Mark a notification as read.
    
    Args:
        notification_id: ObjectId of the notification
        user_id: ObjectId of the user (for ownership check)
    
    Returns:
        Updated notification or None if not found/not owned
    """
    collection = get_notifications_collection()
    
    updated = await collection.find_one_and_update(
        {"_id": notification_id, "userId": user_id},
        {"$set": {"isRead": True}},
        return_document=True
    )
    
    if updated:
        logger.info(f"Marked notification {notification_id} as read")
    
    return updated
