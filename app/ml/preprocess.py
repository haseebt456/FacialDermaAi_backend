import torch
from PIL import Image
import torchvision.transforms as transforms
from typing import Union, BinaryIO
import io


def preprocess_image(image_path: Union[str, bytes, BinaryIO], target_size: tuple = (224, 224)) -> torch.Tensor:
    """
    Preprocess image for PyTorch model prediction
    
    Steps:
    1. Load image with PIL
    2. Resize to target_size (224, 224)
    3. Convert to tensor
    4. Normalize with ImageNet mean and std
    5. Add batch dimension
    
    Returns:
        Preprocessed image tensor ready for prediction (shape: 1, 3, 224, 224)
    """
    # Define ImageNet normalization (as used in training)
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    
    # Define transformation pipeline
    transform = transforms.Compose([
        transforms.Resize(target_size),
        transforms.ToTensor(),  # Converts to [0, 1] and changes to CHW format
        normalize
    ])
    
    # Load image
    if isinstance(image_path, (bytes, bytearray)):
        image_stream = io.BytesIO(image_path)
        image_stream.seek(0)
        img = Image.open(image_stream).convert('RGB')
    elif hasattr(image_path, 'read'):
        image_path.seek(0)
        img = Image.open(image_path).convert('RGB')
    else:
        img = Image.open(image_path).convert('RGB')
    
    # Apply transformations
    img_tensor = transform(img)
    
    # Add batch dimension (1, 3, 224, 224)
    img_tensor = img_tensor.unsqueeze(0)
    
    return img_tensor
