from fastapi import APIRouter, HTTPException, status, Request
from app.auth.schemas import (
    SignupRequest, LoginRequest, LoginResponse, 
    MessageResponse, ErrorResponse, UserResponse
)
from app.auth.service import (
    get_user_by_email, get_user_by_username,
    create_user, verify_password, create_access_token
)
from app.email.mailer import send_welcome_email, send_login_notification_email
import asyncio
from pydantic import ValidationError

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request, checking X-Forwarded-For header"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def signup(signup_data: SignupRequest):
    """
    Register a new user
    
    Validations:
    - role must be "patient" or "dermatologist"
    - username: required, unique, no spaces
    - email: required, unique, lowercased
    - password: required
    """
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(signup_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Email or username already exists"}
            )
        
        existing_user = await get_user_by_username(signup_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Email or username already exists"}
            )
        
        # Create user
        user = await create_user(
            role=signup_data.role,
            username=signup_data.username,
            email=signup_data.email,
            password=signup_data.password
        )
        
        # Send welcome email asynchronously (don't await)
        asyncio.create_task(
            send_welcome_email(user["email"], user["username"])
        )
        
        return {"message": "User registered successfully"}
        
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "All fields are required"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "All fields are required"}
        )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """
    Authenticate user and return JWT token
    
    Validates:
    - All fields required (emailOrUsername, password, role)
    - User exists by email or username
    - Password is correct
    - Role matches stored role
    """
    # Check if all fields provided
    if not login_data.emailOrUsername or not login_data.password or not login_data.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "All fields are required"}
        )
    
    # Find user by email or username
    user = await get_user_by_email(login_data.emailOrUsername)
    if not user:
        user = await get_user_by_username(login_data.emailOrUsername)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "User Not Found"}
        )
    
    # Verify password
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid Password"}
        )
    
    # Check role match
    if user["role"] != login_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"Role mismatch. You are registered as a {user['role']}."}
        )
    
    # Create JWT token
    token_data = {
        "id": str(user["_id"]),
        "role": user["role"]
    }
    token = create_access_token(token_data)
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Send login notification email asynchronously
    asyncio.create_task(
        send_login_notification_email(user["email"], user["username"], client_ip)
    )
    
    # Return response
    user_response = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"]
    )
    
    return LoginResponse(token=token, user=user_response)
