from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Literal
import re


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    role: Literal["patient", "dermatologist"]
    username: str
    email: EmailStr
    password: str
    
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


class LoginRequest(BaseModel):
    """Request schema for user login"""
    emailOrUsername: str
    password: str
    role: Literal["patient", "dermatologist"]


class UserResponse(BaseModel):
    """User data in responses"""
    id: str
    username: str
    email: str
    role: str


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
