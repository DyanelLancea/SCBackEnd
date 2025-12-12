# Backend Emergency Message Integration Guide

This document describes how the backend integrates frontend emergency messages into Twilio calls.

---

## Request Format

When an emergency is triggered (SOS button or voice emergency intent), the frontend sends a POST request to `/api/safety/sos` with the following body structure:

```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "alert_type": "sos",
  "latitude": 1.410576,
  "longitude": 103.893386,
  "location": "Lat: 1.410576, Lng: 103.893386",
  "message": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386).",
  "text": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
}
```

---

## Backend Implementation

### SOSRequest Model

The backend `SOSRequest` model accepts all frontend fields:

```python
class SOSRequest(BaseModel):
    user_id: str
    alert_type: Optional[str] = None  # Type of alert, typically "sos"
    latitude: Optional[float] = None  # GPS latitude coordinate
    longitude: Optional[float] = None  # GPS longitude coordinate
    location: Optional[str] = None  # Formatted location string with coordinates
    message: Optional[str] = None  # Complete emergency message (ready-to-speak)
    text: Optional[str] = None  # Same as message - included for Twilio compatibility
```

---

## Message Handling Logic

### Priority Order

The backend uses the following priority when building the emergency message:

1. **Frontend's `message` field** (highest priority)
   - Complete, ready-to-speak message with location details
   - Includes: address, MRT station, coordinates
   - Optimized for text-to-speech

2. **Frontend's `text` field** (fallback)
   - Same content as `message` field
   - Used if `message` is not provided

3. **Backend-built message** (fallback)
   - Only used if frontend doesn't provide `message` or `text`
   - Includes timestamp and location info from database

### Implementation Code

```python
# Build the automated message for the phone call
# Priority: Use frontend's ready-to-use message, fallback to building our own
if sos_request.message or sos_request.text:
    # Frontend provides a complete, ready-to-speak message
    # Use it directly - it's already formatted with location details, MRT station, and coordinates
    emergency_message = sos_request.message or sos_request.text
else:
    # Fallback: Build message if frontend doesn't provide one
    message_parts = [
        "Emergency SOS Alert.",
        f"Alert triggered on {time_str}.",
        f"Location: {location_info}.",
    ]
    message_parts.append("This requires immediate attention. Please respond as soon as possible.")
    emergency_message = " ".join(message_parts)
```

---

## Twilio Integration

### TwiML Generation

The backend uses the message directly in Twilio's `<Say>` verb:

```python
# Escape special characters for XML/TwiML
safe_message = emergency_message.replace("&", "and").replace("<", "less than").replace(">", "greater than")

# Make the call with the message
call = client.calls.create(
    twiml=f'<Response><Say voice="alice" language="en-US">{safe_message}</Say><Pause length="2"/><Say voice="alice" language="en-US">Repeating alert details. {safe_message}</Say></Response>',
    to=emergency_number,
    from_=from_number,
    timeout=10
)
```

### Twilio Say Verb Settings

- **Voice**: `alice` (natural-sounding voice)
- **Language**: `en-US`
- **Message**: Used directly from frontend (no additional processing)
- **Repetition**: Message is repeated once for clarity

---

## Message Format Details

### Frontend Message Format

The frontend sends messages in this format:

```
Emergency SOS activated. Location: [address details] near [MRT station] MRT (Lat: X.XXXXXX, Lng: Y.YYYYYY).
```

### Message Components

1. **Address Details**: Street number and area name
   - Example: "123 Seletar" or "Seletar Link, Seletar"

2. **Nearest MRT Station**: Automatically detected and included
   - Example: "near Punggol Coast MRT"

3. **Coordinates**: Always included in format "Lat: X.XXXXXX, Lng: Y.YYYYYY"
   - 6 decimal places for precision

### Example Messages

**Example 1 - Full address with MRT:**
```
Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386).
```

**Example 2 - Road name with MRT:**
```
Emergency SOS activated. Location: Seletar Link, Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386).
```

**Example 3 - Only MRT and coordinates:**
```
Emergency SOS activated. Location: near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386).
```

