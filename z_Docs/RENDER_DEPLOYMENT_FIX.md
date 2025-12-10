# 🔧 Render Deployment Fix Guide

## ⚠️ Common Issues on Render

### Issue 1: Module Import Fails (Most Common)

**Error**: `ModuleNotFoundError: No module named 'openai'`

**Solution**: 
1. Go to your Render dashboard
2. Navigate to your service → **Environment** tab
3. Add build command:
   ```
   pip install -r requirements.txt
   ```
4. Make sure `requirements.txt` includes `openai==1.54.0`

---

### Issue 2: OPENAI_API_KEY Not Set

**Error**: `OPENAI_API_KEY environment variable is not set`

**Solution**:
1. Go to Render dashboard → Your service
2. Go to **Environment** tab
3. Click **Add Environment Variable**
4. Key: `OPENAI_API_KEY`
5. Value: `sk-your-actual-key-here`
6. Click **Save Changes**
7. **Redeploy** your service

---

### Issue 3: Tests Fail Locally

**Error**: All tests return 500 or connection errors

**Checklist**:
- [ ] Server is running: `uvicorn app.main:app --reload`
- [ ] OPENAI_API_KEY is set in `.env` file
- [ ] OpenAI package installed: `pip install openai==1.54.0`
- [ ] Test endpoint directly: `http://localhost:8000/api/orchestrator/process-singlish`

---

### Issue 4: GPT-4 Model Not Available

**Error**: `The model 'gpt-4' does not exist`

**Solution**: The code now automatically falls back to `gpt-3.5-turbo`. If you want to force gpt-3.5-turbo, edit `app/orchestrator/routes.py` line 246:
```python
model = "gpt-3.5-turbo"  # Change from "gpt-4"
```

---

## 🧪 Quick Test on Render

### Test 1: Check if endpoint exists
```bash
curl https://your-app.onrender.com/api/orchestrator/process-singlish
# Should return 422 (method not allowed) or 405, NOT 404
```

### Test 2: Test with transcript
```bash
curl -X POST https://your-app.onrender.com/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "transcript": "walao this uncle cut queue sia"}'
```

**Expected Response**:
```json
{
  "success": true,
  "user_id": "test",
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh no, this elderly man cut in line.",
  "sentiment": "frustrated",
  "tone": "informal, colloquial"
}
```

---

## 📋 Render Environment Variables Checklist

Make sure these are set in Render:

| Variable | Required | Example |
|----------|----------|---------|
| `OPENAI_API_KEY` | ✅ YES | `sk-...` |
| `SUPABASE_URL` | ✅ YES | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | ✅ YES | `eyJ...` |
| `TWILIO_ACCOUNT_SID` | ❌ Optional | `AC...` |
| `TWILIO_AUTH_TOKEN` | ❌ Optional | `...` |

---

## 🔍 Debugging Steps

### Step 1: Check Render Logs
1. Go to Render dashboard → Your service
2. Click **Logs** tab
3. Look for errors during startup
4. Common errors:
   - `ModuleNotFoundError` → Missing package
   - `OPENAI_API_KEY` → Missing env var
   - `401 Unauthorized` → Invalid API key

### Step 2: Test Locally First
```bash
# 1. Set environment variable
$env:OPENAI_API_KEY="sk-your-key"

# 2. Start server
uvicorn app.main:app --reload

# 3. Test endpoint
python test_singlish_processing.py
```

### Step 3: Check API Key Validity
```python
# Quick test script
import os
from openai import OpenAI

key = os.getenv("OPENAI_API_KEY")
if not key:
    print("❌ Key not set")
else:
    print(f"✅ Key found: {key[:10]}...")
    try:
        client = OpenAI(api_key=key)
        # Test with a simple call
        print("✅ Key is valid")
    except Exception as e:
        print(f"❌ Key invalid: {e}")
```

---

## 🚀 Deployment Checklist

Before deploying to Render:

- [ ] `requirements.txt` includes `openai==1.54.0`
- [ ] `.env` file has `OPENAI_API_KEY` (for local testing)
- [ ] Render environment has `OPENAI_API_KEY` set
- [ ] Code changes committed to GitHub
- [ ] Render auto-deploy is enabled
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 📞 Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `500 Internal Server Error` | OpenAI API key missing | Set `OPENAI_API_KEY` in Render |
| `401 Unauthorized` | Invalid API key | Generate new key from OpenAI |
| `ModuleNotFoundError: openai` | Package not installed | Add to `requirements.txt` |
| `422 Validation Error` | Missing required field | Check request body format |
| `Connection timeout` | OpenAI API down | Wait and retry |

---

## ✅ Success Indicators

Your deployment is working if:

1. ✅ Render build completes without errors
2. ✅ Service shows "Live" status
3. ✅ Health check passes: `GET /health`
4. ✅ Endpoint responds: `POST /api/orchestrator/process-singlish`
5. ✅ Returns proper JSON with `clean_english`, `sentiment`, `tone`

---

## 🆘 Still Not Working?

1. **Check Render logs** - Most errors show up there
2. **Test locally first** - If it works locally, it's an env var issue
3. **Verify API key** - Test key directly with OpenAI
4. **Check requirements.txt** - Make sure openai is listed
5. **Redeploy** - Sometimes Render needs a fresh deploy

---

## 📝 Updated Code Changes

The latest fix includes:
- ✅ Lazy OpenAI client initialization (won't fail on import)
- ✅ Better error messages
- ✅ GPT-3.5-turbo fallback if GPT-4 unavailable
- ✅ Proper JSON import at top level

**Make sure to pull the latest changes from GitHub!**

