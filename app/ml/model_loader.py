import tensorflow as tf
from tensorflow import keras
from app.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Global model instance
_model = None

# Label mapping
LABELS_MAP = {
    0: "Acne",
    1: "Melanoma",
    2: "Normal",
    3: "Perioral_Dermatitis",
    4: "Rosacea",
    5: "Warts"
}


def load_model():
    """
    Load the Keras model from disk
    Should be called once at application startup
    """
    global _model
    
    if _model is not None:
        logger.info("Model already loaded")
        return _model
    
    model_path = settings.MODEL_PATH
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}")
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    logger.info(f"Loading model from {model_path}")
    _model = keras.models.load_model(model_path)
    logger.info("Model loaded successfully")
    
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
