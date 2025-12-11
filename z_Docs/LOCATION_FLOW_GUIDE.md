# Location Flow Guide - Frontend Integration

This document explains how location tracking works in the system, from capture to storage to sharing.

---

## Overview

The location system allows users to:
1. **Capture** their current GPS location
2. **Store** location data in the database
3. **Retrieve** their stored location
4. **Share** location in emergency situations

---

## Location Flow Diagram

```
┌─────────────────┐
│   Frontend      │
│   (Browser)     │
└────────┬────────┘
         │
         │ 1. User grants location permission
         │    navigator.geolocation.getCurrentPosition()
         ▼
┌─────────────────┐
│   GPS/Device    │
│   Coordinates   │
│   (lat, lng)    │
└────────┬────────┘
         │
         │ 2. POST /api/safety/location
         │    { user_id, latitude, longitude, address? }
         ▼
┌─────────────────┐
│   Backend API   │
│   /api/safety   │
└────────┬────────┘
         │
         │ 3. Store in database
         ▼
┌─────────────────┐
│   Supabase      │
│   location_logs │
│   table         │
└────────┬────────┘
         │
         │ 4. GET /api/safety/location/{user_id}
         │    Retrieve latest location
         ▼
┌─────────────────┐
│   Frontend      │
│   Display/Use   │
└─────────────────┘
```

---

## Step 1: Capturing Location (Frontend)

The frontend is responsible for capturing the user's location using the browser's Geolocation API.

### Browser Geolocation API

```javascript
// Request location permission and get coordinates
navigator.geolocation.getCurrentPosition(
  (position) => {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    
    // Send to backend
    updateLocationOnBackend(userId, latitude, longitude);
  },
  (error) => {
    console.error("Location error:", error);
    // Handle error (permission denied, timeout, etc.)
  },
  {
    enableHighAccuracy: true,  // Use GPS if available
    timeout: 10000,            // 10 second timeout
    maximumAge: 0              // Don't use cached location
  }
);
```

### React Example

```javascript
import { useEffect, useState } from 'react';

function LocationTracker({ userId }) {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        setLocation({ latitude, longitude });
        
        // Update location on backend
        try {
          const response = await fetch('/api/safety/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              latitude: latitude,
              longitude: longitude
            })
          });
          
          const data = await response.json();
          if (data.success) {
            console.log('Location updated successfully');
          }
        } catch (err) {
          console.error('Failed to update location:', err);
        }
      },
      (err) => {
        setError(`Location error: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [userId]);

  return { location, error };
}
```

---

## Step 2: Sending Location to Backend

### Endpoint: `POST /api/safety/location`

**Purpose**: Store user's current location in the database

**Request Format**:
```json
{
  "user_id": "string (required)",
  "latitude": "number (required)",
  "longitude": "number (required)",
  "address": "string (optional)"
}
```

**Example Request**:
```javascript
const response = await fetch('https://your-backend-url.com/api/safety/location', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user-123',
    latitude: 1.3521,
    longitude: 103.8198,
    address: 'Singapore'  // Optional: human-readable address
  })
});

const data = await response.json();
```

**Success Response** (200):
```json
{
  "success": true,
  "location_updated": true,
  "message": "Location updated successfully"
}
```

**Error Response** (400/500):
```json
{
  "detail": "Error message here"
}
```

---

## Step 3: Location Storage in Database

The backend stores location data in the Supabase `location_logs` table:

**Table Structure**:
```sql
location_logs:
  - id (auto-generated)
  - user_id (string)
  - latitude (float)
  - longitude (float)
  - address (string, optional)
  - timestamp (datetime, auto-generated)
```

**Important Notes**:
- Each location update creates a **new entry** in the table (history is preserved)
- The **most recent entry** is considered the "current location"
- Timestamp is automatically set to UTC when stored
- Address field is optional - can be provided by frontend or left null

---

## Step 4: Retrieving Location from Backend

### Endpoint: `GET /api/safety/location/{user_id}`

**Purpose**: Get the most recent stored location for a user

**Request**:
```javascript
const response = await fetch(`https://your-backend-url.com/api/safety/location/${userId}`);
const data = await response.json();
```

**Success Response** (200):
```json
{
  "success": true,
  "location": {
    "latitude": 1.3521,
    "longitude": 103.8198,
    "last_updated": "2024-12-10T10:30:00Z"
  }
}
```

**Error Response** (404):
```json
{
  "detail": "No location data found for this user"
}
```

### Alternative: Query Parameter Format

You can also use query parameters:
```javascript
const response = await fetch(`/api/safety/location?user_id=${userId}`);
```

---

## Step 5: Using Location in Emergency Situations

When triggering an emergency/SOS alert, location can be included:

### Endpoint: `POST /api/safety/emergency`

**Request Format**:
```json
{
  "user_id": "string (required)",
  "location": "string (optional - human-readable like 'Singapore' or '123 Main St')",
  "message": "string (optional)"
}
```

**Example - Include Current Location**:
```javascript
// First, get current coordinates
navigator.geolocation.getCurrentPosition(async (position) => {
  const { latitude, longitude } = position.coords;
  
  // Optionally, convert to human-readable address (frontend can do this)
  const address = await reverseGeocode(latitude, longitude);
  
  // Trigger emergency with location
  const response = await fetch('/api/safety/emergency', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      location: address || `${latitude}, ${longitude}`,
      message: 'Emergency situation!'
    })
  });
});
```

**Note**: The `location` field in emergency requests is a **human-readable string** (like "Singapore" or "123 Main Street"), not coordinates. This is used for voice alerts via Twilio.

---

## Best Practices for Frontend

### 1. Periodic Location Updates

Update location periodically to keep it current:

```javascript
// Update location every 5 minutes
useEffect(() => {
  const interval = setInterval(() => {
    navigator.geolocation.getCurrentPosition((position) => {
      updateLocationOnBackend(userId, position.coords.latitude, position.coords.longitude);
    });
  }, 5 * 60 * 1000); // 5 minutes

  return () => clearInterval(interval);
}, [userId]);
```

### 2. Handle Permissions Gracefully

```javascript
if (!navigator.geolocation) {
  // Browser doesn't support geolocation
  showMessage("Your browser doesn't support location services");
  return;
}

