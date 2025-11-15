import cv2
import numpy as np
import cvlib as cv
from app.config import settings


def is_image_blurry(image_path: str, threshold: float = None) -> tuple[bool, float]:
    """
    Detect if image is blurry using Laplacian variance
    
    Returns:
        (is_blurry, variance): tuple of boolean and variance value
    """
    if threshold is None:
        threshold = settings.BLUR_THRESHOLD
    
    # Read image
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


def detect_faces(image_path: str) -> tuple[bool, int]:
    """
    Detect faces in image using cvlib
    
    Returns:
        (has_face, face_count): tuple of boolean and number of faces detected
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read image")
    
    # Detect faces
    faces, confidences = cv.detect_face(image)
    
    face_count = len(faces)
    has_face = face_count > 0
    
    return has_face, face_count
