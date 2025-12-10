# Vercel Frontend Troubleshooting Guide

## Issue: Events Not Showing Up on Vercel Frontend

If your Vercel-hosted frontend (from a forked repo) is not showing all events from Supabase, follow these steps:

---

## 🔍 Step 1: Check Frontend API Configuration

### Problem: Frontend pointing to wrong backend URL

**Check your frontend code for the API base URL:**

1. **Find where API calls are made** (usually in a config file or API service):
   ```javascript
   // ❌ WRONG - This won't work on Vercel
   const API_BASE_URL = 'http://localhost:8000';
   
   // ✅ CORRECT - Use your Render backend URL
   const API_BASE_URL = 'https://scbackend-qfh6.onrender.com';
   ```

2. **Common locations to check:**
   - `src/config/api.js` or `src/config/api.ts`
   - `src/services/api.js` or `src/services/api.ts`
   - `src/utils/api.js` or `src/utils/api.ts`
   - `.env.local` or `.env.production` file
   - `next.config.js` (for Next.js apps)

3. **For Next.js apps, check environment variables:**
   ```javascript
   // In your frontend code
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
   ```
   
   **In Vercel Dashboard:**
   - Go to your project → Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://scbackend-qfh6.onrender.com`
   - Redeploy after adding

---

## 🔍 Step 2: Verify Backend is Running

### Test your backend API directly:

1. **Open in browser:**
   ```
   https://scbackend-qfh6.onrender.com/api/events/list
   ```

2. **Should return JSON like:**
   ```json
   {
     "success": true,
     "events": [...],
     "count": 5
   }
   ```

3. **If you get an error:**
   - Backend might be sleeping (Render free tier)
   - Wait 30 seconds and try again
   - Check Render dashboard for deployment status

---

## 🔍 Step 3: Check Backend Environment Variables (Render)

### Problem: Backend using wrong Supabase credentials

**In Render Dashboard:**

1. Go to your backend service → Environment
2. Verify these variables are set:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   ```

3. **Important:** Make sure these match the Supabase project that has your events!

4. **Test the connection:**
   - Visit: `https://scbackend-qfh6.onrender.com/health`
   - Should show: `"database": "connected"`

---

## 🔍 Step 4: Check CORS Configuration

### Problem: CORS blocking requests from Vercel

**Current CORS config allows all origins (`"*"`), but verify:**

1. **Check browser console** for CORS errors:
   ```
   Access to fetch at '...' from origin '...' has been blocked by CORS policy
   ```

2. **If you see CORS errors:**
   - The backend CORS is already configured to allow all origins
   - This shouldn't be the issue, but double-check `app/main.py`

---

## 🔍 Step 5: Check Frontend Network Requests

### Debug what the frontend is actually calling:

1. **Open browser DevTools** (F12)
2. **Go to Network tab**
3. **Reload your Vercel frontend**
4. **Look for API requests:**
   - Should be calling: `https://scbackend-qfh6.onrender.com/api/events/list`
   - NOT: `http://localhost:8000/api/events/list`

5. **Check the response:**
   - Status code should be `200`
   - Response should contain `events` array
   - If status is `404` or `500`, backend has an issue

---

## 🔍 Step 6: Verify Supabase Data

### Make sure events exist in Supabase:

1. **Go to Supabase Dashboard**
2. **Navigate to:** Table Editor → `events` table
3. **Verify events exist:**
   - If table is empty, that's why nothing shows!
   - Create a test event if needed

4. **Check which Supabase project:**
   - Your backend might be connected to a different Supabase project
   - Compare `SUPABASE_URL` in Render with your actual Supabase project URL

---

## 🔍 Step 7: Check Frontend Code Logic

### Problem: Frontend filtering or limiting events

**Check your frontend event fetching code:**

