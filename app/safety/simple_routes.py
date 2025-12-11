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
async def get_current_location(user_id: str):
    """Get the most recent location for a user from location_logs table"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Get most recent location from database
        location_response = (
            supabase.table("location_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)  # Get most recent first
            .limit(1)  # Only get the latest location entry
            .execute()
        )
        
        current_location = location_response.data[0] if location_response.data else None

        if not current_location:
            # Return error response when no location found
            raise HTTPException(
                status_code=404,
                detail="No location data found for this user"
            )

        # Get timestamp and format it properly
        timestamp = current_location.get("timestamp")
        if timestamp:
            # Convert to string if needed
            if not isinstance(timestamp, str):
                if hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                else:
                    timestamp = str(timestamp)
            
            # Ensure timestamp ends with Z (UTC indicator) if it doesn't already
            if not timestamp.endswith('Z') and '+' not in timestamp:
                if timestamp.count('-') > 2:
                    # Has timezone offset like 2025-12-12T10:30:00-05:00
                    parts = timestamp.rsplit('-', 2)
                    if len(parts) == 3:
                        timestamp = parts[0] + '-' + parts[1] + 'Z'
                    else:
                        timestamp = timestamp + 'Z'
                else:
                    timestamp = timestamp + 'Z'

        # Return location in the expected format
        return {
            "success": True,
            "location": {
                "latitude": current_location.get("latitude"),
                "longitude": current_location.get("longitude"),
                "last_updated": timestamp
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get current location: {str(e)}"
        )