# GROQ Migration Guide - Intent Detection

## Overview

We've migrated intent detection from OpenAI GPT to **GROQ** for significantly faster inference speeds and lower costs.

## Why GROQ?

### ✅ **Advantages:**
1. **Speed**: 10-100x faster than OpenAI (typically <100ms vs 1-3 seconds)
2. **Cost**: Significantly cheaper than GPT-4
3. **Perfect for Intent Detection**: Structured output task that doesn't need GPT-4's complexity
4. **Low Latency**: Critical for real-time voice/chat interfaces
5. **OpenAI-Compatible API**: Easy migration, same interface

### ⚠️ **Considerations:**
- Model quality: Llama 3.1 70B is excellent but may be slightly less capable than GPT-4 for very complex reasoning
- For intent detection: This is a perfect use case - structured, clear task

## What Changed

### 1. **Intent Detection** → Now uses GROQ (Llama 3.1 70B)
   - **Before**: GPT-4/GPT-3.5-turbo
   - **After**: GROQ with Llama 3.1 70B (fallback to 8B instant)
   - **Result**: 10-100x faster responses

### 2. **Audio Transcription** → Still uses OpenAI Whisper
   - GROQ doesn't have audio transcription
   - OpenAI Whisper remains the best option

### 3. **General Q&A** → Still uses OpenAI GPT
   - Can optionally switch to GROQ for faster responses
   - Currently uses GPT for more nuanced answers

## Setup Instructions

### 1. Install GROQ Package

```bash
pip install groq==0.11.1
```

Or update requirements.txt (already done):
```bash
pip install -r requirements.txt
```

### 2. Get GROQ API Key

1. Go to https://console.groq.com/
2. Sign up (free tier available)
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### 3. Add to Environment Variables

Add to your `.env` file:
```env
GROQ_API_KEY=your-groq-api-key-here
```

### 4. Restart Your Server

```bash
# If using uvicorn directly
uvicorn app.main:app --reload

# Or use your start script
python start.py
```

## Models Used

### Primary Model: `llama-3.1-70b-versatile`
- **Best quality** for intent detection
- Fast inference (~50-100ms)
- Excellent at structured JSON output

### Fallback Model: `llama-3.1-8b-instant`
- **Fastest** option (~20-50ms)
- Good quality for intent detection
- Used if 70B is unavailable

## API Changes

### No Breaking Changes!
- Same endpoints
- Same request/response format
- Same fallback behavior (keyword detection if GROQ unavailable)

### Response Format
- Uses `response_format={"type": "json_object"}` for reliable JSON output
- Enhanced JSON parsing handles edge cases

## Performance Comparison

| Metric | OpenAI GPT-4 | GROQ Llama 3.1 70B |
|--------|--------------|-------------------|
| **Latency** | 1-3 seconds | 50-100ms |
| **Cost per 1K tokens** | ~$0.03 | ~$0.0007 |
| **Speed Improvement** | Baseline | **10-100x faster** |
| **Accuracy** | Excellent | Excellent |

## Testing

### Test Intent Detection

```python
# Test with curl
curl -X POST http://localhost:8000/api/orchestrator/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "I want to join the pickleball tournament"
  }'
```

### Expected Response
```json
{
  "success": true,
  "intent": "book_event",
  "event_name": "pickleball tournament",
  "message": "Successfully registered you for 'Pickleball Tournament'!",
  ...
}
```

## Troubleshooting

### Issue: "GROQ_API_KEY not found"
**Solution**: Add `GROQ_API_KEY` to your `.env` file

### Issue: "Intent detection requires GROQ package"
**Solution**: Run `pip install groq==0.11.1`

### Issue: Intent detection falls back to keywords
**Check**:
1. GROQ_API_KEY is set correctly
2. API key is valid (check at https://console.groq.com/)
3. Internet connection is working
4. Check server logs for error messages

### Issue: JSON parsing errors
**Solution**: The code now handles JSON parsing more robustly. If issues persist, check GROQ API status.

## Fallback Behavior

If GROQ is unavailable, the system automatically falls back to:
1. **Keyword-based intent detection** (simple pattern matching)
2. **Same functionality** but less intelligent

This ensures the system always works, even without GROQ.

## Cost Comparison

### Example: 1000 intent detection requests

**OpenAI GPT-4:**
- ~300 tokens per request
- Cost: ~$0.009 per request
- **Total: ~$9.00**

**GROQ Llama 3.1 70B:**
- ~300 tokens per request  
- Cost: ~$0.0002 per request
- **Total: ~$0.20**

**Savings: ~98% cheaper!** 💰

## Next Steps (Optional)

### Consider GROQ for General Q&A
You can also switch general question answering to GROQ for faster responses:

```python
# In process_message() function, replace:
gpt_client = get_openai_client()
# With:
gpt_client = get_groq_client()
# And change model to "llama-3.1-70b-versatile"
```

## Support

- GROQ Documentation: https://console.groq.com/docs
- GROQ Models: https://console.groq.com/docs/models
- Issues: Check server logs for detailed error messages

---

**Migration Complete!** 🎉 Your intent detection is now 10-100x faster with GROQ!

