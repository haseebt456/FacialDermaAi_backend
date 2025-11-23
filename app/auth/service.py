from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings
from app.db.mongo import get_users_collection
from bson import ObjectId
from typing import Optional

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Ensure password is properly encoded and within bcrypt's 72-byte limit
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRATION_DAYS)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_user_by_email(email: str):
    """Find user by email (case-insensitive)"""
    users = get_users_collection()
    email_lower = email.lower()
    # Try emailLower first (indexed), fallback to email for older records
    user = await users.find_one({"emailLower": email_lower})
    if not user:
        user = await users.find_one({"email": email_lower})
    return user


async def get_user_by_username(username: str):
    """Find user by username"""
    users = get_users_collection()
    user = await users.find_one({"username": username})
    return user


async def get_user_by_id(user_id: str):
    """Find user by ID"""
    users = get_users_collection()
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        return user
    except:
        return None


async def create_user(role: str, name: Optional[str], username: str, email: str, password: str):
    """Create a new user in the database"""
    users = get_users_collection()
    
    email_lower = email.lower()
    
    user_doc = {
        "role": role,
        "username": username,
        "email": email_lower,
        "emailLower": email_lower,  # For unique index
        "password": hash_password(password),
        "createdAt": datetime.utcnow(),
    }
    
    if name:                      # ADD THIS - Only include if provided
        user_doc["name"] = name
    

    result = await users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return user_doc


async def update_user_password(email: str, new_password: str) -> bool:
    """Update user password"""
    users = get_users_collection()
    email_lower = email.lower()
    
    result = await users.update_one(
        {"emailLower": email_lower},
        {"$set": {"password": hash_password(new_password)}}
    )
    
    return result.modified_count > 0
