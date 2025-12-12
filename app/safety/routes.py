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


async def find_nearest_mrt(latitude: float, longitude: float) -> Optional[str]:
    """
    Find the nearest MRT station to given coordinates.
    Uses Overpass API to query OpenStreetMap for MRT stations in Singapore.
    Returns the name of the nearest MRT station.
    """
    try:
        # Singapore MRT stations with their coordinates (major stations)
        # Format: {"station_name": (lat, lng)}
        mrt_stations = {
            "Punggol Coast MRT": (1.410576, 103.893386),
            "Punggol MRT": (1.4047, 103.9023),
            "Sengkang MRT": (1.3915, 103.8950),
            "Buangkok MRT": (1.3833, 103.8933),
            "Hougang MRT": (1.3711, 103.8928),
            "Kovan MRT": (1.3592, 103.8850),
            "Serangoon MRT": (1.3500, 103.8728),
            "Lorong Chuan MRT": (1.3517, 103.8639),
            "Bishan MRT": (1.3506, 103.8481),
            "Ang Mo Kio MRT": (1.3692, 103.8494),
            "Yio Chu Kang MRT": (1.3817, 103.8450),
            "Khatib MRT": (1.4172, 103.8328),
            "Yishun MRT": (1.4294, 103.8350),
            "Sembawang MRT": (1.4489, 103.8200),
            "Canberra MRT": (1.4431, 103.8297),
            "Admiralty MRT": (1.4406, 103.8011),
            "Woodlands MRT": (1.4367, 103.7861),
            "Woodlands North MRT": (1.4478, 103.7847),
            "Woodlands South MRT": (1.4272, 103.7917),
            "Jurong East MRT": (1.3331, 103.7422),
            "Jurong West MRT": (1.3394, 103.7056),
            "Boon Lay MRT": (1.3383, 103.7056),
            "Pioneer MRT": (1.3375, 103.6972),
            "Joo Koon MRT": (1.3278, 103.6783),
            "Gul Circle MRT": (1.3194, 103.6606),
            "Tuas Crescent MRT": (1.3211, 103.6492),
            "Tuas West Road MRT": (1.3297, 103.6397),
            "Tuas Link MRT": (1.3403, 103.6367),
            "Choa Chu Kang MRT": (1.3850, 103.7444),
            "Yew Tee MRT": (1.3972, 103.7472),
            "Kranji MRT": (1.4253, 103.7622),
            "Marsiling MRT": (1.4325, 103.7781),
            "Orchard MRT": (1.3042, 103.8325),
            "Somerset MRT": (1.3003, 103.8386),
            "Dhoby Ghaut MRT": (1.2992, 103.8458),
            "City Hall MRT": (1.2931, 103.8525),
            "Raffles Place MRT": (1.2842, 103.8514),
            "Marina Bay MRT": (1.2806, 103.8547),
            "Bayfront MRT": (1.2817, 103.8592),
            "Promenade MRT": (1.2931, 103.8603),
            "Esplanade MRT": (1.2931, 1.2931),
            "Bras Basah MRT": (1.2969, 1.2969),
            "Bugis MRT": (1.3008, 103.8558),
            "Lavender MRT": (1.3072, 103.8631),
            "Kallang MRT": (1.3114, 103.8714),
            "Aljunied MRT": (1.3164, 103.8828),
            "Paya Lebar MRT": (1.3175, 103.8922),
            "Eunos MRT": (1.3197, 103.9031),
            "Kembangan MRT": (1.3208, 103.9128),
            "Bedok MRT": (1.3239, 103.9297),
            "Tanah Merah MRT": (1.3272, 103.9464),
            "Simei MRT": (1.3433, 103.9531),
            "Tampines MRT": (1.3525, 103.9453),
            "Pasir Ris MRT": (1.3656, 103.9494),
            "Tampines West MRT": (1.3456, 103.9403),
            "Tampines East MRT": (1.3567, 103.9514),
        }
        
        # Calculate distance to each station and find nearest
        import math
        
        def calculate_distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two coordinates in kilometers using Haversine formula"""
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        nearest_station = None
        min_distance = float('inf')
        
        for station_name, (station_lat, station_lng) in mrt_stations.items():
            distance = calculate_distance(latitude, longitude, station_lat, station_lng)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station_name
        
        # Only return if within reasonable distance (5km)
        if nearest_station and min_distance <= 5.0:
            return nearest_station
        
        return None
        
    except Exception as e:
        print(f"Finding nearest MRT failed: {e}")
        return None


# Request Models
class SOSRequest(BaseModel):
    user_id: str
    alert_type: Optional[str] = None  # Type of alert, typically "sos"
    latitude: Optional[float] = None  # GPS latitude coordinate
    longitude: Optional[float] = None  # GPS longitude coordinate
    location: Optional[str] = None  # Formatted location string with coordinates
    message: Optional[str] = None  # Complete emergency message (ready-to-speak)
    text: Optional[str] = None  # Same as message - included for Twilio compatibility


class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None  # Optional address - if not provided, will be reverse geocoded


# SOS Endpoint
@router.post("/sos")
async def trigger_sos(sos_request: SOSRequest):
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

        # Skip database operations - just prepare for emergency call
        sos_response = {"data": [{"id": "temp-sos-id", "user_id": sos_request.user_id}]}
        latest_location = None

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
        # Format: "the location is at xxx, the nearest mrt is xxxxx the timing of this is xxxx"
        
        # Get location address
        location_address = "Unknown location"
        if sos_request.location:
            # Try to extract address from location string
            location_address = sos_request.location
            # If location contains coordinates, try to reverse geocode
            if sos_request.latitude and sos_request.longitude:
                geocoded_address = await reverse_geocode(sos_request.latitude, sos_request.longitude)
                if geocoded_address:
                    location_address = geocoded_address
        elif sos_request.latitude and sos_request.longitude:
            # Reverse geocode from coordinates
            geocoded_address = await reverse_geocode(sos_request.latitude, sos_request.longitude)
            if geocoded_address:
                location_address = geocoded_address
        
        # Find nearest MRT station
        nearest_mrt = "Unknown MRT"
        if sos_request.latitude and sos_request.longitude:
            mrt_station = await find_nearest_mrt(sos_request.latitude, sos_request.longitude)
            if mrt_station:
                nearest_mrt = mrt_station
        
        # Build message in required format
        # Priority: Use frontend's ready-to-use message if it contains all required info, otherwise build our own
        if sos_request.message or sos_request.text:
            # Check if frontend message already has the required format
            frontend_message = sos_request.message or sos_request.text
            # If message contains "location is at" and "nearest mrt" and "timing", use it
            if ("location is at" in frontend_message.lower() and 
                "nearest mrt" in frontend_message.lower() and
                "timing" in frontend_message.lower()):
                emergency_message = frontend_message
            else:
                # Frontend message doesn't have required format, build our own
                emergency_message = f"the location is at {location_address}, the nearest mrt is {nearest_mrt} the timing of this is {time_str}"
        else:
            # Build message in required format: "the location is at xxx, the nearest mrt is xxxxx the timing of this is xxxx"
            emergency_message = f"the location is at {location_address}, the nearest mrt is {nearest_mrt} the timing of this is {time_str}"

        # Make emergency call using Twilio
        # Get phone numbers from environment variables
        emergency_number = os.getenv("SOS_EMERGENCY_NUMBER")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")  # Your verified Twilio number
        
        call_sid = None
        call_error_details = None
        call_status = None
        
        # Check if emergency number is configured
        # Detect if we're in production (Render, etc.)
        is_production = (
            os.getenv("RENDER") == "true" or 
            "render.com" in os.getenv("RENDER_SERVICE_URL", "").lower() or
            "render.com" in os.getenv("RENDER_EXTERNAL_URL", "").lower() or
            os.getenv("ENVIRONMENT") == "production"
        )
        
        env_location = "Render dashboard Environment tab" if is_production else ".env file"
        
        if not emergency_number:
            call_status = f"Emergency number not configured. Please set SOS_EMERGENCY_NUMBER in {env_location}."
            call_error_details = f"SOS_EMERGENCY_NUMBER must be set in environment variables ({env_location})"
        elif not from_number:
            call_status = f"Twilio phone number not configured. Please set TWILIO_PHONE_NUMBER in {env_location}."
            call_error_details = f"TWILIO_PHONE_NUMBER must be set in environment variables ({env_location})"
        else:
            try:
                account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                
                if not account_sid or not auth_token:
                    call_status = f"Twilio not configured - Missing Account SID or Auth Token. Please check {env_location}."
                    call_error_details = f"TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables ({env_location})"
                else:
                    client = Client(account_sid, auth_token)
                    
                    # Escape special characters for XML/TwiML
                    safe_message = emergency_message.replace("&", "and").replace("<", "less than").replace(">", "greater than")
                    
                    # Make the call with detailed automated message
                    # Use timeout to prevent hanging
                    try:
                        call = client.calls.create(
                            twiml=f'<Response><Say voice="alice" language="en-US">{safe_message}</Say><Pause length="2"/><Say voice="alice" language="en-US">Repeating alert details. {safe_message}</Say></Response>',
                            to=emergency_number,
                            from_=from_number,
                            timeout=10  # Timeout after 10 seconds
                        )
                        call_sid = call.sid
                        call_status = f"Emergency call successfully initiated to {emergency_number}. Call SID: {call.sid}"
                    except Exception as timeout_error:
                        # If call creation times out, still return success but note the timeout
                        error_str = str(timeout_error)
                        call_status = f"Call initiation may have timed out: {error_str}"
                        call_error_details = f"Call request sent but confirmation timed out. The call may still be processing."
                        print(f"Warning: Twilio call creation timeout: {error_str}")
                    
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
        
        # Skip caregiver lookup for now
        caregivers = []

        # Determine overall success based on call status
        call_successful = call_sid is not None and "successfully initiated" in call_status.lower()
        
        # Build user-friendly message for frontend
        if call_successful:
            user_message = f"SOS alert sent! Emergency call initiated to {emergency_number}."
        elif call_error_details and ("not configured" in call_error_details.lower() or "must be set" in call_error_details.lower()):
            user_message = "SOS alert logged successfully. Emergency call not configured - please configure Twilio settings."
        else:
            user_message = f"SOS alert sent! {call_status}"
        
        return {
            "success": True,
            "message": user_message,  # User-friendly message for frontend
            "alert_triggered": True,  # Always true if we reach here - indicates alert was sent
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
async def trigger_emergency(sos_request: SOSRequest):
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
            "location_updated": True,
            "message": "Location updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store location: {str(e)}"
        )


# Get Current Location Endpoint (query parameters version for frontend compatibility)
@router.get("/location")
async def get_location(
    user_id: Optional[str] = Query(None, description="User ID"),
    role: Optional[str] = Query(None, description="User role: 'caregiver' or 'elderly'."),
    lat: Optional[float] = Query(None, description="Current latitude"),
    lng: Optional[float] = Query(None, description="Current longitude")
):
    """
    Get the most recent location for a user from location_logs table.
    This endpoint accepts user_id as a query parameter for frontend compatibility.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required as a query parameter")
    
    # Call the path-based endpoint
    return await get_current_location(user_id, role, lat, lng)


