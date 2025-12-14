from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class TreatmentSuggestionBase(BaseModel):
    name: str = Field(..., description="Name of the skin condition")
    treatments: List[str] = Field(default_factory=list, description="List of treatment recommendations")
    prevention: List[str] = Field(default_factory=list, description="List of prevention tips")
    resources: List[str] = Field(default_factory=list, description="List of helpful resources")


class TreatmentSuggestionCreate(TreatmentSuggestionBase):
    pass


class TreatmentSuggestionUpdate(BaseModel):
    name: Optional[str] = None
    treatments: Optional[List[str]] = None
    prevention: Optional[List[str]] = None
    resources: Optional[List[str]] = None


class TreatmentSuggestionInDB(TreatmentSuggestionBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }


class TreatmentSuggestionResponse(TreatmentSuggestionBase):
    id: str
    created_at: datetime
    updated_at: datetime
