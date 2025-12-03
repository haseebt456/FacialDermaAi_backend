# backend/map/service.py
import requests
import os
from typing import List, Dict
from app.config import settings

GOOGLE_API_KEY = settings.GOOGLE_MAPS_API_KEY

def get_nearest_dermatology(lat: float, lng: float, radius: int = 10000) -> List[Dict]:
    """
    Fetches nearest dermatology centers from Google Places API.
    Returns a list of dicts: name, lat, lng, address
    """
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": "dermatologist skin clinic",
        "type": "doctor",
        "key": GOOGLE_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    # Check for API errors
    if data.get("status") != "OK":
        print(f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
        return []

    results = []
    for place in data.get("results", []):
        results.append({
            "name": place.get("name"),
            "lat": place["geometry"]["location"]["lat"],
            "lng": place["geometry"]["location"]["lng"],
            "address": place.get("vicinity"),
            "rating": place.get("rating")
        })

    return results
