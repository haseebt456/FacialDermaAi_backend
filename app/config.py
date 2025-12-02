from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    PORT: int = 5000
    MONGO_URI: str
    DB_NAME: str = "facialderma_db"
    JWT_SECRET: str
    EMAIL_USER: str
    EMAIL_PASS: str
    ORIGIN: str = "0.0.0.0"
    
    # Email SMTP configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SKIP_EMAIL: bool = False  # Set to True to skip email and log OTP to console
    
    # Email verification
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for verification links
    VERIFICATION_TOKEN_EXPIRY_MINUTES: int = 15  # Token expiry time in minutes
    
    # Cloudinary configuration
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # JWT configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7  # Extended to 7 days for better UX
    
    # ML Model (PyTorch)
    PYTORCH_MODEL_PATH: str = "best_model.pth"
    
    # Image validation thresholds
    BLUR_THRESHOLD: float = 50.0
    MIN_FACE_AREA_RATIO: float = 0.25  # Minimum face area as fraction of image (5%)
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
