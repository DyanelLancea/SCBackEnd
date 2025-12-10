# Frontend Guide: Singlish Orchestrator Integration

## Overview
This guide explains how to integrate your frontend with the Singlish Orchestrator agent that processes Singlish audio/text and returns clean English translations with sentiment analysis.

---

## 🎯 Frontend Responsibilities

Your frontend needs to:
1. **Capture audio** from user's microphone OR accept text input
2. **Send data** to backend orchestrator endpoint
3. **Display results** (original Singlish, clean English, sentiment, tone)
4. **Handle errors** gracefully

---

## 📋 Backend Endpoint You'll Call

```
POST /api/orchestrator/process-singlish
```

**Request Body (JSON):**
```json
{
  "user_id": "string",
  "audio": "base64_encoded_audio_string (optional)",
  "transcript": "walao this uncle cut queue sia (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh no, this elderly man cut in line.",
  "sentiment": "frustrated",
  "tone": "informal, colloquial"
}
```

---

## 🎤 Option 1: Audio Recording (Recommended)

### Step 1: Request Microphone Permission

```javascript
// Check if browser supports audio recording
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  alert('Your browser does not support audio recording');
  return;
}

// Request microphone access
try {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  console.log('Microphone access granted');
} catch (error) {
  console.error('Microphone access denied:', error);
}
```

### Step 2: Record Audio

```javascript
// Using MediaRecorder API
let mediaRecorder;
let audioChunks = [];

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };
  
  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    await sendAudioToBackend(audioBlob);
    audioChunks = [];
  };
  
  mediaRecorder.start();
  console.log('Recording started');
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    console.log('Recording stopped');
  }
}
```

### Step 3: Convert Audio to Base64 and Send

```javascript
async function sendAudioToBackend(audioBlob) {
  // Convert blob to base64
  const reader = new FileReader();
  reader.readAsDataURL(audioBlob);
  
  reader.onloadend = async () => {
    const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
    
    // Send to backend
    try {
      const response = await fetch('http://localhost:8000/api/orchestrator/process-singlish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: getCurrentUserId(), // Your user ID function
          audio: base64Audio,
        }),
      });
      
      const data = await response.json();
      displayResults(data);
    } catch (error) {
      console.error('Error sending audio:', error);
      alert('Failed to process audio. Please try again.');
    }
  };
}
```

---

## ⌨️ Option 2: Text Input (Simpler Alternative)

If user prefers to type instead of speaking:

```javascript
async function sendTextToBackend(transcript) {
  try {
    const response = await fetch('http://localhost:8000/api/orchestrator/process-singlish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: getCurrentUserId(),
        transcript: transcript,
      }),
    });
    
    const data = await response.json();
    displayResults(data);
  } catch (error) {
    console.error('Error processing text:', error);
    alert('Failed to process text. Please try again.');
  }
}
```

---

## 🎨 UI Component Example (React)

```jsx
import React, { useState, useRef } from 'react';

export default function SinglishTranslator() {
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Start audio recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      alert('Microphone access denied');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Process audio
  const processAudio = async (audioBlob) => {
    setLoading(true);
    const reader = new FileReader();
    reader.readAsDataURL(audioBlob);

    reader.onloadend = async () => {
      const base64Audio = reader.result.split(',')[1];

      try {
        const response = await fetch('http://localhost:8000/api/orchestrator/process-singlish', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 'user_123', // Replace with actual user ID
            audio: base64Audio,
          }),
        });

        const data = await response.json();
        setResult(data);
      } catch (error) {
        alert('Failed to process audio');
      } finally {
        setLoading(false);
      }
    };
  };

  // Process text
  const processText = async () => {
    if (!textInput.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/orchestrator/process-singlish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'user_123', // Replace with actual user ID
          transcript: textInput,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert('Failed to process text');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Singlish Translator</h1>

      {/* Audio Recording Section */}
      <div className="mb-6 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-3">🎤 Record Audio</h2>
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-6 py-3 rounded-lg font-semibold ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
          disabled={loading}
        >
          {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
        </button>
      </div>

      {/* Text Input Section */}
      <div className="mb-6 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-3">⌨️ Or Type Text</h2>
        <textarea
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Type Singlish here... e.g., 'walao this uncle cut queue sia'"
          className="w-full p-3 border rounded-lg mb-3"
          rows="3"
        />
        <button
          onClick={processText}
          className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-semibold"
          disabled={loading || !textInput.trim()}
        >
          Translate to English
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <p className="text-lg">Processing...</p>
        </div>
      )}

      {/* Results Display */}
      {result && !loading && (
        <div className="p-6 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-bold mb-4">Results</h2>
          
          <div className="mb-4">
            <h3 className="font-semibold text-gray-700">Original Singlish:</h3>
            <p className="text-lg">{result.singlish_raw}</p>
          </div>

          <div className="mb-4">
            <h3 className="font-semibold text-gray-700">Clean English:</h3>
            <p className="text-lg text-blue-600">{result.clean_english}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-gray-700">Sentiment:</h3>
              <p className="text-lg">{result.sentiment}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700">Tone:</h3>
              <p className="text-lg">{result.tone}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 📦 Required NPM Packages

```bash
# No additional packages needed for basic implementation
# Browser APIs handle everything

