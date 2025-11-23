from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
import warnings


# Silence TensorFlow C++ logs as early as possible
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
# Ensure Keras uses TensorFlow backend (Keras 3)
os.environ.setdefault("KERAS_BACKEND", "tensorflow")
# Optionally mute noisy deprecation warnings
warnings.filterwarnings("ignore", message=r".*sparse_softmax_cross_entropy.*")
# Further reduce TensorFlow/Keras verbosity
try:
    import tensorflow as tf  # Import early to set log levels
    tf.get_logger().setLevel("ERROR")
    try:
        from absl import logging as absl_logging
        absl_logging.set_verbosity(absl_logging.ERROR)
    except Exception:
        pass
except Exception:
    pass

from app.config import settings
from app.db.mongo import connect_to_mongo, close_mongo_connection, ensure_indexes
from app.ml.model_loader import load_model
from app.middleware.logging import RequestLoggingMiddleware
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router
from app.predictions.routes import router as predictions_router
from app.review_requests.routes import router as review_requests_router
from app.notifications.routes import router as notifications_router
from app.cloudinary_helper import cloudinary
import cloudinary.api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting FacialDerma AI Backend...")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Ensure database indexes
    await ensure_indexes()

    # Cloudinary connectivity check
    try:
        # This will fetch account info and raise if credentials are invalid
        account_info = cloudinary.api.ping()
        logger.info(f"Connected to Cloudinary: {account_info}")
    except Exception as e:
        logger.error(f"Cloudinary connection failed: {str(e)}")

    # Load ML model
    try:
        load_model()
        logger.info("ML model loaded successfully")
    except FileNotFoundError as e:
        logger.warning(f"Model file not found: {str(e)}")
        logger.warning("The /api/predictions/predict endpoint will fail until model is added")
    except Exception as e:
        msg = str(e)
        if "Full object config" in msg:
            msg = msg.split("Full object config")[0].strip()
        logger.error(f"Failed to load model: {msg}")
        logger.debug("Full model load error details", exc_info=True)
    
    logger.info(f"Application started on port {settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FacialDerma AI Backend...")
    await close_mongo_connection()
    logger.info("Application shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="FacialDerma AI Backend",
    description="Production-ready FastAPI backend for facial dermatology AI diagnosis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ORIGIN] if settings.ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(predictions_router)
app.include_router(review_requests_router)
app.include_router(notifications_router)



@app.get("/", response_class=PlainTextResponse)
async def health_check():
    """Health check endpoint"""
    return "FacialDerma AI Backend Running!"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )
