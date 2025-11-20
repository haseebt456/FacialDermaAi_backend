from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    PORT: int = 5000
    MONGO_URI: str
    DB_NAME: str = "facialderma_db"
    JWT_SECRET: str
    EMAIL_USER: str
    EMAIL_PASS: str
    ORIGIN: str = "http://localhost:3000"
    
    # Cloudinary configuration
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # JWT configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7  # Extended to 7 days for better UX
    
    # ML Model
    MODEL_PATH: str = "ResNet_Model.keras"
    
    # Image validation thresholds
    BLUR_THRESHOLD: float = 100.0
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
