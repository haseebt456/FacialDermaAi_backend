import numpy as np
from app.ml.model_loader import get_model, LABELS_MAP
from app.ml.preprocess import preprocess_image
from typing import Dict


def predict_image(image_path: str) -> Dict[str, any]:
    """
    Predict dermatological condition from image
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with:
        - predicted_label: str
        - confidence_score: float (rounded to 3 decimals)
    """
    # Get model
    model = get_model()
    
    # Preprocess image
    img_array = preprocess_image(image_path)
    
    # Make prediction
    predictions = model.predict(img_array, verbose=0)
    
    # Get predicted class and confidence
    predicted_class = int(np.argmax(predictions[0]))
    confidence = float(np.max(predictions[0]))
    
    # Round confidence to 3 decimals
    confidence_rounded = round(confidence, 3)
    
    # Get label
    predicted_label = LABELS_MAP[predicted_class]
    
    return {
        "predicted_label": predicted_label,
        "confidence_score": confidence_rounded
    }
