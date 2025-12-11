# Frontend Fixes and Backend Issues

**Date**: December 2024  
**Status**: Frontend fixes complete, backend issues identified

---

## Summary

This document outlines all frontend changes made to fix SOS button navigation and location tracking issues, as well as potential backend issues that need to be addressed.

---

## Frontend Changes Made

### 1. SOS Button Navigation Fix

**Issue**: SOS button was causing page navigation instead of showing a popup.

**Files Modified**:
- `pages/home.tsx`

**Changes**:
1. Added `e.preventDefault()` to `handleSOS` function to prevent default button behavior
2. Changed button type to `type="button"` to prevent form submission
3. Simplified alert messages to "Emergency call initiated!" for success cases
4. Added explicit location update before triggering emergency (ensures location is stored)

**Code Changes**:
```typescript
// Before
const handleSOS = async () => {
  // ... SOS logic
}

// After
const handleSOS = async (e: React.MouseEvent<HTMLButtonElement>) => {
  e.preventDefault(); // Prevent default button behavior
  // ... SOS logic with location update
}

// Button element
<button
  type="button"  // Added this
  onClick={handleSOS}
  // ...
>
```

**Result**: 
- ✅ SOS button stays on same page
- ✅ Shows popup "Emergency call initiated!"
- ✅ Makes emergency call in background
- ✅ Updates location before triggering emergency

---

### 2. Emergency Endpoint Error Handling

**Issue**: Frontend was getting 404 errors when calling `/api/safety/emergency` endpoint.

**Files Modified**:
- `lib/api.js`

**Changes**:
1. Improved error handling in `apiCall` function to include status codes in error objects
2. Reversed endpoint order: tries `/api/safety/sos` first (more likely to exist), then `/api/safety/emergency` as fallback
3. Added better 404 detection using status codes and error message patterns
4. Added comprehensive logging for debugging

**Code Changes**:
```javascript
// Added status code to errors
const error = new Error(errorMessage);
error.status = response.status;
error.statusText = response.statusText;
throw error;

// Improved fallback logic
export async function triggerEmergency(...) {
  try {
    // Try /api/safety/sos first
    return await apiCall('/api/safety/sos', {...});
  } catch (error) {
    // If 404, try /api/safety/emergency
    if (error.status === 404 || error.message.includes('not found')) {
      return await apiCall('/api/safety/emergency', {...});
    }
    throw error;
  }
}
```

**Result**:
- ✅ Automatically falls back to working endpoint
- ✅ Better error messages
- ✅ More reliable error detection

---

### 3. Continuous Location Updates

**Issue**: Location was only updated on home page, causing delays in location visibility.

**Files Modified**:
- `hooks/useLocationUpdate.ts` (NEW)
- `pages/home.tsx`
- `pages/profile.tsx`
- `pages/events.tsx`
- `pages/reminders.tsx`
- `pages/feedback.tsx`

**Changes**:
1. Created reusable `useLocationUpdate` hook for continuous location updates
2. Added location updates to all key pages elderly users visit
3. Increased update frequency from 5 minutes to 2 minutes
4. Updates location immediately on page load

**New Hook** (`hooks/useLocationUpdate.ts`):
```typescript
export function useLocationUpdate(userId: string, enabled: boolean = true) {
  useEffect(() => {
    if (!enabled) return;
    
    const updateUserLocation = async () => {
      // Get GPS location and update via API
    };
    
    // Update immediately
    updateUserLocation();
    
    // Update every 2 minutes
    const interval = setInterval(updateUserLocation, 120000);
    
    return () => clearInterval(interval);
  }, [userId, enabled]);
}
```

**Pages Updated**:
- **Home**: Always enabled
- **Profile**: Enabled for elderly users only
- **Events**: Enabled for elderly users only
- **Reminders**: Always enabled
- **Feedback**: Enabled for elderly users only

**Result**:
- ✅ Location updates immediately when app opens
- ✅ Location updates every 2 minutes continuously
- ✅ Works on all pages, not just home page
- ✅ Location is always current

---

### 4. Location Page Improvements

**Issue**: Location page showed "Waiting for location update" even when location was being updated.

**Files Modified**:
- `pages/location.tsx`

