import asyncio
import sys
import os

# Add the parent directory to the Python path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mongo import connect_to_mongo, close_mongo_connection, get_database, get_dermatologist_verifications_collection
from app.auth.service import hash_password
from datetime import datetime

async def init_admin_system():
    """Initialize admin system with collections and default admin user"""

    await connect_to_mongo()
    db = get_database()

    # Create dermatologist_verifications collection with indexes
    verifications_collection = get_dermatologist_verifications_collection()

    # Create indexes
    await verifications_collection.create_index("dermatologistId")
    await verifications_collection.create_index("status")
    await verifications_collection.create_index([("createdAt", -1)])

    print("✓ Created dermatologist_verifications collection with indexes")

    # Create default admin user
    users_collection = db["users"]

    # Check if admin already exists
    existing_admin = await users_collection.find_one({"email": "admin@facialderma.com"})
    if existing_admin:
        print("✓ Admin user already exists")
    else:
        admin_data = {
            "username": "admin",
            "email": "admin@facialdermaai.com",
            "password": hash_password("Admin@123"),  # Change this password in production
            "role": "admin",
            "name": "System Administrator",
            "is_verified": True,
            "adminPermissions": {
                "canVerifyDermatologists": True,
                "canManageUsers": True,
                "canViewAnalytics": True,
                "canManageContent": True
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await users_collection.insert_one(admin_data)
        print(f"✓ Created admin user with ID: {result.inserted_id}")
        print("   Email: admin@facialderma.com")
        print("   Password: admin123 (CHANGE THIS IN PRODUCTION!)")

    await close_mongo_connection()
    print("✓ Admin system initialization complete")

if __name__ == "__main__":
    asyncio.run(init_admin_system())