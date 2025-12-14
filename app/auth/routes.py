from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import ValidationError
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
    ResendVerificationRequest,
)
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.mongo import get_users_collection
from app.auth.service import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    verify_password,
    create_access_token,
    update_user_password,
    verify_email_token,
)
from app.email.mailer import (
    send_welcome_email,
    send_login_notification_email,
    send_otp_email,
    send_verification_email,
)
from app.admin.service import log_user_activity
from app.deps.auth import get_current_user
from app.db.mongo import get_users_collection
import asyncio
from datetime import datetime, timedelta
import random
import string

router = APIRouter(prefix="/api/auth", tags=["auth"])
@router.post("/verify-email-otp", response_model=MessageResponse)
async def verify_email_otp(request_data: VerifyOTPRequest):
    """
    Verify user's email using a 6-digit OTP code.

    Process:
    1. Validates email exists
    2. Checks OTP matches and is not expired
    3. Marks user as verified
    4. Clears verification_token, token_expiry, email_otp, email_otp_expires
    """
    try:
        users = get_users_collection()
        email_lower = request_data.email.lower()

        user = await users.find_one({"emailLower": email_lower})
        if not user:
            # Fallback to email field for older records
            user = await users.find_one({"email": email_lower})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No account found with this email address"})

        # Rate-limit / lock check
        lock_until = user.get("email_otp_lock_until")
        if lock_until and lock_until > datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"error": "Too many failed attempts. Try again later."})

        # Validate OTP
        if request_data.otp != user.get("email_otp"):
            attempts = int(user.get("email_otp_attempts", 0)) + 1
            update = {"$set": {"email_otp_attempts": attempts}}
            # Lock after 5 failed attempts for 15 minutes
            if attempts >= 5:
                update["$set"]["email_otp_lock_until"] = datetime.utcnow() + timedelta(minutes=15)
            await users.update_one({"_id": user["_id"]}, update)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Invalid OTP"})

        # Check expiry
        if user.get("email_otp_expires") and user["email_otp_expires"] < datetime.utcnow():
            # Clear expired
            await users.update_one({"_id": user["_id"]}, {"$unset": {"email_otp": "", "email_otp_expires": ""}, "$set": {"email_otp_attempts": 0}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "OTP has expired. Please request a new one."})

        # Success: mark verified and clear fields
        await users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"is_verified": True, "email_otp_attempts": 0},
                "$unset": {"verification_token": "", "token_expiry": "", "email_otp": "", "email_otp_expires": "", "email_otp_lock_until": ""}
            }
        )

        message = "Email verified successfully!"
        if user.get("role") == "dermatologist":
            message = "Email verified successfully! Your account is pending admin approval. You will be notified once approved."

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Email OTP verification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Email OTP verification failed. Please try again."})


