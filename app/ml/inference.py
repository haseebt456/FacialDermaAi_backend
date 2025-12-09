import torch
import torch.nn.functional as F
import numpy as np
from app.ml.pytorch_loader import get_model, get_model_device, LABELS_MAP
from app.ml.preprocess import preprocess_image
from typing import Dict, Union, BinaryIO, Any


def predict_image(image_path: Union[str, bytes, BinaryIO]) -> Dict[str, Any]:
    """
    Predict dermatological condition from image using PyTorch
    
    Args:
        image_path: Path to the image file, bytes, or file-like object
        
    Returns:
        Dictionary with:
        - predicted_label: str
        - confidence_score: float (rounded to 3 decimals)
        - all_probabilities: dict with disease name as key and probability as value
        - top_3_predictions: list of dicts with label and probability for top 3
    """
    # Get model and device
    model = get_model()
    device = get_model_device()
    
    # Preprocess image
    img_tensor = preprocess_image(image_path)
    
    # Move tensor to model's device
    img_tensor = img_tensor.to(device)
    
    # Make prediction (no gradient computation needed)
    with torch.no_grad():
        outputs = model(img_tensor)
        # Apply softmax to get probabilities
        probabilities = F.softmax(outputs, dim=1)
    
    # Get predicted class and confidence
    confidence, predicted_class = torch.max(probabilities, dim=1)
    
    # Convert to Python types
    predicted_class = int(predicted_class.item())
    confidence = float(confidence.item())
    
    # Round confidence to 3 decimals
    confidence_rounded = round(confidence, 3)
    
    # Get label
    predicted_label = LABELS_MAP[predicted_class]
    
    # Get all probabilities for each disease (for graphical representation)
    # Exclude "normal" from the response
    all_probs = probabilities[0].cpu().numpy()
    all_probabilities = {}
    for class_idx, prob in enumerate(all_probs):
        disease_name = LABELS_MAP[class_idx]
        if disease_name != "normal":  # Skip "normal" disease
            all_probabilities[disease_name] = round(float(prob), 4)
    
    return {
        "predicted_label": predicted_label,
        "confidence_score": confidence_rounded,
        "all_probabilities": all_probabilities
    }
