from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global MongoDB client
mongo_client = None


async def connect_to_mongo():
    """Initialize MongoDB connection"""
    global mongo_client
    try:
        mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
        # Verify connection by pinging the database
        await mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        print(f"Connected to MongoDB at {settings.MONGO_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Closed MongoDB connection")


def get_database():
    """Get the database instance"""
    return mongo_client[settings.DB_NAME]


def get_users_collection():
    """Get users collection"""
    db = get_database()
    return db["users"]


def get_predictions_collection():
    """Get predictions collection"""
    db = get_database()
    return db["predictions"]


def get_review_requests_collection():
    """Get review_requests collection"""
    db = get_database()
    return db["review_requests"]


def get_notifications_collection():
    """Get notifications collection"""
    db = get_database()
    return db["notifications"]


async def ensure_indexes():
    """
    Create indexes for all collections to optimize queries and enforce constraints.
    Called once during application startup.
    """
    try:
        # Users collection: migrate existing users first
        users = get_users_collection()
        
        # Migration: Add emailLower to existing users that don't have it
        result = await users.update_many(
            {"emailLower": {"$exists": False}},
            [{"$set": {"emailLower": {"$toLower": "$email"}}}]
        )
        if result.modified_count > 0:
            logger.info(f"Migrated {result.modified_count} users to add emailLower field")
        
        # Add createdAt to users without it
        result = await users.update_many(
            {"createdAt": {"$exists": False}},
            [{"$set": {"createdAt": datetime.utcnow()}}]
        )
        if result.modified_count > 0:
            logger.info(f"Added createdAt to {result.modified_count} users")
        
        # Drop old index if it exists (non-sparse version)
        try:
            await users.drop_index("emailLower_1")
            logger.info("Dropped old emailLower index")
        except Exception:
            pass  # Index might not exist
        
        # Create indexes
        await users.create_index("emailLower", unique=True, sparse=True)
        await users.create_index("username", unique=True)
        await users.create_index("role")
        logger.info("Created indexes on users collection")
        
        # Predictions collection indexes
        predictions = get_predictions_collection()
        await predictions.create_index("userId")
        await predictions.create_index([("createdAt", -1)])
        logger.info("Created indexes on predictions collection")
        
        # Review requests collection indexes
        review_requests = get_review_requests_collection()
        await review_requests.create_index(
            [("predictionId", 1), ("dermatologistId", 1)],
            unique=True
        )
        await review_requests.create_index([("dermatologistId", 1), ("status", 1), ("createdAt", -1)])
        await review_requests.create_index([("patientId", 1), ("status", 1), ("createdAt", -1)])
        await review_requests.create_index("predictionId")
        logger.info("Created indexes on review_requests collection")
        
        # Notifications collection indexes
        notifications = get_notifications_collection()
        await notifications.create_index([("userId", 1), ("isRead", 1), ("createdAt", -1)])
        logger.info("Created indexes on notifications collection")
        
        logger.info("All database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {str(e)}")
