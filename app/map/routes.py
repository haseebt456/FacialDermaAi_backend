# backend/map/routes.py
from fastapi import APIRouter, Query
from .service import get_nearest_dermatology
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter(
    prefix="/api/map",
    tags=["Map / Dermatology Locator"]
)

# Optional: if using this router separately, configure CORS in main.py instead
# Example: allow React frontend
# origins = ["http://localhost:3000"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@router.get("/nearest-dermatology")
def get_nearby_dermatologists(lat: float = Query(...), lng: float = Query(...), radius: int = 10000):
    """
    Returns nearest dermatology centers near given lat/lng
    """
    centers = get_nearest_dermatology(lat, lng, radius)
    return {"results": centers}
