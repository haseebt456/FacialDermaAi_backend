from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from app.predictions.schemas import PredictionResponse, PredictionDocument, PredictionResult
from app.predictions.repo import create_prediction, get_user_predictions
from app.deps.auth import get_current_user
from app.ml.validators import is_image_blurry, detect_faces
from app.ml.inference import predict_image
import os
import shutil
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# Uploads directory
UPLOADS_DIR = "uploads"


def ensure_uploads_directory():
    """Ensure uploads directory exists"""
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)
        logger.info(f"Created uploads directory: {UPLOADS_DIR}")


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
    # Ensure uploads directory exists
    ensure_uploads_directory()
    
    # Save uploaded file
    file_path = os.path.join(UPLOADS_DIR, image.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        logger.info(f"Saved uploaded image to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to save image"}
        )
    
    try:
        # Validate: Check for blur (EXACT typo from spec)
        is_blurry, variance = is_image_blurry(file_path)
        if is_blurry:
            # Clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Image is blury.Please try again with a clear picture"}
            )
        
        # Validate: Check for face
        has_face, face_count = detect_faces(file_path)
        if not has_face:
            # Clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "No face detected in the image"}
            )
        
        logger.info(f"Image validation passed: variance={variance:.2f}, faces={face_count}")
        
        # Run ML inference
        prediction_result = predict_image(file_path)
        
        # Build image URL
        scheme = request.url.scheme
        host = request.headers.get("host", request.client.host)
        image_url = f"{scheme}://{host}/uploads/{image.filename}"
        
        # Save prediction to database
        user_id = str(current_user["_id"])
        await create_prediction(
            user_id=user_id,
            predicted_label=prediction_result["predicted_label"],
            confidence_score=prediction_result["confidence_score"],
            image_url=image_url
        )
        
        logger.info(f"Prediction saved: {prediction_result['predicted_label']} ({prediction_result['confidence_score']})")
        
        # Return response
        return PredictionResponse(
            predicted_label=prediction_result["predicted_label"],
            confidence_score=prediction_result["confidence_score"],
            image_url=image_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Prediction failed"}
        )
