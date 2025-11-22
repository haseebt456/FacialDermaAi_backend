from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from typing import Optional
import logging

from app.review_requests.schemas import (
    ReviewRequestCreate,
    ReviewRequest,
    ReviewAction,
    ReviewRequestListResponse
)
from app.review_requests.repo import (
    create_review_request,
    get_review_request_by_id,
    get_review_requests_for_user,
    submit_review,
    reject_review_request,
    get_prediction_by_id
)
from app.deps.auth import get_current_user, require_role
from app.predictions.schemas import PredictionDocument, PredictionResult
from app.auth.service import get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/review-requests", tags=["review-requests"])


def format_review_request(doc: dict) -> ReviewRequest:
    """Convert MongoDB document to ReviewRequest schema"""
    return ReviewRequest(
        id=str(doc["_id"]),
        predictionId=str(doc["predictionId"]),
        patientId=str(doc["patientId"]),
        dermatologistId=str(doc["dermatologistId"]),
        status=doc["status"],
        comment=doc.get("comment"),
        createdAt=doc["createdAt"],
        reviewedAt=doc.get("reviewedAt"),
        patientUsername=doc.get("patientUsername"),
        dermatologistUsername=doc.get("dermatologistUsername")
    )


@router.post("", response_model=ReviewRequest, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: ReviewRequestCreate,
    current_user: dict = Depends(require_role("patient"))
):
    """
    Create a review request for a prediction.
    
    Requires: Patient role and prediction ownership
    
    Returns:
        201: Created review request
        400: Invalid input or duplicate request
        403: Not a patient or not prediction owner
        404: Prediction or dermatologist not found
    """
    try:
        prediction_id = ObjectId(payload.predictionId)
        dermatologist_id = ObjectId(payload.dermatologistId)
        patient_id = ObjectId(str(current_user["_id"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid ObjectId format"}
        )
    
    # Verify prediction exists and belongs to patient
    prediction = await get_prediction_by_id(prediction_id)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Prediction not found"}
        )
    
    if prediction["userId"] != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "You can only request reviews for your own predictions"}
        )
    
    # Verify dermatologist exists and has correct role
    dermatologist = await get_user_by_id(str(dermatologist_id))
    if not dermatologist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Dermatologist not found"}
        )
    
    if dermatologist.get("role") != "dermatologist":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Selected user is not a dermatologist"}
        )
    
    # Create review request
    try:
        doc = await create_review_request(prediction_id, patient_id, dermatologist_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": str(e)}
        )
    
    # Send notifications (import here to avoid circular dependency)
    from app.notifications.repo import create_notification
    from app.email.mailer import send_review_request_email
    import asyncio
    
    # Create in-app notification for dermatologist
    await create_notification(
        user_id=dermatologist_id,
        notification_type="review_requested",
        message=f"New review request from {current_user['username']}",
        ref_data={
            "requestId": str(doc["_id"]),
            "predictionId": str(prediction_id)
        }
    )
    
    # Send email notification (non-blocking)
    asyncio.create_task(
        send_review_request_email(
            dermatologist["email"],
            dermatologist["username"],
            current_user["username"],
            str(prediction_id)
        )
    )
    
    logger.info(f"Review request created: {doc['_id']}")
    
    return format_review_request(doc)


@router.get("", response_model=ReviewRequestListResponse)
async def list_requests(
    status_filter: Optional[str] = Query(None, regex="^(pending|reviewed|rejected)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    List review requests for the current user.
    
    - Patients see requests they created
    - Dermatologists see requests assigned to them
    
    Query params:
        status: Filter by "pending" or "reviewed"
        limit: Max results (1-100, default 50)
        offset: Skip count for pagination
    """
    user_id = ObjectId(str(current_user["_id"]))
    role = current_user.get("role")
    
    requests, total = await get_review_requests_for_user(
        user_id, role, status_filter, limit, offset
    )
    
    return ReviewRequestListResponse(
        requests=[format_review_request(r) for r in requests],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{id}")
async def get_request(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific review request with prediction details.
    
    Requires: Must be the assigned dermatologist or the patient who created it
    
    Returns:
        200: Review request details with prediction (image, result, patient info)
        403: Not authorized to view this request
        404: Request not found
    """
    try:
        request_id = ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid request ID"}
        )
    
    doc = await get_review_request_by_id(request_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review request not found"}
        )
    
    # Check authorization
    current_user_id = ObjectId(str(current_user["_id"]))
    if doc["patientId"] != current_user_id and doc["dermatologistId"] != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "You are not authorized to view this request"}
        )
    
    # Load prediction details
    prediction = await get_prediction_by_id(doc["predictionId"])
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Prediction not found"}
        )
    
    # Load patient info
    patient = await get_user_by_id(str(doc["patientId"]))
    patient_info = None
    if patient:
        patient_info = {
            "name": patient.get("name"),
            "username": patient.get("username"),
            "email": patient.get("email"),
            "age": patient.get("age"),
            "gender": patient.get("gender"),
            "phone": patient.get("phone"),
            "bloodGroup": patient.get("bloodGroup"),
            "allergies": patient.get("allergies")
        }
    patient_name = patient.get("name") or patient.get("username") if patient else "Unknown"
    
    # Load dermatologist info
    dermatologist = await get_user_by_id(str(doc["dermatologistId"]))
    dermatologist_info = None
    if dermatologist:
        dermatologist_info = {
            "name": dermatologist.get("name"),
            "username": dermatologist.get("username"),
            "email": dermatologist.get("email")
        }
    
    # Return enriched response with prediction details
    return {
        "id": str(doc["_id"]),
        "predictionId": str(doc["predictionId"]),
        "patientId": str(doc["patientId"]),
        "dermatologistId": str(doc["dermatologistId"]),
        "status": doc["status"],
        "comment": doc.get("comment"),
        "createdAt": doc["createdAt"],
        "reviewedAt": doc.get("reviewedAt"),
        "patientUsername": doc.get("patientUsername"),
        "dermatologistUsername": doc.get("dermatologistUsername"),
        # Prediction details
        "prediction": {
            "id": str(prediction["_id"]),
            "userId": str(prediction["userId"]),
            "result": {
                "predicted_label": prediction["result"]["predicted_label"],
                "confidence_score": prediction["result"]["confidence_score"],
            },
            "imageUrl": prediction["imageUrl"],
            "createdAt": prediction["createdAt"],
        },
        "patientName": patient_name,
        "patientInfo": patient_info,
        "dermatologistInfo": dermatologist_info
    }


