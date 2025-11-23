import torch
import torch.nn.functional as F
from app.ml.pytorch_loader import get_model, get_model_device, LABELS_MAP
from app.ml.preprocess import preprocess_image
from typing import Dict, Union, BinaryIO


def predict_image(image_path: Union[str, bytes, BinaryIO]) -> Dict[str, any]:
    """
    Predict dermatological condition from image using PyTorch
    
    Args:
        image_path: Path to the image file, bytes, or file-like object
        
    Returns:
        Dictionary with:
        - predicted_label: str
        - confidence_score: float (rounded to 3 decimals)
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
    
    return {
        "predicted_label": predicted_label,
        "confidence_score": confidence_rounded
    }
