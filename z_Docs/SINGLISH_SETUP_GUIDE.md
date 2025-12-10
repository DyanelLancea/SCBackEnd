# Singlish Orchestrator Setup Guide

## ✅ What Has Been Implemented

Your backend now has a complete **Singlish Processing Orchestrator** that can:
- ✅ Accept audio (base64) or text transcript input
- ✅ Process audio with OpenAI Whisper STT
- ✅ Translate Singlish → Clean English using GPT-4
- ✅ Analyze sentiment (happy, frustrated, angry, etc.)
- ✅ Detect tone (informal, polite, urgent, etc.)
- ✅ Return structured JSON response

---

## 🚀 What YOU Need to Do

### Step 1: Get OpenAI API Key

1. Go to: **https://platform.openai.com/api-keys**
2. Sign up or log in
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-...`)
5. **IMPORTANT**: Save it somewhere safe - you can't see it again!

**Cost Estimate:**
- Whisper STT: ~$0.006 per minute of audio
- GPT-4: ~$0.03 per request (for short Singlish translations)
- Total: ~$0.04 per audio request, ~$0.03 per text request

---

### Step 2: Install Dependencies

Open your terminal in the project directory:

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install new OpenAI package
pip install openai==1.54.0

# Or reinstall everything
pip install -r requirements.txt
```

---

### Step 3: Set Up Environment Variable

#### Option A: Using .env file (Recommended)

