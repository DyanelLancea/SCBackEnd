# 🦁 SEA-LION/Merlion LLM Setup Guide

## Why Use SEA-LION for Singlish?

**SEA-LION (Southeast Asian Language in One Network)** is specifically designed for Southeast Asian languages and cultures, making it **perfect for Singlish translation**:

✅ **Better Singlish Understanding**
- Trained on Southeast Asian language patterns
- Understands Malay, Hokkien, and dialect mixing
- Better cultural context awareness

✅ **Cost Effective**
- Open-source model
- Can be self-hosted (free)
- Lower API costs if using hosted version

✅ **Regional Focus**
- Built by AI Singapore
- Designed for Singaporean context
- Better at understanding local expressions

## 🚀 Setup Options

### Option 1: Use SEA-LION API (If Available)

If SEA-LION offers a hosted API:

1. **Get API credentials** from SEA-LION provider
2. **Set environment variables** in Render:
   ```
   SEA_LION_API_URL=https://api.sea-lion.ai/v1/chat/completions
   SEA_LION_API_KEY=your-key-here
   ```
3. **Code will automatically use SEA-LION** and fallback to OpenAI if it fails

### Option 2: Self-Host SEA-LION

If you want to self-host SEA-LION:

1. **Deploy SEA-LION model** (check https://docs.sea-lion.ai/)
2. **Set API URL** to your self-hosted instance:
   ```
   SEA_LION_API_URL=http://your-sea-lion-server:8000/v1/chat/completions
   ```
3. **No API key needed** if self-hosted without auth

### Option 3: Use OpenAI (Current Default)

If SEA-LION is not available:
- Just set `OPENAI_API_KEY` in Render
- Code will use OpenAI automatically
- Works as before

## 📋 Configuration

### Environment Variables

**For SEA-LION:**
```bash
SEA_LION_API_URL=https://api.sea-lion.ai/v1/chat/completions
SEA_LION_API_KEY=your-key-here  # Optional
```

**For OpenAI (fallback):**
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Priority Order

The code tries in this order:
1. **SEA-LION** (if `SEA_LION_API_URL` is set)
2. **OpenAI** (if SEA-LION fails or not configured)

## 🔧 How It Works

```python
# Code automatically:
1. Checks if SEA_LION_API_URL is set
2. If yes → tries SEA-LION first
3. If SEA-LION fails → falls back to OpenAI
4. If SEA-LION not configured → uses OpenAI directly
```

## 🧪 Testing

### Test with SEA-LION:
```bash
# Set environment variables
export SEA_LION_API_URL="https://api.sea-lion.ai/v1/chat/completions"
export SEA_LION_API_KEY="your-key"

# Test endpoint
curl -X POST http://localhost:8000/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "transcript": "walao this uncle cut queue sia"}'
```

### Test with OpenAI (fallback):
```bash
# Just set OpenAI key (SEA-LION will be skipped)
export OPENAI_API_KEY="sk-your-key"

# Same test
curl -X POST http://localhost:8000/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "transcript": "walao this uncle cut queue sia"}'
```

## 📝 Current Status

**Note**: SEA-LION API availability may vary. The code is set up to:
- ✅ Try SEA-LION if configured
- ✅ Automatically fallback to OpenAI
- ✅ Work seamlessly with either option

## 🔍 Finding SEA-LION API

1. **Check official docs**: https://docs.sea-lion.ai/
2. **AI Singapore**: May offer hosted API
3. **Self-hosting**: Deploy model yourself
4. **Alternative providers**: Some may offer SEA-LION as a service

## 💡 Recommendation

**For now:**
- Use OpenAI (it works and is reliable)
- When SEA-LION API becomes available, just add the environment variable
- Code will automatically switch

**For production:**
- If SEA-LION API is available → Use it (better for Singlish)
- If not → OpenAI works great too

## 🆘 Troubleshooting

### SEA-LION not working?
- Check API URL is correct
- Verify API key (if required)
- Check API endpoint format matches expected format
- Code will automatically fallback to OpenAI

### Want to force OpenAI?
- Don't set `SEA_LION_API_URL`
- Only set `OPENAI_API_KEY`
- Code will use OpenAI directly

### API format different?
- Modify `call_sea_lion_api()` function in `app/orchestrator/routes.py`
- Adjust payload format to match your SEA-LION API

---

## ✅ Summary

**You now have:**
- ✅ SEA-LION support (if available)
- ✅ Automatic fallback to OpenAI
- ✅ Easy configuration via environment variables
- ✅ Better Singlish understanding (when using SEA-LION)

**Just set the environment variables and it works!** 🎉

