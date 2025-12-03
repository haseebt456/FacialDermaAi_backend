from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from app.predictions.schemas import PredictionResponse, PredictionDocument, PredictionResult
from app.predictions.repo import create_prediction, get_user_predictions, delete_prediction
from app.deps.auth import get_current_user
from app.ml.validators import validate_min_face_ratio
from app.ml.inference import predict_image
from app.cloudinary_helper import upload_to_cloudinary
import io
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("", response_model=List[PredictionDocument])
async def get_predictions(current_user: dict = Depends(get_current_user)):
    """
    Get all predictions for the authenticated user
    
    Returns predictions sorted by createdAt descending (newest first)
    """
    user_id = str(current_user["_id"])
    predictions = await get_user_predictions(user_id)
    
    # Convert to response format
    result = []
    for pred in predictions:
        result.append(PredictionDocument(
            id=str(pred["_id"]),
            userId=str(pred["userId"]),
            result=PredictionResult(**pred["result"]),
            imageUrl=pred["imageUrl"],
            reportId=pred.get("reportId", ""),
            createdAt=pred["createdAt"]
        ))
    
    return result


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Predict dermatological condition from uploaded image
    
    Steps:
    1. Save uploaded file
    2. Validate image (blur detection, face detection)
    3. Run ML inference
    4. Save prediction to database
    5. Return result with image URL
    
    Validations:
    - Image must not be blurry (Laplacian variance >= 100)
    - Image must contain at least one face
    """
    try:
        # Read uploaded file into BytesIO buffer for in-memory processing
        image.file.seek(0)
        image_bytes = await image.read()
        image_buffer = io.BytesIO(image_bytes)
        
        # Validate: Check for face and minimum face size ratio
        image_buffer.seek(0)
        is_valid, reason, details = validate_min_face_ratio(image_buffer)
        if not is_valid:
            logger.warning(f"Image validation failed: {reason} | Details: {details}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": reason, "validation_details": details}
            )
        logger.info(f"Image validation passed: faces={details['face_count']}, max_ratio={details['max_face_ratio']:.2%}")
        
        # Run ML inference
        image_buffer.seek(0)
        prediction_result = predict_image(image_buffer)
        
        # Upload to Cloudinary
        image_buffer.seek(0)
        try:
            cloudinary_result = upload_to_cloudinary(image_buffer, folder="facial_derma_predictions")
            image_url = cloudinary_result["url"]
            logger.info(f"Image uploaded to Cloudinary: {cloudinary_result['public_id']}")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to upload image"}
            )
        # Save prediction to database
        user_id = str(current_user["_id"])
        prediction_doc = await create_prediction(
            user_id=user_id,
            predicted_label=prediction_result["predicted_label"],
            confidence_score=prediction_result["confidence_score"],
            image_url=image_url
        )
        
        logger.info(f"Prediction saved: {prediction_result['predicted_label']} ({prediction_result['confidence_score']})")
        
        # Return response with report_id
        return PredictionResponse(
            predicted_label=prediction_result["predicted_label"],
            confidence_score=prediction_result["confidence_score"],
            image_url=image_url,
            report_id=prediction_doc["reportId"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Prediction failed"}
        )


@router.delete("/{prediction_id}", status_code=status.HTTP_200_OK)
async def delete_prediction_record(
    prediction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a prediction record
    
    Requires: User must own the prediction
    
    Returns:
        200: Prediction deleted successfully
        403: Not the owner of the prediction
        404: Prediction not found
    """
    try:
        from bson import ObjectId
        ObjectId(prediction_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid prediction ID"}
        )
    
    user_id = str(current_user["_id"])
    deleted = await delete_prediction(prediction_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Prediction not found or you don't have permission to delete it"}
        )
    
    logger.info(f"Prediction {prediction_id} deleted by user {user_id}")
    
    return {"message": "Prediction deleted successfully"}
