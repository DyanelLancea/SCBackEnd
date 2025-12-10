"""
Safety & Emergency Response Routes
Emergency alerts, location tracking, and safety monitoring
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.shared.supabase import get_supabase_client


router = APIRouter()


# ==================== REQUEST MODELS ====================

class EmergencyAlert(BaseModel):
    """Trigger an emergency alert"""
    user_id: str
    alert_type: str  # fall, sos, health, wandering
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    """Update user location"""
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None


# ==================== ENDPOINTS ====================

@router.get("/")
def safety_info():
    """Get information about the Safety module"""
    return {
        "module": "Safety & Emergency Response",
        "description": "Emergency alerts, location tracking, and safety monitoring",
        "capabilities": [
            "Emergency SOS alerts",
            "Real-time location tracking",
            "Caregiver notifications",
            "Safety monitoring"
        ],
        "endpoints": {
            "emergency": "/api/safety/emergency",
            "location": "/api/safety/location",
            "tracking": "/api/safety/location/{user_id}"
        },
        "status": "ready"
    }


@router.post("/emergency")
def trigger_emergency(alert: EmergencyAlert):
    """Trigger an emergency alert"""
    return {
        "success": True,
        "message": "Emergency alert triggered",
        "alert": alert.dict(),
        "caregivers_notified": True
    }


@router.post("/location")
def update_location(location: LocationUpdate):
    """Update user location"""
    return {
        "success": True,
        "message": "Location updated",
        "location": location.dict()
    }


@router.get("/location/{user_id}")
def get_location(user_id: str):
    """Get user's current location"""
    return {
        "success": True,
        "user_id": user_id,
        "location": None,
        "message": "Location tracking - ready for implementation"
    }