**Example 4 - Only coordinates (fallback):**
```
Emergency SOS activated. Location: Lat: 1.410576, Lng: 103.893386.
```

**Example 5 - Location unavailable:**
```
Emergency SOS activated. Location unavailable.
```

---

## Important Notes

### 1. Message is Ready-to-Use

- ✅ The `message` field is already formatted and optimized for text-to-speech
- ✅ No additional processing or formatting is needed
- ✅ Use it directly in Twilio's `<Say>` verb

### 2. Always Use Message Field First

- ✅ Prioritize `message` field over `text` field
- ✅ Both contain the same content
- ✅ Use `text` only as fallback if `message` is missing

### 3. Fallback Behavior

- ✅ If neither `message` nor `text` is provided, backend builds its own message
- ✅ Fallback message includes timestamp and location from database
- ✅ Ensures emergency call always has location information

### 4. XML Escaping

- ✅ Special characters are escaped for TwiML compatibility
- ✅ `&` → `and`
- ✅ `<` → `less than`
- ✅ `>` → `greater than`

### 5. Message Length

- ✅ Messages are designed to be concise but informative
- ✅ Typically range from 50-150 characters
- ✅ Optimized for clear speech delivery

---

## Endpoints

### Primary Endpoint

**POST `/api/safety/sos`**

- Accepts the complete request body with all fields
- Uses `message` or `text` field directly for Twilio call
- Returns call status and details

### Fallback Endpoint

**POST `/api/safety/emergency`**

- Alias for `/api/safety/sos`
- Same functionality
- Maintained for backward compatibility

### Orchestrator Endpoint

**POST `/api/orchestrator/message`**

- Also handles emergency intents
- Uses `request.message` if provided
- Falls back to building message from `request.location`

---

## Error Handling

### Missing Message Field

If `message` and `text` are both missing:

```python
# Fallback message is built
emergency_message = "Emergency SOS Alert. Alert triggered on [timestamp]. Location: [location_info]. This requires immediate attention. Please respond as soon as possible."
```

### Invalid Message Format

- Backend accepts any string in `message` field
- No validation is performed (frontend is responsible for formatting)
- Message is used as-is in Twilio call

### Twilio Call Failures

- Errors are caught and logged
- Response includes error details
- Frontend receives status information

---

## Testing

### Test Cases

1. **Full Location Available**
   - Request includes: `message`, `latitude`, `longitude`
   - Expected: Message used directly in Twilio call

2. **Message Only**
   - Request includes: `message` only
   - Expected: Message used directly (coordinates not needed)

3. **Text Field Only**
   - Request includes: `text` only (no `message`)
   - Expected: `text` field used as fallback

4. **No Message Field**
   - Request doesn't include `message` or `text`
   - Expected: Backend builds fallback message

5. **Location Unavailable**
   - Request includes: `message` with "Location unavailable"
   - Expected: Message used as-is (no modification)

### Verification Steps

1. Trigger emergency from frontend (SOS button or voice)
2. Check backend logs to verify message is received
3. Verify Twilio call is made with the message
4. Listen to the call to confirm message is spoken correctly
5. Verify message includes location details (address, MRT, coordinates)

---

## Code Locations

### Safety Routes

**File**: `app/safety/routes.py`

- **Line 120-127**: `SOSRequest` model definition
- **Line 231-242**: Message handling logic
- **Line 278**: XML escaping
- **Line 284**: Twilio call with message

### Orchestrator Routes

**File**: `app/orchestrator/routes.py`

- **Line 625-629**: Emergency message handling in orchestrator
- Uses `request.message` if provided
- Falls back to building message from `request.location`

---

## Summary

- ✅ Backend prioritizes frontend's `message` field
- ✅ Message is used directly in Twilio `<Say>` verb
- ✅ No additional processing or formatting needed
- ✅ Fallback message built if frontend doesn't provide one
- ✅ Special characters are escaped for TwiML compatibility
- ✅ Message includes: address, MRT station, and coordinates
- ✅ Optimized for text-to-speech delivery

---

**Last Updated**: December 2024  
**Status**: Integrated and ready for use

