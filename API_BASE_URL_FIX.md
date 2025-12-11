# API_BASE_URL Configuration Fix

## Problem

When testing the orchestrator endpoints, you're seeing this error:

```
Connection error: Could not reach backend API. Please ensure API_BASE_URL is set to your backend's public URL (e.g., https://your-backend.onrender.com). Error: All connection attempts failed
```

## Root Cause

The orchestrator makes **internal API calls** to other endpoints (like `/api/events/list`) to:
1. Get available events for context during intent detection
2. Register users for events
3. Get event details
4. Unregister users from events

These internal calls need to know the **base URL** of your backend. If `API_BASE_URL` is not set, the orchestrator can't make these calls.

## Solution

### For Production (Render.com)

Set the `API_BASE_URL` environment variable in your Render.com service:

1. Go to your Render.com dashboard
2. Select your backend service
3. Go to **Environment** tab
4. Add a new environment variable:
   ```
   API_BASE_URL=https://scbackend-qfh6.onrender.com
   ```
   **Important**: Do NOT include `/api` in the URL - just the base URL!

5. Save and redeploy

### For Local Development

If running locally, `API_BASE_URL` is optional. The code defaults to `http://localhost:8000`.

However, if you want to test against production from your local machine, set:
```bash
export API_BASE_URL=https://scbackend-qfh6.onrender.com
```

Or in your `.env` file:
```
API_BASE_URL=https://scbackend-qfh6.onrender.com
```

## How It Works

The `get_api_base_url()` function tries to auto-detect the URL in this order:

1. **Explicit `API_BASE_URL`** environment variable (highest priority)
2. **`RENDER_SERVICE_URL`** (Render.com internal service URL)
3. **`RENDER_EXTERNAL_URL`** (Render.com external/public URL) - **NEW**
4. **`VERCEL_URL`** (for Vercel deployments)
5. **Production check**: If in production but no URL found, raises error
6. **Default**: `http://localhost:8000` (for local development)

## Verification

After setting `API_BASE_URL`, test with:

```bash
curl -X POST https://scbackend-qfh6.onrender.com/api/orchestrator/voice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "transcript": "I want to book the workout event"
  }'
```

You should see:
- ✅ Intent detected correctly
- ✅ Event matching works
- ✅ Action executed successfully
- ✅ No connection errors

## About `register_event` vs `book_event`

**Note**: The intent might be detected as `register_event` instead of `book_event`, but this is **not a problem**. The code treats both the same:

```python
elif intent in ["book_event", "register_event"]:
    # Both intents are handled identically
```

Both mean "user wants to register/book for an event" and are processed the same way.

## Troubleshooting

### Issue: Still getting connection errors after setting API_BASE_URL

**Check**:
1. Did you include `/api` in the URL? **Remove it!**
   - ❌ Wrong: `https://scbackend-qfh6.onrender.com/api`
   - ✅ Correct: `https://scbackend-qfh6.onrender.com`

2. Did you redeploy after setting the environment variable?

3. Check Render.com logs to see what URL is being used:
   ```python
   # Add temporary logging in get_api_base_url():
   print(f"DEBUG: API_BASE_URL = {api_url}")
   ```

### Issue: Works locally but not in production

**Cause**: Local development defaults to `localhost:8000`, but production needs explicit URL.

**Solution**: Set `API_BASE_URL` in production environment variables.

### Issue: Internal calls work but external calls fail

**Check**: Make sure your backend is publicly accessible and not behind a firewall.

## Code Changes Made

Updated `get_api_base_url()` to:
1. Check `RENDER_EXTERNAL_URL` (new)
2. Better production detection
3. Clearer error messages

## Related Files

- `app/orchestrator/routes.py` - Contains `get_api_base_url()` function
- `env_template.txt` - Template for environment variables
- `test_singlish_intents.py` - Test script that calls the API

