from datetime import datetime
from typing import Optional
import os
import requests

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.shared.supabase import get_supabase_client

router = APIRouter()


# Request Models
class SOSRequest(BaseModel):
    user_id: str
    location: Optional[str] = None
    message: Optional[str] = None


class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float


# SOS Endpoint
@router.post("/sos")
def trigger_sos(sos_request: SOSRequest):
    """
    Trigger an SOS emergency call.
    - Inserts into sos_logs table
    - Finds linked caregivers
    - Returns success response
    """
    try:
        if not sos_request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Insert SOS log directly (remove user_id foreign key constraint from database)
        sos_data = {
            "user_id": sos_request.user_id,
            "location": sos_request.location,
            "message": sos_request.message,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        sos_response = supabase.table("sos_logs").insert(sos_data).execute()

        # Simulate emergency call (free version)
        emergency_number = "+6598631975"
        try:
            # Log emergency details
            emergency_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": sos_request.user_id,
                "location": sos_request.location or "Unknown",
                "message": sos_request.message or "No message",
                "emergency_contact": emergency_number
            }
            
            # Simulate call attempt
            print(f"🚨 EMERGENCY CALL SIMULATION 🚨")
            print(f"Calling: {emergency_number}")
            print(f"User: {sos_request.user_id}")
            print(f"Location: {sos_request.location or 'Unknown'}")
            print(f"Message: {sos_request.message or 'No message'}")
            print(f"Time: {datetime.utcnow()}")
            
            call_status = f"Emergency call simulated to {emergency_number}. Check server logs for details."
            
        except Exception as call_error:
            call_status = f"Emergency simulation failed: {str(call_error)}"
        
        # Find linked caregivers
        caregivers_response = (
            supabase.table("caregivers")
            .select("*")
            .eq("user_id", sos_request.user_id)
            .execute()
        )
        caregivers = caregivers_response.data if caregivers_response.data else []

        return {
            "success": True,
            "message": "SOS alert triggered",
            "emergency_whatsapp_sent": f"+{emergency_number}",
            "alert_status": call_status,
            "sos_log": sos_response.data[0] if sos_response.data else None,
            "caregivers_notified": len(caregivers),
            "caregivers": caregivers,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger SOS: {str(e)}")


# Location Endpoint
@router.post("/location")
def update_location(location: LocationRequest):
    """
    Store user's current location in location_logs table.
    """
    try:
        if not location.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        location_data = {
            "user_id": location.user_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": datetime.utcnow().isoformat(),
        }
        response = supabase.table("location_logs").insert(location_data).execute()

        return {
            "success": True,
            "message": "Location stored",
            "data": response.data[0] if response.data else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store location: {str(e)}"
        )


# Status Endpoint
@router.get("/status/{user_id}")
def get_safety_status(user_id: str):
    """
    Return most recent SOS log and last known location for a user.
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Get most recent SOS log
        sos_response = (
            supabase.table("sos_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        recent_sos = sos_response.data[0] if sos_response.data else None

        # Get last known location
        location_response = (
            supabase.table("location_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        last_location = location_response.data[0] if location_response.data else None

        return {
            "success": True,
            "user_id": user_id,
            "recent_sos": recent_sos,
            "last_location": last_location,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get safety status: {str(e)}"
        )
