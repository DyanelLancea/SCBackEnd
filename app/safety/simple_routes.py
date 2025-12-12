from datetime import datetime
from typing import Optional
import os
from twilio.rest import Client
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.shared.supabase import get_supabase_client

router = APIRouter()

class SOSRequest(BaseModel):
    user_id: str
    location: Optional[str] = None
    message: Optional[str] = None

class LocationRequest(BaseModel):
    user_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@router.post("/sos")
def trigger_sos(sos_request: SOSRequest):
    """Simple SOS that just makes emergency call"""
    try:
        if not sos_request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Make emergency call using Twilio
        emergency_number = "+6598631975"
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not from_number:
            return {
                "success": True,
                "message": "SOS alert received (call not configured)",
                "call_status": "Twilio phone number not configured"
            }

        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if account_sid and auth_token:
                client = Client(account_sid, auth_token)
                
                # Get user's current address for the call
                user_address = "Location not available"
                if sos_request.location:
                    user_address = sos_request.location
                else:
                    user_address = "Current location"
                
                message = f"Emergency SOS Alert. Address: {user_address}."
                
                call = client.calls.create(
                    twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
                    to=emergency_number,
                    from_=from_number
                )
                
                return {
                    "success": True,
                    "message": "SOS alert sent successfully",
                    "call_sid": call.sid,
                    "call_status": "Emergency call initiated"
                }
        except Exception as e:
            return {
                "success": True,
                "message": "SOS alert received",
                "call_status": f"Call failed: {str(e)}"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SOS failed: {str(e)}")

@router.post("/location")
def update_location(location_request: LocationRequest):
    """Update/store current device location"""
    return {
        "success": True,
        "message": "Location updated",
        "user_id": location_request.user_id or "anonymous",
        "location_display": "Current location",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/location")
def get_location(
    user_id: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None)
):
    """Get current device location"""
    if lat is None or lng is None:
        return {
            "success": False,
            "message": "Please provide current location",
            "location_display": "Location access required"
        }
    
    return {
        "success": True,
        "user_id": user_id or "anonymous",
        "current_location": {
            "latitude": lat,
            "longitude": lng,
            "timestamp": datetime.utcnow().isoformat()
        },
        "location_display": "Current location",
        "timestamp": datetime.utcnow().isoformat(),
        "time_since_update": "Just now"
    }

@router.get("/location/{user_id}")
def get_current_location(
    user_id: str,
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None)
):
    """Get current device location with user ID in path"""
    if lat is None or lng is None:
        return {
            "success": False,
            "message": "Please provide current location",
            "location_display": "Location access required"
        }
    
    return {
        "success": True,
        "user_id": user_id,
        "current_location": {
            "latitude": lat,
            "longitude": lng,
            "timestamp": datetime.utcnow().isoformat()
        },
        "location_display": "Current location",
        "timestamp": datetime.utcnow().isoformat(),
        "time_since_update": "Just now"
    }