@router.post("/verification/resend", response_model=MessageResponse)
async def resend_verification_email(request_data: ResendVerificationRequest):
    """
    Resend verification email with new token and OTP.

    Flow:
    1. Email verification must be completed first
    2. Then dermatologist admin approval (if applicable)

    Rate limiting: Max 3 resends per 15 minutes per email.
    """
    try:
        users = get_users_collection()
        email_lower = request_data.email.lower()

        # Find user
        user = await users.find_one({"emailLower": email_lower})
        if not user:
            user = await users.find_one({"email": email_lower})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No account found with this email address"}
            )

        # Check if already verified
        if user.get("is_verified"):
            # Check dermatologist approval status
            if user.get("role") == "dermatologist":
                if user.get("is_approved") == "pending":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"error": "Email already verified. Your account is pending admin approval."}
                    )
                elif user.get("is_approved") == "rejected":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"error": "Email already verified. Your dermatologist application was rejected."}
                    )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Email is already verified. You can log in."}
            )

        # Rate limiting: check resend attempts
        resend_lock_until = user.get("resend_lock_until")
        if resend_lock_until and resend_lock_until > datetime.utcnow():
            remaining_mins = int((resend_lock_until - datetime.utcnow()).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": f"Too many resend attempts. Please try again in {remaining_mins} minutes."}
            )

        resend_attempts = user.get("resend_attempts", 0)
        last_resend = user.get("last_resend_at")

        # Reset counter if last resend was more than 15 minutes ago
        if last_resend and (datetime.utcnow() - last_resend).total_seconds() > 900:
            resend_attempts = 0

        # Check if max resends reached
        if resend_attempts >= 3:
            lock_until = datetime.utcnow() + timedelta(minutes=15)
            await users.update_one(
                {"_id": user["_id"]},
                {"$set": {"resend_lock_until": lock_until}}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "Too many resend attempts. Please try again in 15 minutes."}
            )

        # Generate new verification token
        import secrets
        new_token = secrets.token_urlsafe(32)
        token_expiry = datetime.utcnow() + timedelta(minutes=15)

        # Generate new 6-digit OTP
        new_otp = ''.join(random.choices(string.digits, k=6))
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)

        # Update user with new token and OTP
        await users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "verification_token": new_token,
                    "token_expiry": token_expiry,
                    "email_otp": new_otp,
                    "email_otp_expires": otp_expiry,
                    "email_otp_attempts": 0,
                    "resend_attempts": resend_attempts + 1,
                    "last_resend_at": datetime.utcnow(),
                },
                "$unset": {
                    "email_otp_lock_until": "",
                    "resend_lock_until": ""
                }
            }
        )

        # Send verification email
        asyncio.create_task(
            send_verification_email(
                user["email"], user["username"], new_token, new_otp
            )
        )

        remaining_attempts = 3 - (resend_attempts + 1)
        message = f"Verification email sent! Please check your inbox. ({remaining_attempts} resend(s) remaining)"

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Resend verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to resend verification email. Please try again."}
        )


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
        users = get_users_collection()
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

        # Check license uniqueness for dermatologists
        if signup_data.role == "dermatologist":
            existing_license = await users.find_one({"license": signup_data.license, "role": "dermatologist"})
            if existing_license:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "License number already registered to another dermatologist"},
                )

        # Create user with verification token
        user = await create_user(
            role=signup_data.role,
            name=signup_data.name,
            username=signup_data.username,
            email=signup_data.email,
            password=signup_data.password,
            license=signup_data.license,
        )

        # Log user registration
        await log_user_activity(str(user["_id"]), "User Registration", {"role": signup_data.role})

        # If dermatologist, create verification request automatically
        if signup_data.role == "dermatologist":
            from app.db.mongo import get_dermatologist_verifications_collection
            verifications = get_dermatologist_verifications_collection()
            
            verification_doc = {
                "dermatologistId": str(user["_id"]),
                "status": "pending",
                "license": signup_data.license,
                "specialization": None,
                "clinic": None,
                "experience": None,
                "bio": None,
                "submittedAt": datetime.utcnow(),
                "createdAt": datetime.utcnow(),
            }
            
            await verifications.insert_one(verification_doc)
            
            # TODO: Send notification to admin about new dermatologist registration
            # You can implement email notification to admin here

        # Send verification email asynchronously
        asyncio.create_task(
            send_verification_email(
                user["email"], user["username"], user["verification_token"], user.get("email_otp")
            )
        )

        message = "Registration successful! Please check your email to verify your account."
        if signup_data.role == "dermatologist":
            message = "Registration successful! Please verify your email. Your dermatologist account will be activated after admin approval."
        
        return {"message": message}

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
                detail={"error": "Verification token is required"},
            )

        # Verify token and update user
        result = await verify_email_token(token)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Invalid verification token"},
            )

        if isinstance(result, dict) and "error" in result:
            if result["error"] == "expired":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Verification link has expired. Please request a new verification email."
                    },
                )
            elif result["error"] == "already_verified":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Email is already verified. You can now log in."},
                )

        # Check if user is a dermatologist
        message = "Email verified successfully! You can now log in to your account."
        if result and result.get("role") == "dermatologist":
            message = "Email verified successfully! Your account is pending admin approval. You will be notified once approved."
        
        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        import logging

        logging.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Email verification failed. Please try again."},
        )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """
    Authenticate user and return JWT token

    Validates:
    - All fields required (password, role)
    - User exists by email or username
    - Password is correct
    - Role retrieve from DB automatically and matched
    """
    # Check if required fields provided
    if not login_data.emailOrUsername or not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email/Username and Password fields are required"},
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
    if login_data.role and user["role"] != login_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"Role mismatch. You are registered as a {user['role']}."},
        )

    # Check if user is suspended
    if user.get("isSuspended", False):
        # Allow login but return suspension status in response
        # The frontend will handle showing the suspension screen
        pass
    
    # Step 1: Check email verification (applies to all users)
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Email not verified. Please check your inbox and verify your email address."
            },
        )
    
    # Step 2: For dermatologists, check admin approval status
    if user["role"] == "dermatologist":
        from app.db.mongo import get_dermatologist_verifications_collection
        verifications = get_dermatologist_verifications_collection()
        verification = await verifications.find_one({"dermatologistId": str(user["_id"])})
        
        if not verification:
            # No verification record found - shouldn't happen but handle gracefully
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Dermatologist verification record not found. Please contact support."
                },
            )
        
        if verification.get("status") == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Your account is pending admin approval. You will be notified once approved."
                },
            )
        elif verification.get("status") == "rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Your dermatologist verification was rejected. Reason: {verification.get('reviewComments', 'No reason provided')}"
                },
            )

    # Create JWT token
    token_data = {"id": str(user["_id"]), "role": user["role"]}
    token = create_access_token(token_data)

    # Get client IP
    client_ip = get_client_ip(request)
    
    # Get user agent
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Send login notification email asynchronously
    asyncio.create_task(
        send_login_notification_email(user["email"], user["username"], client_ip, user_agent)
    )

    # Log user login
    await log_user_activity(str(user["_id"]), "User Login", {"ip": client_ip, "userAgent": user_agent})

    # Return response
    user_response = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        name=user.get("name"),
        isSuspended=user.get("isSuspended", False),
    )

    return LoginResponse(token=token, user=user_response)


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return "".join(random.choices(string.digits, k=6))


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
                detail={"error": "No account found with this email address"},
            )

        # Generate OTP
        otp = generate_otp()
        otp_expires = datetime.utcnow() + timedelta(minutes=10)

        # Store OTP in user document
        from app.db.mongo import get_users_collection

        users_collection = get_users_collection()

        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"resetOtp": otp, "resetOtpExpires": otp_expires}},
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
            detail={"error": "Failed to process forgot password request"},
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

        user = await users_collection.find_one(
            {"email": request_data.email.lower(), "resetOtp": request_data.otp}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Invalid OTP"}
            )

        # Check if OTP is expired
        if user.get("resetOtpExpires") and user["resetOtpExpires"] < datetime.utcnow():
            # Clear expired OTP
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"resetOtp": "", "resetOtpExpires": ""}},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "OTP has expired. Please request a new one."},
            )

        return {
            "message": "OTP verified successfully. You can now reset your password."
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging

        logging.error(f"Verify OTP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to verify OTP"},
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

        user = await users_collection.find_one(
            {"email": request_data.email.lower(), "resetOtp": request_data.otp}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid OTP or email"},
            )

        # Check if OTP is expired
        if user.get("resetOtpExpires") and user["resetOtpExpires"] < datetime.utcnow():
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$unset": {"resetOtp": "", "resetOtpExpires": ""}},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "OTP has expired. Please request a new one."},
            )

        # Update password
        await update_user_password(request_data.email, request_data.newPassword)

        # Clear OTP fields
        await users_collection.update_one(
            {"_id": user["_id"]}, {"$unset": {"resetOtp": "", "resetOtpExpires": ""}}
        )

        return {
            "message": "Password reset successfully. You can now login with your new password."
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging

        logging.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to reset password"},
        )
