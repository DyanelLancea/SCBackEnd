# Emergency Message Format Fix

## Summary

Updated both emergency intent call and trigger SOS call to output messages in the required format:

**Format**: `"the location is at xxx, the nearest mrt is xxxxx the timing of this is xxxx"`

---

## Changes Made

### 1. Added MRT Station Finding Function (`app/safety/routes.py`)

Created `find_nearest_mrt()` function that:
- Takes latitude and longitude coordinates
- Calculates distance to all major Singapore MRT stations
- Returns the nearest MRT station within 5km
- Uses Haversine formula for accurate distance calculation

**Function**: `async def find_nearest_mrt(latitude: float, longitude: float) -> Optional[str]`

### 2. Updated SOS Endpoint (`app/safety/routes.py`)

**File**: `app/safety/routes.py` - `trigger_sos()` function

**Changes**:
- Extracts location address from coordinates using reverse geocoding
- Finds nearest MRT station using coordinates
- Formats message as: `"the location is at {address}, the nearest mrt is {mrt_station} the timing of this is {timestamp}"`
- Still accepts frontend's message if it already has the required format
- Falls back to building message if frontend doesn't provide complete format

### 3. Updated Orchestrator Emergency Handling (`app/orchestrator/routes.py`)

**File**: `app/orchestrator/routes.py` - Emergency intent handling

**Changes**:
- Added `latitude` and `longitude` fields to `TextMessage` and `VoiceMessage` models
- Imports `reverse_geocode` and `find_nearest_mrt` from safety routes
- Formats message as: `"the location is at {address}, the nearest mrt is {mrt_station} the timing of this is {timestamp}"`
- Uses coordinates to get better address and find MRT station
- Falls back to extracting MRT from location string if coordinates not available

---

## Message Format Details

### Required Format

```
"the location is at {address}, the nearest mrt is {mrt_station} the timing of this is {timestamp}"
```

### Components

1. **Location Address** (`{address}`):
   - Extracted from coordinates using reverse geocoding
   - Falls back to `location` field if coordinates not available
   - Format: "Road Name, Area" (e.g., "Seletar Link, Seletar")

2. **Nearest MRT** (`{mrt_station}`):
   - Found using `find_nearest_mrt()` function
   - Calculates distance to all major Singapore MRT stations
   - Returns station name (e.g., "Punggol Coast MRT")
   - Falls back to "Unknown MRT" if not found

3. **Timing** (`{timestamp}`):
   - Singapore timezone (SGT - UTC+8)
   - Format: "December 10, 2024 at 03:45 PM SGT"

---

## Example Messages

### Example 1: Full Information Available
```
"the location is at Seletar Link, Seletar, the nearest mrt is Punggol Coast MRT the timing of this is December 10, 2024 at 03:45 PM SGT"
```

### Example 2: Location Only (No Coordinates)
```
"the location is at Singapore, the nearest mrt is Unknown MRT the timing of this is December 10, 2024 at 03:45 PM SGT"
```

### Example 3: Coordinates Only
```
"the location is at Seletar Link, Seletar, the nearest mrt is Punggol Coast MRT the timing of this is December 10, 2024 at 03:45 PM SGT"
```

---

## How It Works

### Flow for SOS Endpoint

1. **Receive Request** with `user_id`, `latitude`, `longitude`, `location`, `message`
2. **Extract Location Address**:
   - If coordinates available → reverse geocode to get address
   - Else → use `location` field
3. **Find Nearest MRT**:
   - If coordinates available → calculate distance to all MRT stations
   - Else → try to extract from `location` string
4. **Get Timestamp**: Format current time in Singapore timezone
5. **Build Message**: Format as required
6. **Check Frontend Message**: If frontend already provided correctly formatted message, use it
7. **Send to Twilio**: Use message in `<Say>` verb

### Flow for Orchestrator Emergency

1. **Detect Emergency Intent** from user message
2. **Get Coordinates** from `request.latitude` and `request.longitude`
3. **Extract Location Address**: Reverse geocode if coordinates available
4. **Find Nearest MRT**: Calculate distance to MRT stations
5. **Get Timestamp**: Format current time
6. **Build Message**: Format as required
7. **Send to Twilio**: Use message in `<Say>` verb