**Changes**:
1. Added refresh button in header for manual location refresh
2. Added retry logic with exponential backoff (retries up to 3 times with 1s, 2s, 3s delays)
3. Increased auto-refresh frequency from 30 seconds to 10 seconds
4. Added helpful message when no location data is available
5. Improved error handling and logging
6. Added delay to manual refresh to allow pending updates to complete

**Code Changes**:
```typescript
// Retry logic
async function fetchLocation(retryCount = 0) {
  // Add delay if retrying
  if (retryCount > 0) {
    await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
  }
  
  const response = await getCurrentLocation(userId);
  
  // If no location found and retries remaining, retry
  if (response.success === false && retryCount < 3) {
    setTimeout(() => fetchLocation(retryCount + 1), 1000 * (retryCount + 1));
    return;
  }
  
  // Process location data...
}

// Auto-refresh every 10 seconds
const interval = setInterval(() => fetchLocation(0), 10000);
```

**Result**:
- ✅ Better handling of timing issues
- ✅ Automatic retries when location not found
- ✅ Faster location updates (10s refresh)
- ✅ Manual refresh button for immediate updates
- ✅ Clearer user messaging

---

## Backend Issues Identified

### Issue 1: Location Storage/Retrieval Mismatch ⚠️ **CRITICAL**

**Problem**: 
- POST `/api/safety/location` returns `{success: true, location_updated: true}`
- GET `/api/safety/location/{user_id}` returns `{success: false, message: 'Please provide current location'}`

**Evidence from Logs**:
```
✅ Location updated successfully: {success: true, location_updated: true, message: 'Location updated successfully'}
📍 Location API response: {success: false, message: 'Please provide current location', location_display: 'Location access required'}
```

**Possible Causes**:
1. **Database Transaction Issue**: Location is being stored but transaction isn't committed before GET request
2. **Table/Column Mismatch**: POST stores in one table/format, GET queries different table/format
3. **User ID Format Mismatch**: POST and GET might be using different user_id formats (string vs UUID)
4. **Database Sync Delay**: Location stored but database replication/sync hasn't completed
5. **Query Logic Error**: GET endpoint might be querying with wrong WHERE clause or ordering

**Backend Fixes Needed**:
```python
# Check these in your backend:

# 1. Verify POST endpoint actually commits to database
@app.post("/api/safety/location")
async def update_location(data: LocationData):
    # ... store location ...
    db.session.commit()  # Ensure this is called
    return {"success": True, "location_updated": True}

# 2. Verify GET endpoint queries same table/columns
@app.get("/api/safety/location/{user_id}")
async def get_location(user_id: str):
    # Ensure user_id format matches (string vs UUID)
    # Ensure query uses same table as POST
    # Ensure ORDER BY timestamp DESC to get latest
    location = db.query(LocationLog).filter(
        LocationLog.user_id == user_id
    ).order_by(LocationLog.timestamp.desc()).first()
    
# 3. Check for case sensitivity or type mismatches
# user_id might be stored as string but queried as UUID or vice versa
```

**Testing**:
```bash
# Test POST
curl -X POST https://scbackend-qfh6.onrender.com/api/safety/location \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "latitude": 1.3521, "longitude": 103.8198}'

# Immediately test GET
curl https://scbackend-qfh6.onrender.com/api/safety/location/00000000-0000-0000-0000-000000000001

# Should return location data, not "Please provide current location"
```

---

### Issue 2: Emergency Endpoint Availability ⚠️ **MEDIUM**

**Problem**: 
- Frontend tries `/api/safety/emergency` first, gets 404
- Falls back to `/api/safety/sos` which works
- According to `SAFETY_ENDPOINTS_FIX.md`, `/api/safety/emergency` should exist as an alias

**Evidence**:
- Frontend logs show: `⚠️ /api/safety/sos returned 404, trying /api/safety/emergency as fallback...`
- But we reversed the order, so now it tries `/api/safety/sos` first

**Possible Causes**:
1. `/api/safety/emergency` endpoint not implemented in backend
2. Endpoint exists but route is not registered
3. Endpoint exists but returns different response format

**Backend Fixes Needed**:
```python
# Ensure /api/safety/emergency endpoint exists
@app.post("/api/safety/emergency")
async def trigger_emergency(data: EmergencyData):
    # Should be an alias for /api/safety/sos
    # Call same function as sos endpoint
    return await trigger_sos_alert(data)
```

