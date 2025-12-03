from pydantic import BaseModel
from datetime import datetime
from typing import Dict


class PredictionResult(BaseModel):
    """Prediction result embedded in Prediction document"""
    predicted_label: str
    confidence_score: float


class PredictionResponse(BaseModel):
    """Response for single prediction"""
    predicted_label: str
    confidence_score: float
    image_url: str
    report_id: str


class PredictionDocument(BaseModel):
    """Full prediction document from database"""
    id: str
    userId: str
    result: PredictionResult
    imageUrl: str
    reportId: str
    createdAt: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
