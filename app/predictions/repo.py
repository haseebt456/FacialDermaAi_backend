from app.db.mongo import get_predictions_collection
from bson import ObjectId
from datetime import datetime
from typing import List, Dict


async def create_prediction(
    user_id: str,
    predicted_label: str,
    confidence_score: float,
    image_url: str
) -> dict:
    """
    Create a new prediction document in database
    
    Args:
        user_id: User's ObjectId as string
        predicted_label: Predicted condition label
        confidence_score: Confidence score (0-1)
        image_url: Full URL to uploaded image
        
    Returns:
        Created prediction document
    """
    predictions = get_predictions_collection()
    
    prediction_doc = {
        "userId": ObjectId(user_id),
        "result": {
            "predicted_label": predicted_label,
            "confidence_score": confidence_score
        },
        "imageUrl": image_url,
        "createdAt": datetime.utcnow()
    }
    
    result = await predictions.insert_one(prediction_doc)
    prediction_doc["_id"] = result.inserted_id
    
    return prediction_doc


async def get_user_predictions(user_id: str) -> List[dict]:
    """
    Get all predictions for a user, sorted by createdAt descending
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        List of prediction documents
    """
    predictions = get_predictions_collection()
    
    cursor = predictions.find({"userId": ObjectId(user_id)}).sort("createdAt", -1)
    predictions_list = await cursor.to_list(length=None)
    
    return predictions_list
