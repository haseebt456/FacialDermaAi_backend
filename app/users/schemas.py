from pydantic import BaseModel


class UserMeResponse(BaseModel):
    """Response for GET /api/users/me"""
    id: str
    username: str
    email: str
    role: str