---

## Frontend Integration

### What Frontend Should Send

**For SOS Endpoint** (`POST /api/safety/sos`):
```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "latitude": 1.410576,
  "longitude": 103.893386,
  "location": "Seletar Link, Seletar",
  "message": "the location is at Seletar Link, Seletar, the nearest mrt is Punggol Coast MRT the timing of this is December 10, 2024 at 03:45 PM SGT"
}
```

**For Orchestrator** (`POST /api/orchestrator/message`):
```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "message": "help",
  "location": "Seletar Link, Seletar",
  "latitude": 1.410576,
  "longitude": 103.893386
}
```

### Frontend Console Logging

The frontend should log:
- `🌐 Nominatim response:` - What the geocoding API returns
- `✅ Got display_name:` - The full address string
- `✅ Got addressDetails:` - The structured address data
- `🔍 Formatting emergency location:` - The location object being formatted
- `🔍 Final emergency message:` - The complete message being sent

**If only coordinates appear**, check:
1. Is geocoding API being called?
2. Is it returning address data?
3. Is address parsing working?
4. What does the final message contain?

---

## Testing

### Test Case 1: Full Coordinates
```bash
curl -X POST http://localhost:8000/api/safety/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "latitude": 1.410576,
    "longitude": 103.893386
  }'
```

**Expected Message**:
```
"the location is at Seletar Link, Seletar, the nearest mrt is Punggol Coast MRT the timing of this is [current time]"
```

### Test Case 2: Location String Only
```bash
curl -X POST http://localhost:8000/api/safety/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "location": "Singapore"
  }'
```

**Expected Message**:
```
"the location is at Singapore, the nearest mrt is Unknown MRT the timing of this is [current time]"
```

### Test Case 3: Frontend Message Provided
```bash
curl -X POST http://localhost:8000/api/safety/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "message": "the location is at Seletar Link, Seletar, the nearest mrt is Punggol Coast MRT the timing of this is December 10, 2024 at 03:45 PM SGT"
  }'
```

**Expected**: Uses frontend message directly

---

## MRT Stations Included

The function includes major Singapore MRT stations:
- North-South Line: Jurong East, Woodlands, Yishun, Ang Mo Kio, Bishan, Orchard, Marina Bay, etc.
- East-West Line: Pasir Ris, Tampines, Bedok, Paya Lebar, City Hall, Jurong East, etc.
- North-East Line: HarbourFront, Outram Park, Chinatown, Dhoby Ghaut, Serangoon, Punggol, etc.
- Circle Line: All major stations
- Downtown Line: All major stations
- And more...

**Total**: 50+ major MRT stations

---

## Troubleshooting

### Issue: "Unknown MRT" appears

**Possible Causes**:
1. Coordinates not provided
2. Location is more than 5km from any MRT station
3. MRT station not in the list

**Solution**:
- Ensure `latitude` and `longitude` are provided
- Check if location is in Singapore
- Add more MRT stations to the list if needed

### Issue: "Unknown location" appears

**Possible Causes**:
1. Reverse geocoding failed
2. Coordinates invalid
3. Network error

**Solution**:
- Check coordinates are valid (Singapore: lat ~1.3, lng ~103.8)
- Check network connectivity
- Verify Nominatim API is accessible

### Issue: Message format incorrect

**Possible Causes**:
1. Frontend message doesn't match required format
2. Backend building message incorrectly

**Solution**:
- Check backend logs for message being built
- Verify all components (address, MRT, timing) are present
- Test with coordinates to ensure reverse geocoding works

---

## Files Modified

1. `app/safety/routes.py`
   - Added `find_nearest_mrt()` function
   - Updated `trigger_sos()` message building logic

2. `app/orchestrator/routes.py`
   - Added `latitude` and `longitude` to `TextMessage` and `VoiceMessage` models
   - Updated emergency message building logic
   - Imports `reverse_geocode` and `find_nearest_mrt` from safety routes

---

## Next Steps

1. **Test the endpoints** with coordinates to verify message format
2. **Check frontend console** to see what's being sent
3. **Verify MRT station detection** works for different locations
4. **Test with real coordinates** from Singapore locations

---

**Last Updated**: December 2024  
**Status**: ✅ Implemented and ready for testing