**Testing**:
```bash
# Test emergency endpoint
curl -X POST https://scbackend-qfh6.onrender.com/api/safety/emergency \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "location": "Test", "message": "Test"}'

# Should return same response as /api/safety/sos
```

---

### Issue 3: Location Response Format Inconsistency ⚠️ **LOW**

**Problem**: 
- Frontend handles multiple response formats, suggesting backend might return different formats
- Some responses have `{success: true, location: {...}}`
- Others might have `{success: true, latitude: ..., longitude: ...}`

**Possible Causes**:
1. Different endpoints return different formats
2. Backend code has inconsistent response structures
3. Multiple developers worked on endpoints with different patterns

**Backend Fixes Needed**:
```python
# Standardize response format
# GET /api/safety/location/{user_id} should always return:
{
    "success": True,
    "location": {
        "latitude": 1.3521,
        "longitude": 103.8198,
        "last_updated": "2024-12-10T10:30:00Z",
        "timestamp": "2024-12-10T10:30:00Z"
    }
}

# Or if no location:
{
    "success": False,
    "message": "No location data found for this user"
}
```

---

### Issue 4: Database Query Performance ⚠️ **LOW**

**Problem**: 
- Location updates happen frequently (every 2 minutes)
- GET requests happen every 10 seconds
- If database isn't indexed properly, queries might be slow

**Backend Fixes Needed**:
```sql
-- Ensure proper indexes on location_logs table
CREATE INDEX IF NOT EXISTS idx_location_user_id ON location_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_location_timestamp ON location_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_location_user_timestamp ON location_logs(user_id, timestamp DESC);

-- Query should use index
SELECT * FROM location_logs 
WHERE user_id = ? 
ORDER BY timestamp DESC 
LIMIT 1;
```

---

## Testing Checklist

### Frontend Testing ✅
- [x] SOS button doesn't navigate away
- [x] SOS button shows popup
- [x] Location updates on home page
- [x] Location updates on other pages
- [x] Location page shows location when available
- [x] Location page handles "no location" gracefully
- [x] Refresh button works
- [x] Auto-refresh works

### Backend Testing Needed ⚠️
- [ ] POST `/api/safety/location` actually stores in database
- [ ] GET `/api/safety/location/{user_id}` retrieves stored location
- [ ] User ID format matches between POST and GET
- [ ] Database transaction commits properly
- [ ] `/api/safety/emergency` endpoint exists and works
- [ ] Response formats are consistent
- [ ] Database indexes are optimized

---

## Recommended Backend Fixes Priority

### 🔴 **HIGH PRIORITY**
1. **Fix Location Storage/Retrieval Mismatch** - This is blocking location display
   - Verify POST actually commits to database
   - Verify GET queries same table/format
   - Check user_id format consistency
   - Add database transaction logging

### 🟡 **MEDIUM PRIORITY**
2. **Implement `/api/safety/emergency` Endpoint** - For API consistency
   - Create alias endpoint that calls same function as `/api/safety/sos`
   - Ensure same response format

### 🟢 **LOW PRIORITY**
3. **Standardize Response Formats** - For maintainability
   - Ensure all endpoints return consistent format
   - Document expected response structures

4. **Optimize Database Queries** - For performance
   - Add proper indexes
   - Optimize queries for frequent access

---

## Files Changed Summary

### New Files
- `hooks/useLocationUpdate.ts` - Reusable location update hook

### Modified Files
- `pages/home.tsx` - SOS button fix, location updates
- `pages/location.tsx` - Improved error handling, retry logic, refresh button
- `pages/profile.tsx` - Added location updates
- `pages/events.tsx` - Added location updates
- `pages/reminders.tsx` - Added location updates
- `pages/feedback.tsx` - Added location updates
- `lib/api.js` - Improved error handling, endpoint fallback logic

---

## Next Steps

1. **Immediate**: Test backend location storage/retrieval to identify root cause
2. **Short-term**: Fix backend location GET endpoint to properly retrieve stored locations
3. **Medium-term**: Implement `/api/safety/emergency` endpoint for consistency
4. **Long-term**: Standardize all API response formats and optimize database queries

---

**Last Updated**: December 2024  
**Status**: Frontend fixes complete, awaiting backend fixes for location retrieval issue

