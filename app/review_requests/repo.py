from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.db.mongo import get_review_requests_collection, get_predictions_collection, get_users_collection
import logging

logger = logging.getLogger(__name__)


async def create_review_request(
    prediction_id: ObjectId,
    patient_id: ObjectId,
    dermatologist_id: ObjectId
) -> dict:
    """
    Create a new review request.
    
    Raises:
        ValueError: If duplicate request exists
    """
    collection = get_review_requests_collection()
    
    # Check for duplicate
    existing = await collection.find_one({
        "predictionId": prediction_id,
        "dermatologistId": dermatologist_id
    })
    
    if existing:
        raise ValueError("A review request to this dermatologist already exists for this prediction")
    
    doc = {
        "predictionId": prediction_id,
        "patientId": patient_id,
        "dermatologistId": dermatologist_id,
        "status": "pending",
        "comment": None,
        "createdAt": datetime.utcnow(),
        "reviewedAt": None
    }
    
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    
    logger.info(f"Created review request {result.inserted_id} for prediction {prediction_id}")
    
    return doc


async def get_review_request_by_id(request_id: ObjectId) -> Optional[dict]:
    """Get a review request by ID with user metadata"""
    collection = get_review_requests_collection()
    users_collection = get_users_collection()
    
    # Fetch the review request
    request = await collection.find_one({"_id": request_id})
    if not request:
        return None
    
    # Optionally enrich with usernames
    patient = await users_collection.find_one({"_id": request["patientId"]}, {"username": 1})
    dermatologist = await users_collection.find_one({"_id": request["dermatologistId"]}, {"username": 1})
    
    if patient:
        request["patientUsername"] = patient.get("username")
    if dermatologist:
        request["dermatologistUsername"] = dermatologist.get("username")
    
    return request


async def get_review_requests_for_user(
    user_id: ObjectId,
    role: str,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[dict], int]:
    """
    Get review requests for a user based on their role.
    
    Args:
        user_id: Current user's ObjectId
        role: "patient" or "dermatologist"
        status_filter: Optional "pending" or "reviewed"
        limit: Max results per page
        offset: Skip count for pagination
    
    Returns:
        (list of requests, total count)
    """
    collection = get_review_requests_collection()
    users_collection = get_users_collection()
    
    # Build query based on role
    if role == "dermatologist":
        query = {"dermatologistId": user_id}
    elif role == "patient":
        query = {"patientId": user_id}
    else:
        return [], 0
    
    if status_filter:
        query["status"] = status_filter
    
    # Count total
    total = await collection.count_documents(query)
    
    # Fetch paginated results
    cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
    requests = await cursor.to_list(length=limit)
    
    # Enrich with usernames
    for req in requests:
        patient = await users_collection.find_one({"_id": req["patientId"]}, {"username": 1})
        dermatologist = await users_collection.find_one({"_id": req["dermatologistId"]}, {"username": 1})
        if patient:
            req["patientUsername"] = patient.get("username")
        if dermatologist:
            req["dermatologistUsername"] = dermatologist.get("username")
    
    return requests, total


async def submit_review(
    request_id: ObjectId,
    dermatologist_id: ObjectId,
    comment: str
) -> Optional[dict]:
    """
    Submit a review for a request.
    
    Returns:
        Updated request document or None if not found/not authorized
    
    Raises:
        ValueError: If request is not pending or dermatologist is not assigned
    """
    collection = get_review_requests_collection()
    
    request = await collection.find_one({"_id": request_id})
    if not request:
        return None
    
    # Verify dermatologist is assigned
    if request["dermatologistId"] != dermatologist_id:
        raise ValueError("You are not assigned to this request")
    
    # Verify status is pending
    if request["status"] != "pending":
        raise ValueError("This request has already been reviewed")
    
    # Update with review
    update_result = await collection.find_one_and_update(
        {"_id": request_id},
        {
            "$set": {
                "comment": comment,
                "status": "reviewed",
                "reviewedAt": datetime.utcnow()
            }
        },
        return_document=True
    )
    
    logger.info(f"Review submitted for request {request_id} by dermatologist {dermatologist_id}")
    
    return update_result


async def get_prediction_by_id(prediction_id: ObjectId) -> Optional[dict]:
    """Get a prediction document by ID"""
    collection = get_predictions_collection()
    return await collection.find_one({"_id": prediction_id})
