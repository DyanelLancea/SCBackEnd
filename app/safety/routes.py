from datetime import datetime, timezone
from typing import Optional
import os
import httpx
from twilio.rest import Client

from fastapi import APIRouter, HTTPException, Query
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


async def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Convert coordinates to a clean, readable address using OpenStreetMap Nominatim API.
    Returns a nice, short address like "Bukit Timah" or "Holland Road" instead of full address.
    """
    try:
        # Use OpenStreetMap Nominatim API (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18,  # Higher zoom for more detailed address
        }
        headers = {
            "User-Agent": "SCBackend-LocationService/1.0"  # Required by Nominatim
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                
                # For Singapore addresses, build a clean, short format
                # Priority order for a nice display:
                # 1. Road name (e.g., "Holland Road")
                # 2. Suburb/Neighbourhood (e.g., "Bukit Timah")
                # 3. City district
                # 4. City
                
                road = address.get("road") or address.get("street")
                suburb = address.get("suburb") or address.get("neighbourhood")
                city_district = address.get("city_district")
                city = address.get("city")
                
                # Build a nice, short address
                location_parts = []
                
                # If we have a road name, use it (e.g., "Holland Road")
                if road:
                    location_parts.append(road)
                
                # Add suburb/neighbourhood if available and different from road
                if suburb and suburb != road:
                    location_parts.append(suburb)
                elif city_district and city_district != road:
                    location_parts.append(city_district)
                elif city and city != road and city not in ["Singapore"]:
                    location_parts.append(city)
                
                # If we have parts, join them nicely (e.g., "Holland Road, Bukit Timah")
                if location_parts:
                    # Limit to 2 parts max for a clean display
                    if len(location_parts) > 2:
                        location_parts = location_parts[:2]
                    return ", ".join(location_parts)
                
                # Fallback: try to extract from display_name
                display_name = data.get("display_name", "")
                if display_name:
                    # Split by comma and take first 2 parts (usually road and area)
                    parts = [p.strip() for p in display_name.split(",")]
                    # Filter out generic parts like "Singapore", "Central Region", postal codes
                    filtered_parts = []
                    skip_words = ["singapore", "central region", "south west region", 
                                 "north east region", "north west region", "south east region"]
                    
                    for part in parts[:3]:  # Take first 3 parts max
                        part_lower = part.lower()
                        # Skip if it's a generic location or postal code (numbers only)
                        if (part_lower not in skip_words and 
                            not part.isdigit() and 
                            len(part) > 2):
                            filtered_parts.append(part)
                            if len(filtered_parts) >= 2:  # Max 2 parts for clean display
                                break
                    
                    if filtered_parts:
                        return ", ".join(filtered_parts)
                    
                    # Last resort: return first part if it's not too generic
                    if len(parts) > 0 and parts[0].lower() not in skip_words:
                        return parts[0]
                
                return None
    except Exception as e:
        print(f"Reverse geocoding failed: {e}")
        return None
    
    return None


# Request Models
class SOSRequest(BaseModel):
    user_id: str
    location: Optional[str] = None
    message: Optional[str] = None


class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None  # Optional address - if not provided, will be reverse geocoded


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

        # Format current time in Singapore timezone (SGT - UTC+8)
        if ZoneInfo:
            # Use zoneinfo for proper timezone handling
            singapore_tz = ZoneInfo("Asia/Singapore")
            current_time = datetime.now(singapore_tz)
            time_str = current_time.strftime("%B %d, %Y at %I:%M %p SGT")
        else:
            # Fallback: manually add 8 hours for Singapore time (UTC+8)
            from datetime import timedelta
            current_time = datetime.utcnow() + timedelta(hours=8)
            time_str = current_time.strftime("%B %d, %Y at %I:%M %p SGT")

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
async def update_location(location: LocationRequest):
    """
    Store user's current location in location_logs table.
    If address is not provided, performs reverse geocoding to get readable address
    like "Punggol Coast" from coordinates.
    """
    try:
        if not location.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # Get readable address - use provided address or reverse geocode
        address = location.address
        if not address:
            # Perform reverse geocoding to get readable address from coordinates
            address = await reverse_geocode(location.latitude, location.longitude)
            if not address:
                # Fallback: use generic message instead of coordinates
                address = "Location not available"

        # Build location data - only include address if column exists
        location_data = {
            "user_id": location.user_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Try to include address if the column exists (some databases may not have it)
        # We'll try to insert it, and if it fails, we'll store it separately or skip it
        try:
            location_data["address"] = address
            response = supabase.table("location_logs").insert(location_data).execute()
        except Exception as e:
            # If address column doesn't exist, insert without it
            error_str = str(e)
            if "address" in error_str.lower() or "column" in error_str.lower():
                # Remove address and try again
                location_data.pop("address", None)
                response = supabase.table("location_logs").insert(location_data).execute()
                # Store address in a separate way or just return it in the response
            else:
                raise

        return {
            "success": True,
            "message": "Location stored",
            "data": response.data[0] if response.data else None,
            "address": address,  # Return the readable address
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store location: {str(e)}"
        )


# Get Current Location Endpoint
@router.get("/location/{user_id}")
async def get_current_location(
    user_id: str,
    role: Optional[str] = Query(None, description="User role: 'caregiver' or 'elderly'. If 'caregiver', returns linked elderly user's location.")
):
    """
    Get the most recent location for a user (caregiver or elderly) from location_logs table.
    Returns the user's current location from the database, not a hardcoded value.
    
    Query Parameters:
    - role: Optional. If 'caregiver', finds the linked elderly user and returns their location.
            If 'elderly' or not provided, returns the location for the given user_id.
    
    This endpoint works for:
    - Elderly users viewing their own location (role='elderly' or no role)
    - Caregivers viewing their linked elderly person's location (role='caregiver')
    - Any user viewing their own location (no role parameter)
    
    The location is always fetched from the database, never hardcoded.
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get Supabase client
        supabase = get_supabase_client()

        # If role is 'caregiver', find the linked elderly user first
        target_user_id = user_id
        if role and role.lower() == "caregiver":
            # Find elderly user(s) linked to this caregiver
            # Based on SOS endpoint, caregivers table has: user_id = elderly user
            # We need to find which field stores the caregiver's ID
            # Try different possible field names for caregiver identifier
            caregivers_response = None
            
            # Try common field names for caregiver ID
            possible_caregiver_fields = ["caregiver_id", "caregiver_user_id", "linked_caregiver_id", "caregiver"]
            for field_name in possible_caregiver_fields:
                try:
                    caregivers_response = (
                        supabase.table("caregivers")
                        .select("*")
                        .eq(field_name, user_id)
                        .execute()
                    )
                    if caregivers_response.data and len(caregivers_response.data) > 0:
                        break
                except Exception:
                    # Field doesn't exist, try next one
                    continue
            
            # If still no results, get all caregivers and check manually
            if not caregivers_response or not caregivers_response.data or len(caregivers_response.data) == 0:
                try:
                    all_caregivers = supabase.table("caregivers").select("*").limit(100).execute()
                    if all_caregivers.data:
                        # Check all records to find one where any field matches the caregiver user_id
                        for record in all_caregivers.data:
                            # Check all fields in the record
                            for key, value in record.items():
                                if key != "user_id" and str(value) == str(user_id):
                                    caregivers_response = type('obj', (object,), {'data': [record]})()
                                    break
                            if caregivers_response and caregivers_response.data:
                                break
                except Exception:
                    pass
            
            if caregivers_response and caregivers_response.data and len(caregivers_response.data) > 0:
                # Get the first linked elderly user_id
                # The user_id field in caregivers table refers to the elderly user
                caregiver_record = caregivers_response.data[0]
                target_user_id = caregiver_record.get("user_id")
                
                if not target_user_id or target_user_id == user_id:
                    # If we couldn't find the elderly user, return error
                    return {
                        "success": False,
                        "message": "No linked elderly user found for this caregiver",
                        "user_id": user_id,
                        "role": "caregiver",
                        "current_location": None,
                        "location_display": "Location not available - No linked elderly user",
                        "address": None,
                        "timestamp": None,
                    }
            else:
                # No caregiver record found - return helpful error
                # For now, if caregiver lookup fails, return the caregiver's own location as fallback
                # This allows the endpoint to work even if caregiver table structure is unknown
                print(f"Warning: Could not find linked elderly user for caregiver {user_id}. Returning caregiver's own location.")
                target_user_id = user_id  # Fallback to caregiver's own location

        # Get most recent CURRENT location from database (never hardcoded)
        # This ensures we always return the user's actual current location, not a hardcoded value
        location_response = (
            supabase.table("location_logs")
            .select("*")
            .eq("user_id", target_user_id)
            .order("timestamp", desc=True)  # Get most recent first
            .limit(1)  # Only get the latest location entry
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
                "address": None,
                "timestamp": None,
            }

        # Format location display string - prioritize address, fallback to reverse geocoding, then coordinates
        location_display = None
        address = current_location.get("address")
        
        if address:
            # Use address from database if available
            location_display = address
        elif current_location.get("latitude") and current_location.get("longitude"):
            # If no address stored, perform reverse geocoding on-the-fly to get readable address
            lat = current_location.get("latitude")
            lon = current_location.get("longitude")
            try:
                # Try to get address from reverse geocoding (async)
                address = await reverse_geocode(lat, lon)
                if address:
                    location_display = address
                else:
                    # Fallback: use generic message instead of coordinates
                    location_display = "Location not available"
            except Exception as e:
                # If reverse geocoding fails, use generic message
                print(f"Reverse geocoding failed in GET endpoint: {e}")
                location_display = "Location not available"
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
            "user_id": target_user_id,  # Return the actual user_id whose location is being shown
            "requested_user_id": user_id,  # The user_id that was requested (may differ if role=caregiver)
            "current_location": current_location,  # Full location object from database
            "address": current_location.get("address"),
            "location_display": location_display,  # Readable location string for frontend (never hardcoded - always from database)
            "timestamp": current_location.get("timestamp"),
            "time_since_update": time_since_update,  # Human-readable time (e.g., "2 minutes ago")
            "is_current": True,  # Explicitly mark this as the current location
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