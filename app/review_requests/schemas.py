from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class ReviewRequestCreate(BaseModel):
    """Schema for creating a review request"""
    predictionId: str = Field(..., min_length=24, max_length=24, description="MongoDB ObjectId of the prediction")
    dermatologistId: str = Field(..., min_length=24, max_length=24, description="MongoDB ObjectId of the dermatologist")
    
    @field_validator('predictionId', 'dermatologistId')
    @classmethod
    def validate_objectid(cls, v: str) -> str:
        """Validate that the ID is a valid ObjectId format"""
        if not v or len(v) != 24:
            raise ValueError("Invalid ObjectId format")
        try:
            int(v, 16)  # Verify it's hex
        except ValueError:
            raise ValueError("Invalid ObjectId format")
        return v


class ReviewAction(BaseModel):
    """Schema for submitting a review"""
    comment: str = Field(..., min_length=1, max_length=2000, description="Expert review comment")


class ReviewRequest(BaseModel):
    """Schema for review request response"""
    id: str
    predictionId: str
    patientId: str
    dermatologistId: str
    status: Literal["pending", "reviewed"]
    comment: Optional[str] = None
    createdAt: datetime
    reviewedAt: Optional[datetime] = None
    
    # Optional metadata for UI display
    patientUsername: Optional[str] = None
    dermatologistUsername: Optional[str] = None


class ReviewRequestListResponse(BaseModel):
    """Schema for paginated review request list"""
    requests: list[ReviewRequest]
    total: int
    limit: int
    offset: int
