# 🦁 SEA-LION API Setup Guide

## ✅ Good News: SEA-LION Has an Official API!

SEA-LION provides an official API through their playground. Here's how to get your API key:

## 🔑 Step-by-Step: Get Your SEA-LION API Key

### Step 1: Sign In to SEA-LION Playground
1. Go to: **https://playground.sea-lion.ai/**
2. **Sign in with your Google account**

### Step 2: Get Your API Key
1. Click on **"API Key"** in the side menu, OR
2. Select **"Launch Key Manager"** from the home dashboard

### Step 3: Create API Key
1. Click **"Create New Trial API Key"** button
2. Enter a name for your API key (e.g., "Singlish Translator")
3. Click **"Create"** to generate the key

### Step 4: Copy Your Key
- **IMPORTANT**: Copy the key immediately!
- You won't be able to view it again later
- Only one API key is allowed per user

## 📋 API Details

**API Endpoint**: `https://api.sea-lion.ai/v1/chat/completions`

**Model Name**: `aisingapore/Gemma-SEA-LION-v4-27B-IT`

**Authentication**: Bearer token (your API key)

## 🔧 Setup in Render

### Environment Variables

Add these to your Render environment:

```bash
# SEA-LION API (if you want to use it)
SEA_LION_API_URL=https://api.sea-lion.ai/v1/chat/completions
SEA_LION_API_KEY=your-sea-lion-api-key-here

# OpenAI (fallback - still works if SEA-LION not set)
OPENAI_API_KEY=sk-your-openai-key-here
```

## 🎯 How It Works

The code will:
1. **Check if `SEA_LION_API_URL` is set**
2. **If yes** → Try SEA-LION API first
3. **If SEA-LION fails** → Automatically fallback to OpenAI
4. **If SEA-LION not configured** → Use OpenAI directly

## 🧪 Testing

### Test with SEA-LION:
```bash
curl -X POST https://your-app.onrender.com/api/orchestrator/process-singlish \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "transcript": "walao this uncle cut queue sia"
  }'
```

### Expected Response:
```json
{
  "success": true,
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh no, this elderly man cut in line.",
  "sentiment": "frustrated",
  "tone": "informal, colloquial"
}
```

## 📚 References

- **SEA-LION Playground**: https://playground.sea-lion.ai/
- **API Documentation**: https://docs.sea-lion.ai/guides/inferencing/api
- **Model Page**: https://huggingface.co/aisingapore/Gemma-SEA-LION-v4-27B-IT

## 💡 Benefits of Using SEA-LION

✅ **Better Singlish Understanding**
- Trained specifically on Southeast Asian languages
- Understands Malay, Hokkien, and dialect mixing
- Better cultural context

✅ **Cost Effective**
- Trial API key available
- Potentially lower costs than OpenAI

✅ **Regional Focus**
- Built by AI Singapore
- Designed for Singaporean context

## 🆘 Troubleshooting

### "API key not found"
- Make sure you copied the key correctly
- Check for extra spaces
- Verify key is set in Render environment

### "401 Unauthorized"
- Your API key is invalid
- Generate a new key from playground
- Make sure you're using the correct key

### "Model not available"
- Check if the model name is correct
- Verify API endpoint URL
- Code will automatically fallback to OpenAI

## ✅ Summary

1. **Get API key**: https://playground.sea-lion.ai/ → API Key Manager
2. **Set environment variables** in Render
3. **Code automatically uses SEA-LION** if configured
4. **Falls back to OpenAI** if SEA-LION fails

**That's it! Your code is already set up to use it!** 🎉

