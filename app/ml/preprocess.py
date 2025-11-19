import cv2
import numpy as np
from tensorflow.keras.preprocessing import image as keras_image
from typing import Union, BinaryIO


def preprocess_image(image_path: Union[str, bytes, BinaryIO], target_size: tuple = (224, 224)) -> np.ndarray:
    """
    Preprocess image for model prediction
    
    Steps:
    1. Load image
    2. Resize to target_size (224, 224)
    3. Normalize pixel values to [0, 1]
    4. Expand dimensions for batch
    
    Returns:
        Preprocessed image array ready for prediction
    """
    # Accept file-like object or bytes as well as file path
    import io
    if isinstance(image_path, (bytes, bytearray)):
        image_stream = io.BytesIO(image_path)
        image_stream.seek(0)
        img = keras_image.load_img(image_stream, target_size=target_size)
    elif hasattr(image_path, 'read'):
        image_path.seek(0)
        img = keras_image.load_img(image_path, target_size=target_size)
    else:
        img = keras_image.load_img(image_path, target_size=target_size)
    # Convert to array
    img_array = keras_image.img_to_array(img)
    # Normalize to [0, 1]
    img_array = img_array / 255.0
    # Expand dimensions to create batch of 1
    img_array = np.expand_dims(img_array, axis=0)
    return img_array
