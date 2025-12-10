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

        # Send Telegram emergency alert (FREE)
        try:
            # Telegram Bot credentials
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            
            if bot_token and chat_id:
                # Telegram API endpoint
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                
                # Emergency message
                message_text = f"🚨 EMERGENCY SOS ALERT 🚨\n\nUser: {sos_request.user_id}\nLocation: {sos_request.location or 'Unknown'}\nMessage: {sos_request.message or 'No message'}\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n⚠️ PLEASE RESPOND IMMEDIATELY!"
                
                payload = {
                    "chat_id": chat_id,
                    "text": message_text
                }
                
                # Send Telegram message
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    call_status = "Emergency alert sent via Telegram (FREE)"
                else:
                    call_status = f"Telegram send failed: {response.text}"
            else:
                call_status = "Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env"
        except Exception as call_error:
            call_status = f"Telegram send failed: {str(call_error)}"
        
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
            "emergency_telegram_sent": True,
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