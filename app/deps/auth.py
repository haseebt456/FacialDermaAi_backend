from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.service import decode_token, get_user_by_id
from typing import Optional, Callable

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current authenticated user from JWT token
    
    Raises:
    - 401 if no token provided
    - 401 if token is invalid
    - 404 if user not found
    """
    token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "No token, authorization denied"}
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token is not valid"}
        )
    
    # Get user
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token is not valid"}
        )
    
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found"}
        )
    
    return user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory to enforce role-based access control.
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_role("dermatologist"))])
        async def endpoint(current_user: dict = Depends(get_current_user)):
            ...
    
    Args:
        *allowed_roles: One or more role strings (e.g., "patient", "dermatologist")
    
    Returns:
        A dependency function that raises 403 if user role not in allowed_roles
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": f"Access denied. Required role: {', '.join(allowed_roles)}"}
            )
        return current_user
    
    return role_checker
