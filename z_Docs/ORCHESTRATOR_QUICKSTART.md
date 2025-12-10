# Orchestrator Agent - Quick Start

## 🚀 One-Minute Setup

### 1. Add OpenAI API Key

Add to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test It

```bash
# Start backend
python -m app.main

# In another terminal, run test
python test_orchestrator.py
```

## 📡 API Endpoints

### Process Text (Singlish → English)

```bash
curl -X POST "http://localhost:8000/api/orchestrator/process/text" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "walao this uncle cut queue sia"}'
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

### Process Audio

```bash
curl -X POST "http://localhost:8000/api/orchestrator/process" \
  -F "audio=@recording.mp3"
```

### Quick Test

```bash
curl -X POST "http://localhost:8000/api/orchestrator/test"
```

## 🔧 Integration in Other Agents

```python
from app.ochestrator.routes import internal_process

async def my_function():
    result = await internal_process(
        transcript_text="aiyah why you so like that one"
    )
    
    print(result["clean_english"])  # "Oh no, why are you acting this way?"
    print(result["sentiment"])      # "frustrated"
    print(result["tone"])           # "disappointed"
```

## 🧪 Test Examples

| Input (Singlish) | Output (English) | Sentiment | Tone |
|------------------|------------------|-----------|------|
| "walao this uncle cut queue sia" | "Oh my, this man cut in line." | frustrated | annoyed |
| "can lah no problem one" | "Yes, that's fine, no problem." | positive | casual |
| "wah lau this queue damn long leh" | "Wow, this queue is very long." | neutral | exasperated |
| "aiyah why you so like that one" | "Oh no, why are you acting this way?" | frustrated | disappointed |

## 📚 Full Documentation

See: `z_Docs/ORCHESTRATOR_GUIDE.md`

## 🎯 What This Agent Does

1. **Transcribes** audio to text (OpenAI Whisper)
2. **Translates** Singlish → Standard English
3. **Interprets** Malay, Hokkien, Tamil slang
4. **Analyzes** sentiment and tone
5. **Returns** structured JSON output

## ⚙️ Technical Stack

- **STT**: OpenAI Whisper API (`whisper-1`)
- **LLM**: GPT-4o-mini (upgradeable to GPT-4)
- **Framework**: FastAPI
- **Input**: Audio (mp3, wav, m4a) or Text
- **Output**: JSON with 4 fields

## 💰 Cost

- ~$0.006 per audio transcription
- ~$0.0001 per text translation
- Total: **~$6 per 1000 requests**

## 🐛 Troubleshooting

### "OPENAI_API_KEY not configured"
→ Add API key to `.env` file

### "Must provide either 'audio' or 'transcript'"
→ Include at least one input parameter

### Import errors
→ Run: `pip install -r requirements.txt`

## 🎉 You're Ready!

Try it now:
```bash
python test_orchestrator.py
```

Visit: http://localhost:8000/docs