navigator.geolocation.getCurrentPosition(
  successCallback,
  (error) => {
    switch(error.code) {
      case error.PERMISSION_DENIED:
        showMessage("Location permission denied. Please enable it in browser settings.");
        break;
      case error.POSITION_UNAVAILABLE:
        showMessage("Location information unavailable.");
        break;
      case error.TIMEOUT:
        showMessage("Location request timed out.");
        break;
    }
  }
);
```

### 3. Error Handling

```javascript
async function updateLocation(userId, latitude, longitude) {
  try {
    const response = await fetch('/api/safety/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        latitude: latitude,
        longitude: longitude
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update location');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Location update failed:', error);
    // Show user-friendly error message
    showErrorMessage('Unable to update location. Please try again.');
    throw error;
  }
}
```

### 4. Optional: Reverse Geocoding on Frontend

If you want to convert coordinates to addresses on the frontend:

```javascript
async function reverseGeocode(latitude, longitude) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`,
      {
        headers: {
          'User-Agent': 'YourAppName/1.0' // Required by Nominatim
        }
      }
    );
    const data = await response.json();
    return data.display_name || data.address?.road || 'Unknown location';
  } catch (error) {
    console.error('Reverse geocoding failed:', error);
    return null;
  }
}
```

---

## Location Sharing Scenarios

### Scenario 1: User Updates Their Location
1. User opens app
2. Frontend requests location permission
3. GPS coordinates captured
4. Coordinates sent to `POST /api/safety/location`
5. Stored in database

### Scenario 2: Viewing Current Location
1. User opens location screen
2. Frontend calls `GET /api/safety/location/{user_id}`
3. Backend returns latest stored location
4. Frontend displays on map

### Scenario 3: Emergency with Location
1. User triggers emergency button
2. Frontend captures current GPS location
3. Frontend calls `POST /api/safety/emergency` with location string
4. Backend includes location in emergency call/message
5. Caregivers/emergency services receive location info

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/safety/location` | Store/update user location |
| GET | `/api/safety/location/{user_id}` | Retrieve user's latest location |
| POST | `/api/safety/emergency` | Trigger emergency with optional location |

---

## Database Schema

**Table: `location_logs`**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| user_id | String | User identifier |
| latitude | Float | GPS latitude coordinate |
| longitude | Float | GPS longitude coordinate |
| address | String (optional) | Human-readable address |
| timestamp | DateTime | When location was recorded (UTC) |

---

## Important Notes

1. **Location History**: All location updates are stored, creating a history. To get the current location, always fetch the most recent entry.

2. **Coordinates Format**: 
   - Latitude: -90 to 90 (North/South)
   - Longitude: -180 to 180 (East/West)
   - Singapore is approximately: lat 1.35, lng 103.82

3. **Permissions**: Frontend must handle location permissions. Users may deny access, which should be handled gracefully.

4. **Privacy**: Location data is sensitive. Ensure proper security measures are in place (authentication, authorization).

5. **Battery Considerations**: Frequent location updates can drain device battery. Consider updating location:
   - When app opens
   - When user explicitly requests
   - Periodically (e.g., every 5-10 minutes)
   - Before emergency situations

---

## Testing Checklist

- [ ] Location permission request works
- [ ] Location capture works (GPS coordinates obtained)
- [ ] POST `/api/safety/location` successfully stores location
- [ ] GET `/api/safety/location/{user_id}` retrieves stored location
- [ ] Error handling works (permission denied, network errors)
- [ ] Location updates periodically (if implemented)
- [ ] Location included in emergency alerts
- [ ] Works on mobile devices (iOS/Android browsers)
- [ ] Works when location services are disabled
- [ ] Handles timeouts gracefully

---

## Support & Troubleshooting

### Common Issues

1. **"Location permission denied"**
   - User must grant location permission in browser settings
   - Some browsers require HTTPS for geolocation API

2. **"No location data found"**
   - User hasn't updated their location yet
   - Call `POST /api/safety/location` first to store location

3. **Location not updating**
   - Check network connectivity
   - Verify backend is running
   - Check browser console for errors

4. **Inaccurate coordinates**
   - Enable high accuracy mode: `enableHighAccuracy: true`
   - Wait longer for GPS fix (may take 10-30 seconds)
   - Ensure device has GPS signal (not just WiFi/cell tower)

---

**Last Updated**: December 2024
**Backend API Version**: 2.0.0

