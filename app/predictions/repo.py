from app.db.mongo import get_predictions_collection, get_counters_collection
from bson import ObjectId
from datetime import datetime
from typing import List, Dict


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


async def delete_prediction(prediction_id: str, user_id: str) -> bool:
    """
    Delete a prediction document
    
    Args:
        prediction_id: Prediction's ObjectId as string
        user_id: User's ObjectId as string (for authorization)
        
    Returns:
        True if deleted successfully, False if not found
    """
    predictions = get_predictions_collection()
    
    result = await predictions.delete_one({
        "_id": ObjectId(prediction_id),
        "userId": ObjectId(user_id)
    })
    
    return result.deleted_count > 0


async def get_next_report_id() -> str:
    """
    Generate the next unique report ID using a global counter with date prefix
    
    Format: FacialDerma-YYMMDD-XXXX
    Where YYMMDD is the current date (YY=year, MM=month, DD=day)
    and XXXX is a 4-digit zero-padded sequential number that increments continuously globally
    
    Returns:
        Unique report ID string
    """
    counters = get_counters_collection()
    
    # Get current date in YYMMDD format (UTC)
    now = datetime.utcnow()
    date_str = now.strftime("%y%m%d")
    
    # Use MongoDB's atomic findAndModify to increment global counter
    counter_doc = await counters.find_one_and_update(
        {"_id": "report_id_counter"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    
    # Get the sequence number (starts from 1)
    sequence = counter_doc["sequence"]
    
    # Format as 4-digit zero-padded number
    sequence_str = str(sequence).zfill(4)
    
    # Combine with prefix and date
    report_id = f"FacialDerma-{date_str}-{sequence_str}"
    
    return report_id


async def create_prediction(
    user_id: str,
    predicted_label: str,
    confidence_score: float,
    image_url: str,
    all_probabilities: dict = None
) -> dict:
    """
    Create a new prediction document in database with unique report ID
    
    Args:
        user_id: User's ObjectId as string
        predicted_label: Predicted condition label
        confidence_score: Confidence score (0-1)
        image_url: Full URL to uploaded image
        all_probabilities: Dictionary of all disease probabilities
        
    Returns:
        Created prediction document
    """
    predictions = get_predictions_collection()
    
    # Generate unique report ID
    report_id = await get_next_report_id()
    
    result_data = {
        "predicted_label": predicted_label,
        "confidence_score": confidence_score
    }
    
    # Add probability data if provided
    if all_probabilities:
        result_data["all_probabilities"] = all_probabilities
    
    prediction_doc = {
        "userId": ObjectId(user_id),
        "result": result_data,
        "imageUrl": image_url,
        "reportId": report_id,
        "createdAt": datetime.utcnow()
    }
    
    result = await predictions.insert_one(prediction_doc)
    prediction_doc["_id"] = result.inserted_id
    
    return prediction_doc
