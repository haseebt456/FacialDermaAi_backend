from fastapi import APIRouter, HTTPException, status, Request
from app.auth.schemas import (
    SignupRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ErrorResponse,
    UserResponse,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.auth.service import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    verify_password,
    create_access_token,
    update_user_password,
    verify_email_token,
)
from app.email.mailer import send_welcome_email, send_login_notification_email, send_otp_email, send_verification_email
import asyncio
from pydantic import ValidationError
import random
import string
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request, checking X-Forwarded-For header"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/signup", status_code=status.HTTP_201_CREATED, response_model=MessageResponse
)
async def signup(signup_data: SignupRequest):
    """
    Register a new user with email verification

    Process:
    1. Validates user data
    2. Creates user with is_verified=False
    3. Generates secure verification token
    4. Sends verification email with link
    5. Token expires in 15 minutes

    Validations:
    - role must be "patient" or "dermatologist"
    - name is optional
    - username: required, unique, no spaces
    - email: required, unique, lowercased
    - password: required
    
    Returns success message asking user to check email
    """
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(signup_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Email already registered"},
            )

        existing_user = await get_user_by_username(signup_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Username already taken"},
            )

        # Create user with verification token
        user = await create_user(
            role=signup_data.role,
            name=signup_data.name,
            username=signup_data.username,
            email=signup_data.email,
            password=signup_data.password,
        )

        # Send verification email asynchronously
        asyncio.create_task(
            send_verification_email(
                user["email"], 
                user["username"], 
                user["verification_token"]
            )
        )

        return {
            "message": "Registration successful! Please check your email to verify your account."
        }

    except ValidationError as e:
        error_msg = str(e.errors()[0]["msg"]) if e.errors() else "Validation error"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": error_msg}
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Signup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Registration failed. Please try again."},
        )


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str):
    """
    Verify user's email address using token from email link
    
    Process:
    1. Validates token exists and is not expired
    2. Checks if email is already verified
    3. Marks user as verified
    4. Deletes token and expiry (single-use token)
    
    Query params:
    - token: Verification token from email link
    
    Returns:
    - Success message if verification successful
    - Error if token invalid, expired, or already used
    """
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Verification token is required"}
            )
        
        # Verify token and update user
        result = await verify_email_token(token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Invalid verification token"}
            )
        
        if isinstance(result, dict) and "error" in result:
            if result["error"] == "expired":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Verification link has expired. Please request a new verification email."}
                )
            elif result["error"] == "already_verified":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Email is already verified. You can now log in."}
                )
        
        return {
            "message": "Email verified successfully! You can now log in to your account."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Email verification failed. Please try again."}
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
            detail={"error": "All fields are required"},
        )

    # Find user by email or username
    user = await get_user_by_email(login_data.emailOrUsername)
    if not user:
        user = await get_user_by_username(login_data.emailOrUsername)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "User Not Found"}
        )

    # Verify password
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid Password"},
        )

    # Check role match
    if user["role"] != login_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"Role mismatch. You are registered as a {user['role']}."},
        )
    
    # Check email verification (only for users registered via /register endpoint)
    if "is_verified" in user and not user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Email not verified. Please check your inbox and verify your email address."},
        )

    # Create JWT token
    token_data = {"id": str(user["_id"]), "role": user["role"]}
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
        role=user["role"],
        name=user.get("name")
    )

    return LoginResponse(token=token, user=user_response)


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request_data: ForgotPasswordRequest):
    """
    Send OTP to user's email for password reset
    
    Process:
    - Validates email exists in database
    - Generates 6-digit OTP
    - Stores OTP with 10-minute expiration
    - Sends OTP via email
    """
    try:
        # Check if user exists
        user = await get_user_by_email(request_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No account found with this email address"}
            )
        
        # Generate OTP
        otp = generate_otp()
        otp_expires = datetime.utcnow() + timedelta(minutes=10)
        
        # Store OTP in user document
        from app.db.mongo import get_users_collection
        users_collection = get_users_collection()
        
        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "resetOtp": otp,
                    "resetOtpExpires": otp_expires
                }
            }
        )
        
        # Send OTP email asynchronously
        asyncio.create_task(send_otp_email(user["email"], user["username"], otp))
        
        return {"message": "OTP sent to your email address. Please check your inbox."}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Forgot password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process forgot password request"}
        )


@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(request_data: VerifyOTPRequest):
    """
    Verify the OTP sent to user's email
    
    Validations:
    - Email and OTP must match stored values
    - OTP must not be expired (10-minute window)
    """
    try:
        # Find user with matching email and OTP
        from app.db.mongo import get_users_collection
        users_collection = get_users_collection()
        
        user = await users_collection.find_one({
            "email": request_data.email.lower(),
            "resetOtp": request_data.otp
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid OTP"}
            )
        
        # Check if OTP is expired
        if user.get("resetOtpExpires") and user["resetOtpExpires"] < datetime.utcnow():
            # Clear expired OTP
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"resetOtp": "", "resetOtpExpires": ""}}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "OTP has expired. Please request a new one."}
            )
        
        return {"message": "OTP verified successfully. You can now reset your password."}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Verify OTP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to verify OTP"}
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request_data: ResetPasswordRequest):
    """
    Reset user's password after OTP verification
    
    Process:
    - Validates email and OTP one final time
    - Updates password with new hashed password
    - Clears OTP fields from database
    """
    try:
        # Verify OTP one more time before resetting
        from app.db.mongo import get_users_collection
        users_collection = get_users_collection()
        
        user = await users_collection.find_one({
            "email": request_data.email.lower(),
            "resetOtp": request_data.otp
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid OTP or email"}
            )
        
        # Check if OTP is expired
        if user.get("resetOtpExpires") and user["resetOtpExpires"] < datetime.utcnow():
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"resetOtp": "", "resetOtpExpires": ""}}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "OTP has expired. Please request a new one."}
            )
        
        # Update password
        await update_user_password(request_data.email, request_data.newPassword)
        
        # Clear OTP fields
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$unset": {"resetOtp": "", "resetOtpExpires": ""}}
        )
        
        return {"message": "Password reset successfully. You can now login with your new password."}
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to reset password"}
        )
