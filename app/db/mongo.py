from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Global MongoDB client
mongo_client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Initialize MongoDB connection"""
    global mongo_client
    mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    print(f"Connected to MongoDB at {settings.MONGO_URI}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Closed MongoDB connection")


def get_database():
    """Get the database instance"""
    return mongo_client.get_default_database()


def get_users_collection():
    """Get users collection"""
    db = get_database()
    return db["users"]


def get_predictions_collection():
    """Get predictions collection"""
    db = get_database()
    return db["predictions"]