```javascript
// Example - make sure you're not filtering incorrectly
async function fetchEvents() {
  const response = await fetch(`${API_BASE_URL}/api/events/list`);
  const data = await response.json();
  
  // ✅ Should use all events
  return data.events;
  
  // ❌ Don't filter incorrectly
  // return data.events.filter(e => e.date > today); // This might hide events!
}
```

**Common issues:**
- Filtering by date incorrectly
- Limiting results on frontend
- Not handling pagination
- Error handling hiding the issue

---

## 🔍 Step 8: Check Browser Console for Errors

### Look for JavaScript errors:

1. **Open DevTools Console** (F12)
2. **Look for:**
   - Network errors (failed fetch requests)
   - JavaScript errors
   - API response errors

3. **Common errors:**
   ```
   Failed to fetch
   TypeError: Cannot read property 'events' of undefined
   NetworkError when attempting to fetch resource
   ```

---

## ✅ Quick Fix Checklist

- [ ] Frontend API URL points to Render backend (not localhost)
- [ ] Vercel environment variables set correctly
- [ ] Backend is deployed and running on Render
- [ ] Backend environment variables (SUPABASE_URL, SUPABASE_KEY) are set in Render
- [ ] Supabase project has events in the `events` table
- [ ] Backend and frontend use the same Supabase project
- [ ] No CORS errors in browser console
- [ ] Network requests show correct API calls
- [ ] API returns data when tested directly

---

## 🛠️ Step-by-Step Fix

### If events still don't show:

1. **Test backend directly:**
   ```bash
   curl https://scbackend-qfh6.onrender.com/api/events/list
   ```
   - If this works, backend is fine
   - If this fails, fix backend first

2. **Test from frontend code:**
   ```javascript
   // Add this temporarily to your frontend
   console.log('API URL:', process.env.NEXT_PUBLIC_API_URL);
   
   fetch('https://scbackend-qfh6.onrender.com/api/events/list')
     .then(r => r.json())
     .then(data => console.log('Events:', data))
     .catch(err => console.error('Error:', err));
   ```

3. **Check Vercel build logs:**
   - Go to Vercel Dashboard → Deployments
   - Click on latest deployment
   - Check build logs for errors

4. **Check Vercel function logs:**
   - Go to Vercel Dashboard → Functions
   - Look for runtime errors

---

## 📝 Common Solutions

### Solution 1: Update API URL in Frontend

**If using environment variables:**
```bash
# In Vercel Dashboard → Environment Variables
NEXT_PUBLIC_API_URL=https://scbackend-qfh6.onrender.com
```

**If hardcoded in code:**
```javascript
// Find and replace
const API_BASE_URL = 'https://scbackend-qfh6.onrender.com';
```

### Solution 2: Verify Backend Supabase Connection

**In Render Dashboard:**
1. Go to Environment tab
2. Check `SUPABASE_URL` matches your Supabase project
3. Check `SUPABASE_KEY` is the anon/public key (not service role)
4. Redeploy if you changed anything

### Solution 3: Check Supabase Row Level Security (RLS)

**If RLS is enabled:**
1. Go to Supabase Dashboard → Authentication → Policies
2. Make sure `events` table has a policy allowing SELECT
3. Or temporarily disable RLS for testing:
   ```sql
   ALTER TABLE events DISABLE ROW LEVEL SECURITY;
   ```

---

## 🆘 Still Not Working?

If none of the above works:

1. **Share these details:**
   - Browser console errors
   - Network tab screenshot
   - Backend health check response
   - Supabase table data count

2. **Test endpoints manually:**
   - `https://scbackend-qfh6.onrender.com/health`
   - `https://scbackend-qfh6.onrender.com/api/events/list`

3. **Check Render logs:**
   - Go to Render Dashboard → Logs
   - Look for errors when API is called

---

## 📞 Need More Help?

- Check backend logs in Render Dashboard
- Verify Supabase connection in backend health endpoint
- Test API directly with Postman/curl
- Compare working local setup with Vercel deployment

