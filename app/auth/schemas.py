from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Literal, Optional, List
from datetime import datetime
import re


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    role: Literal["patient", "dermatologist"]
    name: Optional[str] = None
    username: str
    email: EmailStr
    password: str
    license: Optional[str] = None  # License number for dermatologists

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v:
            raise ValueError("Username is required")
        if not re.match(r"^\S+$", v):
            raise ValueError("Username cannot contain spaces")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v
    
    @field_validator("license")
    @classmethod
    def validate_license(cls, v: Optional[str], info) -> Optional[str]:
        # Check if role is dermatologist and license is required
        if info.data.get("role") == "dermatologist" and not v:
            raise ValueError("License number is required for dermatologists")
        if v:
            v = v.strip()
            if not v:
                raise ValueError("License number cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_dermatologist_fields(self):
        """Ensure dermatologists provide license number"""
        if self.role == "dermatologist":
            if not self.license or not self.license.strip():
                raise ValueError("License number is mandatory for dermatologist registration")
        return self


class LoginRequest(BaseModel):
    """Request schema for user login"""

    emailOrUsername: str
    password: str
    role: Optional[Literal["patient", "dermatologist", "admin"]] = None


class UserResponse(BaseModel):
    """User data in responses"""

    id: str
    username: str
    email: str
    role: str
    name: Optional[str] = None
    isSuspended: Optional[bool] = False


class LoginResponse(BaseModel):
    """Response schema for successful login"""

    token: str
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""

    error: str


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password - sends OTP"""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Request schema for verifying OTP"""
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password"""
    email: EmailStr
    otp: str
    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification"""
    token: str


# User Profile Schemas
