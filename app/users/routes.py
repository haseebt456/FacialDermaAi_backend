from fastapi import APIRouter, Depends, HTTPException, status
from app.users.schemas import UserMeResponse
from app.deps.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires: Bearer token in Authorization header
    Returns: User data excluding password
    """
    return UserMeResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"]
    )
