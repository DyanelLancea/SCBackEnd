# Fix: "All connection attempts failed" Error

## Problem
When using the orchestrator endpoints (like `/api/orchestrator/message`), you get:
```
Error processing your request: All connection attempts failed
```

## Root Cause
The orchestrator makes internal HTTP requests to other API endpoints (like `/api/events/list`). It needs to know the backend's public URL, but `API_BASE_URL` is not set in your Render environment variables.

## Solution

### Step 1: Get Your Render Backend URL
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your backend service
3. Copy the service URL (e.g., `https://scbackend-qfh6.onrender.com`)

### Step 2: Set Environment Variable in Render
1. In Render Dashboard, go to your backend service
2. Click on **Environment** tab
3. Click **Add Environment Variable**
4. Add:
   - **Key**: `API_BASE_URL`
   - **Value**: Your Render backend URL (e.g., `https://scbackend-qfh6.onrender.com`)
   - **Important**: Do NOT include a trailing slash
5. Click **Save Changes**

### Step 3: Redeploy
1. Render will automatically redeploy when you save environment variables
2. Or manually trigger a redeploy from the Render dashboard

### Step 4: Test
After redeploy, test the endpoint:
```bash
curl https://your-backend.onrender.com/api/orchestrator/message \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "show me events"}'
```

## Alternative: Direct Event Endpoint

If you just want to get events (not through orchestrator), use the direct endpoint:
```bash
GET https://your-backend.onrender.com/api/events/list
```

This doesn't require `API_BASE_URL` because it queries Supabase directly.

## Why This Happens

The orchestrator is designed to:
1. Detect user intent (using AI)
2. Automatically execute actions (like booking events, triggering SOS)
3. Make internal API calls to other modules

For step 3, it needs to know where to call. In production, it can't use `localhost:8000`, so it needs the public URL.

## Auto-Detection

The code now tries to auto-detect the URL from:
1. `API_BASE_URL` (explicit - recommended)
2. `RENDER_SERVICE_URL` (if on Render)
3. `VERCEL_URL` (if on Vercel)
4. Falls back to `localhost:8000` for development

But **explicitly setting `API_BASE_URL` is the most reliable**.

## Verification

After setting the variable, check the logs:
```bash
# Should see successful connections, not "connection attempts failed"
```

Test with:
```bash
# Should return events successfully
curl https://your-backend.onrender.com/api/events/list
```

