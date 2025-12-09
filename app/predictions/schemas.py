from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional


class PredictionResult(BaseModel):
    """Prediction result embedded in Prediction document"""
    predicted_label: str
    confidence_score: float
    all_probabilities: Optional[Dict[str, float]] = None


class PredictionResponse(BaseModel):
    """Response for single prediction"""
    predicted_label: str
    confidence_score: float
    image_url: str
    report_id: str
    all_probabilities: Dict[str, float]


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
