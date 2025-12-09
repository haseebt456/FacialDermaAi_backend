"""
Thin compatibility shim that re-exports the canonical Mongo helpers
from app.db.mongo. This avoids duplication and keeps a single source of truth.
"""

from .mongo import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    get_users_collection,
    get_predictions_collection,
    get_review_requests_collection,
    get_notifications_collection,
    get_activity_logs_collection,
)

__all__ = [
    "connect_to_mongo",
    "close_mongo_connection",
    "get_database",
    "get_users_collection",
    "get_predictions_collection",
    "get_review_requests_collection",
    "get_notifications_collection",
    "get_activity_logs_collection",
]
