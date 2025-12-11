from datetime import datetime, timezone
from typing import Optional
import os
from twilio.rest import Client

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.shared.supabase import get_supabase_client

# Try to import zoneinfo for timezone handling
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older Python versions
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None

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

        # Get latest location data if available
        location_response = (
            supabase.table("location_logs")
            .select("*")
            .eq("user_id", sos_request.user_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        latest_location = location_response.data[0] if location_response.data else None

        # Format current time
        current_time = datetime.utcnow()
        time_str = current_time.strftime("%B %d, %Y at %I:%M %p UTC")

        # Extract area name from location - prioritize the exact location from SOS request
        # Priority: 1) Exact location from SOS request, 2) Extract area from request location, 3) Latest location from DB, 4) Unknown
        area_name = None
        location_info = "Unknown location"
        
        # First, use the location directly from the SOS request if it's a simple area name
        if sos_request.location:
            location_str = sos_request.location.strip()
            
            # Common area patterns in Singapore (can be extended)
            singapore_areas = [
                "Punggol Coast", "Punggol", "Jurong", "Tampines", "Woodlands",
                "Yishun", "Ang Mo Kio", "Bishan", "Toa Payoh", "Orchard",
                "Marina Bay", "Sentosa", "Changi", "Pasir Ris", "Sengkang",
                "Hougang", "Bedok", "Clementi", "Queenstown", "Bukit Timah"
            ]
            
            # Check if the location string exactly matches or contains a known area
            location_lower = location_str.lower()
            for area in singapore_areas:
                area_lower = area.lower()
                # Check for exact match or if location contains the area name
                if location_lower == area_lower or area_lower in location_lower:
                    area_name = area
                    break
            
            # If no exact area match found, check if it's a simple name (1-3 words, no commas/numbers)
            if not area_name:
                # Check if location is already a simple area name (no complex address)
                parts = location_str.replace(',', ' ').replace('-', ' ').split()
                # If it's 1-3 words and doesn't look like coordinates or full address
                if len(parts) <= 3 and not any(char.isdigit() for char in location_str):
                    # Use the location as-is (it's likely already an area name)
                    area_name = location_str
                else:
                    # Extract first 2 words as area name from longer address
                    if len(parts) >= 2:
                        area_name = ' '.join(parts[:2])
                    else:
                        area_name = location_str
        
        # If no area from request, check latest location from database (fallback only)
        if not area_name and latest_location:
            # Check if location_logs has an address field
            if latest_location.get("address"):
                address = latest_location.get("address")
                # Extract area from address
                parts = address.replace(',', ' ').split()
                if len(parts) >= 2:
                    area_name = ' '.join(parts[:2])
                else:
                    area_name = address
        
        # Build location message - use the area name extracted from SOS request location
        if area_name:
            location_info = f"Area: {area_name}"
        elif latest_location and latest_location.get("address"):
            # Fallback: Use address from database if available
            location_info = f"Area: {latest_location.get('address')}"
        else:
            location_info = "Unknown location"

        # Build the automated message for the phone call
        message_parts = [
            "Emergency SOS Alert.",
            f"This is an automated emergency alert from user {sos_request.user_id}.",
            f"Alert triggered on {time_str}.",
            f"Location: {location_info}.",
        ]
        
        if sos_request.message:
            message_parts.append(f"User message: {sos_request.message}.")
        
        message_parts.append("This requires immediate attention. Please respond as soon as possible.")
        emergency_message = " ".join(message_parts)

        # Make emergency call using Twilio
        # Get phone numbers from environment variables
        emergency_number = os.getenv("SOS_EMERGENCY_NUMBER")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")  # Your verified Twilio number
        
        call_sid = None
        call_error_details = None
        call_status = None
        
        # Check if emergency number is configured
        if not emergency_number:
            call_status = "Emergency number not configured. Please set SOS_EMERGENCY_NUMBER in your .env file."
            call_error_details = "SOS_EMERGENCY_NUMBER must be set in environment variables"
        elif not from_number:
            call_status = "Twilio phone number not configured. Please set TWILIO_PHONE_NUMBER in your .env file."
            call_error_details = "TWILIO_PHONE_NUMBER must be set in environment variables"
        else:
            try:
                account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                
                if not account_sid or not auth_token:
                    call_status = "Twilio not configured - Missing Account SID or Auth Token. Please check your .env file."
                    call_error_details = "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables"
                else:
                    client = Client(account_sid, auth_token)
                    
                    # Escape special characters for XML/TwiML
                    safe_message = emergency_message.replace("&", "and").replace("<", "less than").replace(">", "greater than")
                    
                    # Make the call with detailed automated message
                    call = client.calls.create(
                        twiml=f'<Response><Say voice="alice" language="en-US">{safe_message}</Say><Pause length="2"/><Say voice="alice" language="en-US">Repeating alert details. {safe_message}</Say></Response>',
                        to=emergency_number,
                        from_=from_number
                    )
                    call_sid = call.sid
                    call_status = f"Emergency call successfully initiated to {emergency_number}. Call SID: {call.sid}"
                    
            except Exception as call_error:
                error_str = str(call_error)
                call_status = f"Call failed: {error_str}"
                call_error_details = error_str
                
                # Provide helpful error messages for common issues
                if "not yet verified" in error_str.lower():
                    call_error_details = f"The phone number {from_number} is not verified in your Twilio account. Please verify it or use a different Twilio number."
                elif "not authorized to call" in error_str.lower() or "geo-permissions" in error_str.lower():
                    call_error_details = f"Your Twilio account is not authorized to call {emergency_number}. Enable international calling permissions at: https://www.twilio.com/console/voice/calls/geo-permissions/low-risk"
                elif "http error" in error_str.lower():
                    # Extract more details from Twilio error
                    if "21210" in error_str:
                        call_error_details = f"The source phone number {from_number} is not verified. Verify it in Twilio Console or use your actual Twilio number."
                    elif "21215" in error_str:
                        call_error_details = f"International calling not enabled for {emergency_number}. Enable at: https://www.twilio.com/console/voice/calls/geo-permissions/low-risk"
                    elif "21211" in error_str:
                        call_error_details = f"Invalid phone number format: {emergency_number}. Check the number format."
        
        # Find linked caregivers
        caregivers_response = (
            supabase.table("caregivers")
            .select("*")
            .eq("user_id", sos_request.user_id)
            .execute()
        )
        caregivers = caregivers_response.data if caregivers_response.data else []

        # Determine overall success based on call status
        call_successful = call_sid is not None and "successfully initiated" in call_status.lower()
        
        return {
            "success": True,
            "message": "SOS alert triggered",
            "emergency_call_initiated": emergency_number,
            "call_from_number": from_number,
            "call_sid": call_sid,
            "alert_status": call_status,
            "call_successful": call_successful,
            "error_details": call_error_details,
            "sos_log": sos_response.data[0] if sos_response.data else None,
            "caregivers_notified": len(caregivers),
            "caregivers": caregivers,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger SOS: {str(e)}")


# Emergency Endpoint (alias for /sos for frontend compatibility)
@router.post("/emergency")
def trigger_emergency(sos_request: SOSRequest):
    """
    Trigger an emergency alert (alias for /sos endpoint).
    This endpoint exists for frontend compatibility.
    """
    # Simply call the SOS endpoint
    return trigger_sos(sos_request)


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


# Get Current Location Endpoint
@router.get("/location/{user_id}")
def get_current_location(user_id: str):
    """
    Get the most recent location for a user (caregiver or elderly) from location_logs table.
    Returns the user's current location from the database, not a hardcoded value.
    
    This endpoint works for:
    - Elderly users viewing their own location
    - Caregivers viewing an elderly person's location (pass elderly user_id)
    - Any user viewing their own location
    
    The location is always fetched from the database, never hardcoded.
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Get most recent location from database (never hardcoded)
        location_response = (
            supabase.table("location_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        
        current_location = location_response.data[0] if location_response.data else None

        if not current_location:
            return {
                "success": True,
                "message": "No location data found for this user",
                "user_id": user_id,
                "current_location": None,
                "location_display": "Location not available",
                "latitude": None,
                "longitude": None,
                "address": None,
                "timestamp": None,
            }

        # Format location display string - prioritize address, fallback to coordinates
        location_display = None
        if current_location.get("address"):
            # Use address from database if available
            location_display = current_location.get("address")
        elif current_location.get("latitude") and current_location.get("longitude"):
            # Format coordinates as readable string if no address available
            lat = current_location.get("latitude")
            lon = current_location.get("longitude")
            location_display = f"Lat: {lat:.6f}, Lon: {lon:.6f}"
        else:
            location_display = "Location not available"

        # Calculate time since last update
        time_since_update = None
        if current_location.get("timestamp"):
            try:
                timestamp_str = current_location.get("timestamp")
                if isinstance(timestamp_str, str):
                    # Parse ISO format timestamp
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] + '+00:00'
                    location_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if location_time.tzinfo is None:
                        location_time = location_time.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    diff = now - location_time
                    minutes_ago = int(diff.total_seconds() / 60)
                    if minutes_ago < 1:
                        time_since_update = "Just now"
                    elif minutes_ago == 1:
                        time_since_update = "1 minute ago"
                    else:
                        time_since_update = f"{minutes_ago} minutes ago"
            except Exception:
                time_since_update = None

        return {
            "success": True,
            "user_id": user_id,
            "current_location": current_location,
            "latitude": current_location.get("latitude"),
            "longitude": current_location.get("longitude"),
            "address": current_location.get("address"),
            "location_display": location_display,  # Readable location string for frontend (never hardcoded)
            "timestamp": current_location.get("timestamp"),
            "time_since_update": time_since_update,  # Human-readable time (e.g., "2 minutes ago")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get current location: {str(e)}"
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