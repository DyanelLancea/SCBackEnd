# Orchestrator Agent Guide

## Overview

The **Orchestrator Agent** is a powerful audio-to-text and translation service that:
1. Transcribes audio using OpenAI Whisper STT
2. Translates Singlish/colloquial speech to Standard English
3. Analyzes sentiment and tone

## Features

- ✅ **Speech-to-Text**: OpenAI Whisper API for accurate transcription
- ✅ **Singlish Support**: Understands Malay, Hokkien, Tamil, and local slang
- ✅ **LLM Processing**: Uses GPT-4o-mini for translation and analysis
- ✅ **Sentiment Analysis**: Detects emotional context
- ✅ **Tone Detection**: Identifies communication style
- ✅ **Dual Input**: Accepts both audio files and text transcripts
- ✅ **Internal API**: Can be called by other agents

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `openai==1.54.0` - OpenAI API client

### 2. Configure Environment

Add to your `.env` file:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Start the Backend

```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# Or directly
python -m app.main
```

## API Endpoints

Base URL: `http://localhost:8000/api/orchestrator`

### 1. Get Module Info

```http
GET /api/orchestrator/
```

**Response:**
```json
{
  "module": "Orchestrator",
  "version": "2.0",
  "description": "Audio transcription + Singlish → English translation",
  "capabilities": [...],
  "endpoints": {...},
  "status": "ready"
}
```

### 2. Process Audio or Text

```http
POST /api/orchestrator/process
Content-Type: multipart/form-data
```

**Parameters:**
- `audio` (file, optional): Audio file (mp3, wav, m4a, etc.)
- `transcript` (string, optional): Text transcript

*At least one parameter must be provided.*

**Response:**
```json
{
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh my, this man cut in line.",
  "sentiment": "frustrated",
  "tone": "annoyed"
}
```

### 3. Process Text Only (JSON)

```http
POST /api/orchestrator/process/text
Content-Type: application/json
```

**Request Body:**
```json
{
  "transcript": "walao this uncle cut queue sia"
}
```

**Response:**
```json
{
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh my, this man cut in line.",
  "sentiment": "frustrated",
  "tone": "annoyed"
}
```

### 4. Quick Test

```http
POST /api/orchestrator/test
```

Tests the orchestrator with a predefined Singlish example.

## Usage Examples

### Example 1: Process Text (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/orchestrator/process/text",
    json={"transcript": "wah lau eh this one really too much liao"}
)

result = response.json()
print(f"Original: {result['singlish_raw']}")
print(f"English: {result['clean_english']}")
print(f"Sentiment: {result['sentiment']}")
print(f"Tone: {result['tone']}")
```

### Example 2: Upload Audio File (Python)

```python
import requests

with open("recording.mp3", "rb") as audio_file:
    response = requests.post(
        "http://localhost:8000/api/orchestrator/process",
        files={"audio": ("recording.mp3", audio_file, "audio/mpeg")}
    )

result = response.json()
print(result)
```

### Example 3: cURL Request

```bash
# Text processing
curl -X POST "http://localhost:8000/api/orchestrator/process/text" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "can lah no problem one"}'

# Audio processing
curl -X POST "http://localhost:8000/api/orchestrator/process" \
  -F "audio=@recording.mp3"
```

### Example 4: JavaScript/Fetch

```javascript
// Text processing
const response = await fetch('http://localhost:8000/api/orchestrator/process/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ transcript: 'aiyah why you so like that one' })
});

const result = await response.json();
console.log(result);
```

### Example 5: Called by Another Agent

```python
# Inside another agent's routes.py
from app.ochestrator.routes import internal_process

async def my_endpoint():
    # Process Singlish text
    result = await internal_process(
        transcript_text="walao this uncle cut queue sia"
    )
    
    print(result["clean_english"])
    print(result["sentiment"])
    print(result["tone"])
```

## Test Examples

Run the test suite:

```bash
python test_orchestrator.py
```

### Common Singlish Test Cases

| Singlish Input | Expected English Output |
|----------------|------------------------|
| "walao this uncle cut queue sia" | "Oh my, this man cut in line." |
| "aiyah why you so like that one" | "Oh no, why are you acting this way?" |
| "can lah no problem one" | "Yes, that's fine, no problem." |
| "wah lau this queue damn long leh" | "Wow, this queue is very long." |
| "eh bro you free this weekend anot?" | "Hey friend, are you free this weekend?" |

## Technical Details

### Models Used

- **STT**: OpenAI Whisper (`whisper-1`)
- **LLM**: GPT-4o-mini (configurable)
  - Can upgrade to `gpt-4` or `gpt-4-turbo` for better accuracy
  - Current: `gpt-4o-mini` for cost efficiency

### Performance

- **Latency**: 1-3 seconds (depending on audio length)
- **Whisper Call**: ~1-2 seconds for 10-second audio
- **LLM Call**: ~1 second for translation + analysis
- **Total**: Single API call chain (Whisper → LLM)

### Supported Audio Formats

- MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM
- Max file size: 25 MB (OpenAI Whisper limit)

### Error Handling

Common errors:

| Error | Cause | Solution |
|-------|-------|----------|
| 500: "OPENAI_API_KEY not configured" | Missing API key | Add `OPENAI_API_KEY` to `.env` |
| 400: "Must provide either 'audio' or 'transcript'" | Empty request | Include at least one input |
| 500: "Error transcribing audio" | Invalid audio file | Check file format and size |
| 500: "Error processing with LLM" | API rate limit or network issue | Retry or check API quota |

## Advanced Configuration

### Change LLM Model

Edit `app/ochestrator/routes.py`:

```python
response = client.chat.completions.create(
    model="gpt-4",  # Change from gpt-4o-mini to gpt-4
    messages=[...],
    temperature=0.3,
    max_tokens=500
)
```

### Adjust Temperature

- `0.0-0.3`: More consistent, deterministic output
- `0.4-0.7`: Balanced creativity
- `0.8-1.0`: More creative, varied output

Current: `0.3` (recommended for translation tasks)

## Integration Guide

### Adding to Frontend

```javascript
// React/Next.js example
async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.mp3');
  
  const response = await fetch('/api/orchestrator/process', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}
```

### Adding to Other Agents

```python
# In another agent (e.g., wellness, safety, events)
from app.ochestrator.routes import internal_process

async def process_user_input(audio_or_text):
    result = await internal_process(transcript_text=audio_or_text)
    
    # Use cleaned English for further processing
    clean_text = result["clean_english"]
    sentiment = result["sentiment"]
    
    # Your agent logic here...
```

## Cost Estimation

Based on OpenAI pricing (as of Dec 2024):

- **Whisper**: $0.006 per minute of audio
- **GPT-4o-mini**: ~$0.0001 per request (for typical transcript length)
- **Total**: ~$0.006 per audio transcription + translation

Example: 1000 audio transcriptions/day = ~$6/day

## Troubleshooting

### OpenAI API Key Not Working

```bash
# Test your API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Audio Upload Fails

- Check file size < 25 MB
- Ensure correct Content-Type header
- Try converting to MP3 format

## Next Steps

1. **Test the endpoint**: Run `python test_orchestrator.py`
2. **Integrate with frontend**: Add audio recording UI
3. **Add to other agents**: Use `internal_process()` function
4. **Monitor usage**: Track OpenAI API costs
5. **Optimize prompts**: Adjust system prompt for better results

## Support

For issues or questions:
- Check `/docs` for API documentation
- Review error messages in backend logs
- Test with `/api/orchestrator/test` endpoint

---

**Last Updated**: December 2024
**Version**: 2.0

