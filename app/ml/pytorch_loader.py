import torch
import torch.nn as nn
from torchvision import models
from app.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Global model instance
_model = None
_device = None

# Label mapping (same as before for consistency)
LABELS_MAP = {
    0: "Eczema",
    1: "Acne",
    2: "melasma",
    3: "normal",
    4: "Rosacea",
    5: "Seborrheic Dermatitis"
}


def get_device():
    """
    Determine the best available device (CUDA, MPS, or CPU)
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


def create_efficientnet_model(num_classes=6):
    """
    Create EfficientNet-B0 model architecture matching the training configuration
    """
    # Load pretrained EfficientNet-B0
    model = models.efficientnet_b0(weights=None)
    
    # Replace the classifier head to match the training setup
    # Original classifier: model.classifier[1] is Linear(in_features=1280, out_features=1000)
    # We replace it with: Linear(1280, num_classes)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, num_classes)
    
    return model


def load_model():
    """
    Load the PyTorch model from disk
    Should be called once at application startup
    """
    global _model, _device
    
    if _model is not None:
        logger.info("Model already loaded")
        return _model
    
    model_path = settings.PYTORCH_MODEL_PATH
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}")
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    logger.info(f"Loading PyTorch model from {model_path}")
    
    # Determine device
    _device = get_device()
    logger.info(f"Using device: {_device}")
    
    # Create model architecture
    _model = create_efficientnet_model(num_classes=6)
    
    # Load state dict
    try:
        state_dict = torch.load(model_path, map_location=_device)
        _model.load_state_dict(state_dict)
        logger.info("Model state_dict loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model state_dict: {str(e)}")
        raise
    
    # Set to evaluation mode
    _model.eval()
    _model.to(_device)
    
    logger.info("PyTorch model loaded and ready for inference")
    
    return _model


def get_model():
    """
    Get the loaded model instance
    Raises exception if model is not loaded
    """
    global _model
    
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    
    return _model


def get_model_device():
    """
    Get the device the model is running on
    """
    global _device
    
    if _device is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")
    
    return _device