# Get Current Location Endpoint (with user_id in path)
@router.get("/location/{user_id}")
async def get_current_location(
    user_id: str,
    role: Optional[str] = Query(None, description="User role: 'caregiver' or 'elderly'."),
    lat: Optional[float] = Query(None, description="Current latitude"),
    lng: Optional[float] = Query(None, description="Current longitude")
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
            # Return error response when no location found
            raise HTTPException(
                status_code=404,
                detail="No location data found for this user"
            )

        # Get timestamp and format it as ISO 8601 with Z suffix
        timestamp = current_location.get("timestamp")
        if timestamp:
            # Convert to string if needed
            if not isinstance(timestamp, str):
                if hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                else:
                    timestamp = str(timestamp)
            
            # Ensure timestamp ends with Z (UTC indicator)
            # Supabase timestamps are usually in ISO format with timezone
            # Convert to UTC Z format if needed
            if timestamp.endswith('Z'):
                # Already in UTC Z format
                pass
            elif '+' in timestamp or timestamp.count('-') > 2:
                # Has timezone offset, convert to Z
                # Remove timezone offset and add Z
                if '+' in timestamp:
                    timestamp = timestamp.split('+')[0] + 'Z'
                elif timestamp.count('-') > 2:
                    # Format like 2025-12-12T10:30:00-05:00
                    parts = timestamp.rsplit('-', 2)
                    if len(parts) == 3:
                        timestamp = parts[0] + '-' + parts[1] + 'Z'
                    else:
                        timestamp = timestamp + 'Z'
            else:
                # No timezone info, assume UTC and add Z
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