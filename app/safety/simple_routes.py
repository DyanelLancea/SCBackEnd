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
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None

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
                
                message = "Emergency SOS Alert."
                if sos_request.location:
                    message += f" Location: {sos_request.location}."
                if sos_request.message:
                    message += f" Message: {sos_request.message}."
                
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

@router.post("/emergency")
def trigger_emergency(sos_request: SOSRequest):
    """
    Trigger an emergency alert (alias for /sos endpoint).
    This endpoint exists for frontend compatibility.
    """
    # Simply call the SOS endpoint
    return trigger_sos(sos_request)

@router.post("/location")
async def update_location(location: LocationRequest):
    """Store user's current location in location_logs table"""
    try:
        if not location.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Build location data
        location_data = {
            "user_id": location.user_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add address if provided
        if location.address:
            location_data["address"] = location.address
        
        # Insert location into database
        try:
            response = supabase.table("location_logs").insert(location_data).execute()
        except Exception as e:
            # If address column doesn't exist, try without it
            error_str = str(e)
            if "address" in error_str.lower() or "column" in error_str.lower():
                location_data.pop("address", None)
                response = supabase.table("location_logs").insert(location_data).execute()
            else:
                raise

        return {
            "success": True,
            "location_updated": True,
            "message": "Location updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store location: {str(e)}"
        )

@router.get("/location/{user_id}")
def get_current_location(
    user_id: str,
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