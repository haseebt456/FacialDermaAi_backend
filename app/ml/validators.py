import cv2
import numpy as np
import cvlib as cv
from app.config import settings
from typing import Union, BinaryIO


def is_image_blurry(image_path: Union[str, bytes, BinaryIO], threshold: float = None) -> tuple[bool, float]:
    """
    Detect if image is blurry using Laplacian variance
    
    Returns:
        (is_blurry, variance): tuple of boolean and variance value
    """
    if threshold is None:
        threshold = settings.BLUR_THRESHOLD
    
    # Accept file-like object or bytes as well as file path
    import io
    if isinstance(image_path, (bytes, bytearray)):
        image_stream = io.BytesIO(image_path)
        image_stream.seek(0)
        file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    elif hasattr(image_path, 'read'):
        image_path.seek(0)
        file_bytes = np.asarray(bytearray(image_path.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read image")
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Calculate Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Image is blurry if variance is below threshold
    is_blurry = laplacian_var < threshold
    return is_blurry, laplacian_var


def detect_faces(image_path: Union[str, bytes, BinaryIO]) -> tuple[bool, int]:
    """
    Detect faces in image using cvlib
    
    Returns:
        (has_face, face_count): tuple of boolean and number of faces detected
    """
    # Accept file-like object or bytes as well as file path
    import io
    if isinstance(image_path, (bytes, bytearray)):
        image_stream = io.BytesIO(image_path)
        image_stream.seek(0)
        file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    elif hasattr(image_path, 'read'):
        image_path.seek(0)
        file_bytes = np.asarray(bytearray(image_path.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read image")
    # Detect faces
    faces, _ = cv.detect_face(image)
    face_count = len(faces)
    has_face = face_count > 0
    return has_face, face_count
