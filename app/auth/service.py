from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings
from app.db.mongo import get_users_collection
from bson import ObjectId
from typing import Optional
import secrets

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


async def create_user(role: str, name: Optional[str], username: str, email: str, password: str, license: Optional[str] = None, specialization: Optional[str] = None, clinic: Optional[str] = None, experience: Optional[int] = None):
    """Create a new user in the database with email verification (link + OTP)"""
    users = get_users_collection()
    
    email_lower = email.lower()
    
    # Generate secure verification token (link-based)
    verification_token = secrets.token_urlsafe(32)
    token_expiry = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_TOKEN_EXPIRY_MINUTES)

    # Generate 6-digit OTP for email verification (code-based)
    otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
    otp_expiry = datetime.utcnow() + timedelta(minutes=max(10, settings.VERIFICATION_TOKEN_EXPIRY_MINUTES))
    
    user_doc = {
        "role": role,
        "username": username,
        "email": email_lower,
        "emailLower": email_lower,  # For unique index
        "password": hash_password(password),
        "is_verified": False,
        "verification_token": verification_token,
        "token_expiry": token_expiry,
        "email_otp": otp_code,
        "email_otp_expires": otp_expiry,
        "email_otp_attempts": 0,
        "createdAt": datetime.utcnow(),
    }
    
    if name:
        user_doc["name"] = name
    
    # Add dermatologist-specific fields
    if role == "dermatologist":
        if license:
            user_doc["license"] = license
        if specialization:
            user_doc["specialization"] = specialization
        if clinic:
            user_doc["clinic"] = clinic
        if experience is not None:
            user_doc["experience"] = experience
    
    result = await users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return user_doc


async def verify_email_token(token: str) -> Optional[dict]:
    """Verify email token and mark user as verified"""
    users = get_users_collection()
    
    # Find user by token
    user = await users.find_one({"verification_token": token})
    
    if not user:
        return None
    
    # Check if token is expired
    if user.get("token_expiry") and user["token_expiry"] < datetime.utcnow():
        return {"error": "expired"}
    
    # Check if already verified
    if user.get("is_verified"):
        return {"error": "already_verified"}
    
    # Mark as verified and clear token fields
    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"is_verified": True},
            "$unset": {"verification_token": "", "token_expiry": ""}
        }
    )
    
    return user


async def get_user_by_verification_token(token: str):
    """Find user by verification token"""
    users = get_users_collection()
    user = await users.find_one({"verification_token": token})
    return user


async def update_user_password(email: str, new_password: str) -> bool:
    """Update user password"""
    users = get_users_collection()
    email_lower = email.lower()
    
    # Try emailLower first (indexed), fallback to email for older records
    result = await users.update_one(
        {"emailLower": email_lower},
        {"$set": {"password": hash_password(new_password)}}
    )
    
    # If no document was modified, try with email field for older records
    if result.modified_count == 0:
        result = await users.update_one(
            {"email": email_lower},
            {"$set": {"password": hash_password(new_password)}}
        )
    
    return result.modified_count > 0
