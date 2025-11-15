from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
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
