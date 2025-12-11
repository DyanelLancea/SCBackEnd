# Twilio Setup for Render Deployment

This guide explains how to configure Twilio for SOS emergency calls in your Render deployment.

## 🔍 Problem

If SOS calls are not working, the diagnostic shows:
```
❌ SOS call was NOT successful
   Alert Status: Emergency number not configured. Please set SOS_EMERGENCY_NUMBER in your .env file.
```

This means **Twilio environment variables are missing in your Render deployment**.

## ✅ Solution: Add Twilio Environment Variables in Render

### Step 1: Get Your Twilio Credentials

1. Go to [Twilio Console](https://console.twilio.com/)
2. Sign in to your account
3. Find these values on your dashboard:

   - **Account SID**: Found on the main dashboard (starts with `AC...`)
   - **Auth Token**: Click "Show" next to Auth Token (starts with letters/numbers)
   - **Phone Number**: Go to **Phone Numbers** → **Manage** → **Active numbers** (format: `+1...` or `+65...`)
   - **Emergency Number**: The phone number to call during SOS (e.g., `+6598631975`)

### Step 2: Add Environment Variables in Render

1. **Go to Render Dashboard**:
   - Navigate to [Render Dashboard](https://dashboard.render.com/)
   - Click on your backend service (e.g., `sc-backend`)

2. **Open Environment Tab**:
   - Click **"Environment"** in the left sidebar
   - You'll see a list of existing environment variables

3. **Add Twilio Variables**:
   Click **"Add Environment Variable"** for each of these:

   | Key | Value | Example |
   |-----|-------|---------|
   | `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
   | `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
   | `TWILIO_PHONE_NUMBER` | Your Twilio phone number | `+1XXXXXXXXXX` |
   | `SOS_EMERGENCY_NUMBER` | Phone number to call during SOS | `+65XXXXXXXX` |

4. **Save Changes**:
   - After adding all 4 variables, click **"Save Changes"**
   - Render will automatically redeploy your service (takes 2-5 minutes)

### Step 3: Verify Configuration

After deployment completes, test the SOS endpoint:

```bash
# Test locally (if you have the diagnostic script)
python test_sos_call_diagnosis.py

# Or test via API
curl -X POST https://your-backend.onrender.com/api/safety/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "location": "Test Location",
    "message": "Test SOS"
  }'
```

**Expected Response** (if configured correctly):
```json
{
  "success": true,
  "call_successful": true,
  "call_sid": "CA1234567890abcdef...",
  "alert_status": "Emergency call successfully initiated to +6598631975. Call SID: CA..."
}
```

## 🔧 Troubleshooting

### Issue: "Emergency number not configured"

**Cause**: `SOS_EMERGENCY_NUMBER` is not set in Render.

**Fix**:
1. Go to Render → Your Service → Environment
2. Add `SOS_EMERGENCY_NUMBER` with your emergency phone number
3. Save and wait for redeploy

### Issue: "Twilio phone number not configured"

**Cause**: `TWILIO_PHONE_NUMBER` is not set in Render.

**Fix**:
1. Go to Render → Your Service → Environment
2. Add `TWILIO_PHONE_NUMBER` with your Twilio phone number (from Twilio Console)
3. Save and wait for redeploy

### Issue: "Twilio not configured - Missing Account SID or Auth Token"

**Cause**: `TWILIO_ACCOUNT_SID` or `TWILIO_AUTH_TOKEN` is missing.

**Fix**:
1. Go to Render → Your Service → Environment
2. Add both `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
3. Get these from [Twilio Console](https://console.twilio.com/)
4. Save and wait for redeploy

### Issue: "The phone number is not verified in your Twilio account"

**Cause**: The phone number you're using as `TWILIO_PHONE_NUMBER` is not verified in Twilio.

**Fix**:
1. Go to [Twilio Console → Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Verify your phone number, OR
3. Use a Twilio phone number you own (buy one from Twilio)

### Issue: "International calling not enabled"

**Cause**: Your Twilio account doesn't have permission to call the emergency number (e.g., Singapore number `+65...`).

**Fix**:
1. Go to [Twilio Geo Permissions](https://www.twilio.com/console/voice/calls/geo-permissions/low-risk)
2. Enable calling to the country of your emergency number (e.g., Singapore)
3. Wait a few minutes for changes to propagate

### Issue: "Invalid phone number format"

**Cause**: The phone number format is incorrect.

**Fix**:
- Use E.164 format: `+[country code][number]`
- Examples:
  - Singapore: `+6598631975`
  - USA: `+15551234567`
  - No spaces, dashes, or parentheses

## 📝 Environment Variables Checklist

Before testing SOS calls, verify all these are set in Render:

- [ ] `TWILIO_ACCOUNT_SID` (starts with `AC...`)
- [ ] `TWILIO_AUTH_TOKEN` (long alphanumeric string)
- [ ] `TWILIO_PHONE_NUMBER` (your Twilio number, e.g., `+13099280903`)
- [ ] `SOS_EMERGENCY_NUMBER` (number to call during SOS, e.g., `+6598631975`)

## 🧪 Testing

### Test 1: Direct SOS Endpoint

```bash
curl -X POST https://your-backend.onrender.com/api/safety/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "location": "Test Location",
    "message": "Test SOS call"
  }'
```

### Test 2: Voice Endpoint (Triggers SOS)

```bash
curl -X POST https://your-backend.onrender.com/api/orchestrator/voice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "transcript": "Help me, I need emergency assistance",
    "location": "Test Location"
  }'
```

### Test 3: Using Diagnostic Script

```bash
# Run locally (tests production server)
python test_sos_call_diagnosis.py
```

## 🔐 Security Notes

- **Never commit** Twilio credentials to GitHub
- **Always use** Render's Environment Variables (not `.env` files in production)
- **Rotate** Auth Tokens periodically for security
- **Use** Twilio's test credentials for development/testing

## 📚 Additional Resources

- [Twilio Console](https://console.twilio.com/)
- [Twilio Phone Numbers Guide](https://www.twilio.com/docs/phone-numbers)
- [Twilio Geo Permissions](https://www.twilio.com/console/voice/calls/geo-permissions/low-risk)
- [Render Environment Variables](https://render.com/docs/environment-variables)

## ✅ Success Indicators

When everything is configured correctly:

1. ✅ SOS endpoint returns `"call_successful": true`
2. ✅ `call_sid` is present in the response
3. ✅ Phone call is actually made to the emergency number
4. ✅ Voice endpoint successfully triggers SOS when user says "help" or "emergency"

---

**Last Updated**: December 2025