1. Create a `.env` file in your project root (if it doesn't exist)
2. Add this line:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

3. Make sure `.env` is in your `.gitignore` (to keep key secret)

#### Option B: Using Windows Environment Variables

1. Search for "Environment Variables" in Windows
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: `OPENAI_API_KEY`
6. Variable value: `sk-your-actual-api-key-here`
7. Click OK

**Restart your terminal after setting environment variables!**

---

### Step 4: Verify OpenAI Key is Loaded

Create a quick test file `test_openai_key.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
else:
    print("❌ OpenAI API key NOT found!")
    print("Make sure you have OPENAI_API_KEY in your .env file")
```

Run it:
```bash
python test_openai_key.py
```

---

### Step 5: Start Your Backend Server

```bash
# Make sure you're in the project directory
cd C:\Users\Lenovo\GitHub\SCBackEnd

# Activate venv
.\venv\Scripts\activate

# Start server
uvicorn app.main:app --reload
```

You should see:
```
🚀 Starting SC Backend API...
✅ All systems ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 6: Test the New Endpoint

Open a **new terminal** (keep the server running in the first one):

```bash
# Activate venv
.\venv\Scripts\activate

# Run test suite
python test_singlish_processing.py
```

**Expected Output:**
```
✅ Server is running!

🧪 TEST 1: Basic Singlish Text Translation
Input: 'walao this uncle cut queue sia'

✅ Test Results:
   Original: walao this uncle cut queue sia
   English:  Oh no, this elderly man cut in line.
   Sentiment: frustrated
   Tone: informal, colloquial

...

📊 TEST SUMMARY
✅ PASS - Test 1: Basic Singlish Translation
✅ PASS - Test 2: Complex Mixed Languages
...
Results: 8/8 tests passed
🎉 All tests passed!
```

---

## 📡 API Endpoint Details

### Endpoint
```
POST http://localhost:8000/api/orchestrator/process-singlish
```

### Request Body (JSON)

**Option 1: Text Input**
```json
{
  "user_id": "user_123",
  "transcript": "walao this uncle cut queue sia"
}
```

**Option 2: Audio Input**
```json
{
  "user_id": "user_123",
  "audio": "base64_encoded_audio_string_here"
}
```

### Response (JSON)

```json
{
  "success": true,
  "user_id": "user_123",
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh no, this elderly man cut in line.",
  "sentiment": "frustrated",
  "tone": "informal, colloquial"
}
```

### Error Response

```json
{
  "detail": "Either 'audio' or 'transcript' must be provided"
}
```

---

## 🧪 Test with Postman or cURL

### Using cURL (Text Input):

```bash
curl -X POST http://localhost:8000/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"test_user\", \"transcript\": \"wah shiok ah! finally can makan\"}"
```

### Using Postman:

1. **Method**: POST
2. **URL**: `http://localhost:8000/api/orchestrator/process-singlish`
3. **Headers**: `Content-Type: application/json`
4. **Body** (raw JSON):
   ```json
   {
     "user_id": "test_123",
     "transcript": "aiyo why like that one"
   }
   ```
5. Click **Send**

---

## 🎨 Frontend Integration

Your frontend needs to send requests to this endpoint. See the detailed guide:

📄 **`z_Docs/FRONTEND_SINGLISH_ORCHESTRATOR_GUIDE.md`**

Quick example:
```javascript
const response = await fetch('http://localhost:8000/api/orchestrator/process-singlish', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    transcript: 'walao this uncle cut queue sia'
  })
});

const data = await response.json();
console.log(data.clean_english); // "Oh no, this elderly man cut in line."
```

---

## 📝 Example Test Cases

Test these Singlish phrases:

| Singlish | Expected Sentiment | Expected Tone |
|----------|-------------------|---------------|
| `walao this uncle cut queue sia` | frustrated | informal |
| `wah shiok ah! finally can makan` | happy | excited |
| `siao liao! the bus broke down again` | angry | frustrated |
| `aiyah boh bian lah, just tahan` | resigned | accepting |
| `excuse me ah, can help me check?` | neutral | polite |

---

## 🔧 Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:**
1. Check `.env` file exists with `OPENAI_API_KEY=sk-...`
2. Restart your terminal/IDE after setting env vars
3. Make sure `.env` is in the project root directory
4. Try: `python -c "import os; print(os.getenv('OPENAI_API_KEY'))"`

### Issue: "401 Unauthorized" from OpenAI

**Solution:**
- Your API key is invalid or expired
- Generate a new key from https://platform.openai.com/api-keys
- Make sure there are no extra spaces in the key

### Issue: "429 Rate limit exceeded"

**Solution:**
- You've hit OpenAI's rate limit (free tier: 3 requests/minute)
- Wait a minute and try again
- Upgrade to paid plan for higher limits

### Issue: "Audio processing failed"

**Solution:**
- Make sure audio is base64 encoded properly
- Audio should be in webm, mp3, or wav format
- Maximum file size: 25MB
- Check that the base64 string doesn't include the data URI prefix

### Issue: Tests fail with "Connection refused"

**Solution:**
- Make sure the server is running: `uvicorn app.main:app --reload`
- Check the server is on http://localhost:8000
- Check for port conflicts (kill other processes using port 8000)

---

## 📊 Monitoring API Usage

Track your OpenAI usage:
1. Go to: https://platform.openai.com/usage
2. View costs by day
3. Set usage limits to avoid surprises

**Tip**: Start with a low usage limit ($5-10) while testing!

---

## 🔐 Security Notes

**NEVER commit your API key to Git!**

✅ **DO:**
- Store in `.env` file
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate keys periodically

❌ **DON'T:**
- Hardcode in source code
- Share in screenshots
- Post in public repos
- Share the key with others

---

## 🎯 Next Steps

1. ✅ Set up OpenAI API key
2. ✅ Install dependencies
3. ✅ Test the endpoint
4. ⏳ Integrate with frontend
5. ⏳ Test with real audio from browser
6. ⏳ Deploy to production

---

## 📚 Files Modified/Created

- ✅ `requirements.txt` - Added OpenAI package
- ✅ `app/orchestrator/routes.py` - Added `/process-singlish` endpoint
- ✅ `test_singlish_processing.py` - Comprehensive test suite
- ✅ `env_template.txt` - Added OpenAI key requirement
- ✅ `z_Docs/SINGLISH_SETUP_GUIDE.md` - This guide
- ✅ `z_Docs/FRONTEND_SINGLISH_ORCHESTRATOR_GUIDE.md` - Frontend guide

---

## 🆘 Need Help?

If something isn't working:
1. Check this guide again carefully
2. Run the test suite: `python test_singlish_processing.py`
3. Check server logs for errors
4. Verify OpenAI API key is valid
5. Test endpoint with Postman first before frontend integration

**The backend is ready - just follow these steps to get it working!** 🚀