# Optional: For better audio handling
npm install recordrtc  # Advanced recording library
```

---

## 🔒 Error Handling Checklist

```javascript
// 1. Check microphone permission
if (!navigator.mediaDevices) {
  alert('Microphone not supported in this browser');
}

// 2. Handle API errors
try {
  const response = await fetch(...);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
} catch (error) {
  console.error('API call failed:', error);
  alert('Something went wrong. Please try again.');
}

// 3. Handle empty input
if (!textInput.trim() && !audioBlob) {
  alert('Please provide audio or text input');
  return;
}

// 4. Handle timeout
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 sec timeout

try {
  const response = await fetch(url, {
    ...options,
    signal: controller.signal
  });
} catch (error) {
  if (error.name === 'AbortError') {
    alert('Request timed out. Please try again.');
  }
} finally {
  clearTimeout(timeoutId);
}
```

---

## 🧪 Testing Your Integration

### Test Cases:

1. **Audio Recording**:
   - Record "walao this uncle cut queue sia"
   - Should return clean English translation

2. **Text Input**:
   - Type "aiyo why like that one"
   - Should return proper English

3. **Error Handling**:
   - Try without microphone permission
   - Try with empty input
   - Try with network disconnected

### Example Test Transcript:
```
Input: "walao this uncle cut queue sia"
Expected Output: {
  singlish_raw: "walao this uncle cut queue sia",
  clean_english: "Oh no, this elderly man cut in line.",
  sentiment: "frustrated",
  tone: "informal, colloquial"
}
```

---

## 🚀 Deployment Considerations

1. **HTTPS Required**: Browser microphone APIs require HTTPS in production
2. **CORS**: Ensure backend allows your frontend domain
3. **File Size**: Audio files can be large - consider compression
4. **Timeout**: Set reasonable timeout (30-60 seconds) for audio processing

---

## 📱 Mobile Considerations

```javascript
// Mobile-specific: Handle orientation changes
window.addEventListener('orientationchange', () => {
  // Pause/resume recording if needed
});

// Mobile-specific: Handle background/foreground
document.addEventListener('visibilitychange', () => {
  if (document.hidden && isRecording) {
    stopRecording();
  }
});
```

---

## 🔗 Full Flow Diagram

```
User Action
    ↓
[Record Audio Button] OR [Type Text Box]
    ↓
Capture Audio/Text
    ↓
Convert to Base64 (if audio)
    ↓
POST to /api/orchestrator/process-singlish
    ↓
Backend processes with Whisper + GPT
    ↓
Receive JSON response
    ↓
Display: Original | Clean English | Sentiment | Tone
```

---

## 📚 Next Steps

1. ✅ Implement audio recording UI component
2. ✅ Implement text input fallback
3. ✅ Add loading states and error handling
4. ✅ Style results display
5. ⏳ Wait for backend endpoint to be ready
6. ⏳ Test integration end-to-end

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Microphone not working | Check browser permissions in settings |
| CORS error | Add your frontend URL to backend CORS config |
| Audio too large | Compress audio or use shorter recordings |
| Slow processing | Audio processing takes 5-10 seconds - add loading indicator |
| Wrong format error | Ensure audio is base64 encoded properly |

---

## 📞 Questions?

If you encounter issues:
1. Check browser console for errors
2. Test backend endpoint with Postman first
3. Verify audio base64 encoding is correct
4. Check network tab for failed requests

**Remember**: The backend needs to be updated first to accept this format before frontend integration will work!

