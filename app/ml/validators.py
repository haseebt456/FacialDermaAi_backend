import cv2
import numpy as np
import cvlib as cv
from app.config import settings
from typing import Union, BinaryIO


def _decode_image(image_input: Union[str, bytes, BinaryIO]) -> np.ndarray:
    """
    Helper to decode image from various input types
    
    Returns:
        numpy array of the decoded image
    """
    import io
    if isinstance(image_input, (bytes, bytearray)):
        image_stream = io.BytesIO(image_input)
        image_stream.seek(0)
        file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    elif hasattr(image_input, 'read'):
        image_input.seek(0)
        file_bytes = np.asarray(bytearray(image_input.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(image_input)
    
    if image is None:
        raise ValueError("Could not read image")
    return image


def detect_faces(image_path: Union[str, bytes, BinaryIO]) -> tuple[bool, int]:
    """
    Detect faces in image using cvlib
    
    Returns:
        (has_face, face_count): tuple of boolean and number of faces detected
    """
    image = _decode_image(image_path)
    faces, _ = cv.detect_face(image)
    face_count = len(faces)
    has_face = face_count > 0
    return has_face, face_count


def detect_faces_with_ratio(image_input: Union[str, bytes, BinaryIO]) -> tuple[bool, int, list, tuple[int, int], float]:
    """
    Detect faces and calculate the largest face area ratio
    
    Returns:
        (has_face, face_count, boxes, image_size, max_face_area_ratio):
            - has_face: whether at least one face was detected
            - face_count: number of faces detected
            - boxes: list of bounding boxes [(x1, y1, x2, y2), ...]
            - image_size: (height, width) of the image
            - max_face_area_ratio: ratio of largest face area to total image area
    """
    image = _decode_image(image_input)
    height, width = image.shape[:2]
    image_area = height * width
    
    # Detect faces
    faces, _ = cv.detect_face(image)
    face_count = len(faces)
    has_face = face_count > 0
    
    # Convert faces to list of tuples and calculate max ratio
    boxes = [tuple(box) for box in faces] if face_count > 0 else []
    max_face_area_ratio = 0.0
    
    if face_count > 0:
        face_areas = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in boxes]
        max_face_area = max(face_areas)
        max_face_area_ratio = max_face_area / image_area
    
    return has_face, face_count, boxes, (height, width), max_face_area_ratio


def validate_min_face_ratio(image_input: Union[str, bytes, BinaryIO], min_ratio: float = None) -> tuple[bool, str, dict]:
    """
    Validate that the largest detected face meets minimum size ratio requirement
    
    Args:
        image_input: image as path, bytes, or file-like object
        min_ratio: minimum face area ratio (defaults to settings.MIN_FACE_AREA_RATIO)
    
    Returns:
        (is_valid, reason, details):
            - is_valid: True if validation passes
            - reason: error message if validation fails, empty string otherwise
            - details: dict with face_count, max_face_ratio, image_size
    """
    if min_ratio is None:
        min_ratio = settings.MIN_FACE_AREA_RATIO
    
    has_face, face_count, boxes, image_size, max_face_area_ratio = detect_faces_with_ratio(image_input)
    
    details = {
        "face_count": face_count,
        "max_face_ratio": round(max_face_area_ratio, 4),
        "image_size": image_size,
        "min_required_ratio": min_ratio
    }
    
    if not has_face:
        return False, "We couldn't detect a face in your photo. For best results, make sure your face is clearly visible, well-lit, and looking towards the camera.", details
    
    if max_face_area_ratio < min_ratio:
        return False, "Your face needs to be closer to the camera. Please retake the photo with your face filling more of the frame for accurate analysis.", details
    
    return True, "", details
