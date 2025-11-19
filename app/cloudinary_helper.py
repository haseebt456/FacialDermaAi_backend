import cloudinary
import cloudinary.uploader
from app.config import settings
import logging
from typing import Union, BinaryIO

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def upload_to_cloudinary(file_path: Union[str, bytes, BinaryIO], folder: str = "facial_derma") -> dict:
    """
    Upload an image to Cloudinary and return the public URL.
    
    Args:
        file_path: Local path to the image file
        folder: Cloudinary folder name (default: "facial_derma")
    
    Returns:
        dict: {
            "url": "https://res.cloudinary.com/...",
            "public_id": "facial_derma/xyz123"
        }
    
    Raises:
        Exception: If upload fails
    """
    try:
        # Accept file-like object or bytes as well as file path
        upload_source = file_path
        if hasattr(file_path, 'read') or isinstance(file_path, (bytes, bytearray)):
            upload_source = file_path
        # else: assume it's a file path
        result = cloudinary.uploader.upload(
            upload_source,
            folder=folder,
            resource_type="image",
            quality="auto",
            fetch_format="auto"
        )
        logger.info(f"Image uploaded to Cloudinary: {result['public_id']}")
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        raise RuntimeError(f"Failed to upload image to Cloudinary: {str(e)}")


def delete_from_cloudinary(public_id: str) -> bool:
    """
    Delete an image from Cloudinary.
    
    Args:
        public_id: Cloudinary public ID of the image
    
    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") == "ok":
            logger.info(f"Image deleted from Cloudinary: {public_id}")
            return True
        else:
            logger.warning(f"Cloudinary deletion result: {result}")
            return False
    
    except Exception as e:
        logger.error(f"Cloudinary deletion failed: {str(e)}")
        return False
