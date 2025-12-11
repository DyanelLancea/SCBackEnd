# Testing Singlish Intent Detection

## Quick Start

### 1. **Prerequisites**

Make sure you have:
- ✅ Server running: `uvicorn app.main:app --reload`
- ✅ `GROQ_API_KEY` set in `.env` (for intent detection)
- ✅ `OPENAI_API_KEY` set in `.env` (for Singlish translation)
- ✅ Events created in your database (at least 2-3 events for testing)

### 2. **Run the Test Script**

```bash
# Uses production API by default: https://scbackend-qfh6.onrender.com
python test_singlish_intents.py

# Or use localhost instead:
export API_BASE_URL=http://localhost:8000/api
python test_singlish_intents.py
```

## What the Test Script Does

The test script verifies all 4 improved intents work correctly with Singlish:

### ✅ **Test 1: Book a Specific Event**
- Tests that you can book a **specific** event (not just the latest)
- Uses Singlish like: `"eh, I want join pickleball leh"`
- Verifies the correct event is booked

### ✅ **Test 2: Unregister from Event**
- Tests canceling/unregistering from a specific event
- Uses Singlish like: `"eh cancel my yoga registration leh"`
- Verifies the action is executed

### ✅ **Test 3: Get Event Details**
- Tests getting details about a specific event
- Uses Singlish like: `"eh tell me about workout leh"`
- Verifies event details are returned

### ✅ **Test 4: General Questions**
- Tests answering general questions
- Uses Singlish like: `"eh what can this app do ah?"`
- Verifies helpful answers are provided

### ✅ **Test 5: Specific Event Matching (Critical)**
- **Most Important Test**: Verifies it books the **correct** event, not just the latest
- Tests with the **second** event in the list
- Verifies the event ID matches exactly

## Test Flow

Each test follows this flow:

```
1. Singlish Transcript
   ↓
2. /api/orchestrator/process-singlish
   → Translates to English
   ↓
3. /api/orchestrator/voice
   → Detects intent (GROQ)
   → Executes action
   ↓
4. Verify Results
```

## Expected Output

### Successful Test:
```
================================================================================
  Testing: "eh, I want join pickleball leh"
================================================================================

🔤 Step 1: Processing Singlish → English
   Input: "eh, I want join pickleball leh"
   ✅ Translated: "I would like to join the pickleball event"

🎯 Step 2: Intent Detection & Action Execution
   ✅ Intent: book_event
   💬 Message: Successfully registered you for 'Pickleball Tournament'!
   ⚡ Action Executed: True

✅ SUCCESS: Correctly detected intent 'book_event'
✅ VERIFIED: Booked correct event 'Pickleball Tournament'
```

### Failed Test:
```
❌ FAILED: Could not translate Singlish
   or
⚠️  WARNING: Expected 'book_event', got 'general'
```

## Manual Testing

You can also test manually using curl or Postman:

### 1. Process Singlish
```bash
# Production API
curl -X POST https://scbackend-qfh6.onrender.com/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "transcript": "eh I want join pickleball leh"
  }'

# Or localhost
curl -X POST http://localhost:8000/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "transcript": "eh I want join pickleball leh"
  }'
```

### 2. Send to Voice Endpoint
```bash
# Production API
curl -X POST https://scbackend-qfh6.onrender.com/api/orchestrator/voice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "transcript": "I would like to join the pickleball event"
  }'

# Or localhost
curl -X POST http://localhost:8000/api/orchestrator/voice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "transcript": "I would like to join the pickleball event"
  }'
```

## Troubleshooting

### Issue: "Server not accessible"
**Solution**: 
- For production: Check that https://scbackend-qfh6.onrender.com is running
- For localhost: Start the server first
```bash
uvicorn app.main:app --reload
```

### Issue: "No events available"
**Solution**: Create events first
```bash
# Production API
curl -X POST https://scbackend-qfh6.onrender.com/api/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pickleball Tournament",
    "date": "2024-12-20",
    "time": "10:00:00",
    "location": "Community Center"
  }'

# Or localhost
curl -X POST http://localhost:8000/api/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pickleball Tournament",
    "date": "2024-12-20",
    "time": "10:00:00",
    "location": "Community Center"
  }'
```

### Issue: "GROQ_API_KEY not found"
**Solution**: Add to `.env` file
```env
GROQ_API_KEY=your-groq-api-key-here
```

### Issue: Intent detection falls back to keywords
**Check**:
1. GROQ_API_KEY is set correctly
2. API key is valid
3. Check server logs for errors

### Issue: Wrong event booked
**This is the critical test!** If Test 5 fails:
- Check that `find_event_by_name_or_id()` is working
- Verify event names are being extracted correctly
- Check server logs for matching logic

## Test Coverage

| Intent | Test Cases | Status |
|--------|-----------|--------|
| `book_event` | 3 variations | ✅ |
| `cancel_event` | 1 test | ✅ |
| `get_event` | 1 test | ✅ |
| `general` | 3 questions | ✅ |
| **Specific Matching** | **Critical test** | ✅ |

## Success Criteria

✅ **All tests should pass if:**
1. Singlish translation works
2. Intent detection works (GROQ)
3. Event matching finds the correct event
4. Actions are executed successfully
5. Specific events are matched (not just latest)

## Next Steps

After running tests:
1. Review any failed tests
2. Check server logs for detailed errors
3. Verify your events database has test data
4. Ensure API keys are valid
5. Test with real voice recordings (frontend integration)

---

**Happy Testing!** 🎉