@router.post("/{id}/review", response_model=ReviewRequest)
async def add_review(
    id: str,
    payload: ReviewAction,
    current_user: dict = Depends(require_role("dermatologist"))
):
    """
    Submit a review for a request.
    
    Requires: Dermatologist role and must be assigned to this request
    
    Returns:
        200: Review submitted successfully
        400: Request already reviewed or validation error
        403: Not the assigned dermatologist
        404: Request not found
    """
    try:
        request_id = ObjectId(id)
        dermatologist_id = ObjectId(str(current_user["_id"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid request ID"}
        )
    
    try:
        updated_doc = await submit_review(request_id, dermatologist_id, payload.comment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)}
        )
    
    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review request not found"}
        )
    
    # Send notifications to patient
    from app.notifications.repo import create_notification
    from app.email.mailer import send_review_submitted_email
    import asyncio
    
    patient_id = updated_doc["patientId"]
    patient = await get_user_by_id(str(patient_id))
    
    if patient:
        # Create in-app notification
        await create_notification(
            user_id=patient_id,
            notification_type="review_submitted",
            message=f"Dr. {current_user['username']} added a review to your prediction",
            ref_data={
                "requestId": str(request_id),
                "predictionId": str(updated_doc["predictionId"])
            }
        )
        
        # Send email (non-blocking)
        asyncio.create_task(
            send_review_submitted_email(
                patient["email"],
                patient["username"],
                current_user["username"],
                str(updated_doc["predictionId"])
            )
        )
    
    logger.info(f"Review added to request {request_id} by {current_user['username']}")
    
    return format_review_request(updated_doc)


@router.post("/{id}/reject", response_model=ReviewRequest)
async def reject_request(
    id: str,
    payload: ReviewAction,
    current_user: dict = Depends(require_role("dermatologist"))
):
    """
    Reject/deny a pending review request.

    Requires: Dermatologist role and must be assigned to this request

    Returns:
        200: Request rejected successfully
        400: Request already reviewed/rejected or validation error
        403: Not the assigned dermatologist
        404: Request not found
    """
    try:
        request_id = ObjectId(id)
        dermatologist_id = ObjectId(str(current_user["_id"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid request ID"}
        )

    try:
        updated_doc = await reject_review_request(request_id, dermatologist_id, payload.comment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)}
        )

    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review request not found"}
        )

    # Notify patient of rejection
    from app.notifications.repo import create_notification
    from app.email.mailer import send_review_rejected_email
    import asyncio

    patient_id = updated_doc["patientId"]
    patient = await get_user_by_id(str(patient_id))

    if patient:
        await create_notification(
            user_id=patient_id,
            notification_type="review_rejected",
            message=f"Dr. {current_user['username']} rejected your review request",
            ref_data={
                "requestId": str(request_id),
                "predictionId": str(updated_doc["predictionId"])
            }
        )

        asyncio.create_task(
            send_review_rejected_email(
                patient["email"],
                patient["username"],
                current_user["username"],
                str(updated_doc["predictionId"]),
                payload.comment
            )
        )

    logger.info(f"Review request {request_id} rejected by {current_user['username']}")

    return format_review_request(updated_doc)


@router.delete("/{id}")
async def delete_review_request(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a review request.
    
    Requires: Must be the assigned dermatologist or the patient who created it
    
    Returns:
        200: Review request deleted successfully
        403: Not authorized to delete this request
        404: Request not found
    """
    try:
        request_id = ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid request ID"}
        )
    
    doc = await get_review_request_by_id(request_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review request not found"}
        )
    
    # Check authorization - only dermatologist or patient can delete
    current_user_id = ObjectId(str(current_user["_id"]))
    if doc["patientId"] != current_user_id and doc["dermatologistId"] != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "You are not authorized to delete this request"}
        )
    
    # Delete the review request from database
    from app.db.mongo import get_review_requests_collection
    review_requests = get_review_requests_collection()
    result = await review_requests.delete_one({"_id": request_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Review request not found"}
        )
    
    logger.info(f"Review request {request_id} deleted by {current_user['username']}")
    
    return {"message": "Review request deleted successfully", "id": str(request_id)}
