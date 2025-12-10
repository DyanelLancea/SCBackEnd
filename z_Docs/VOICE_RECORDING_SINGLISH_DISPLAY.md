# Voice Recording & Singlish Translation Display Process

## Overview

This document explains how the voice recording feature works from the front end, including the process of capturing Singlish input, translating it to standard English, and displaying both versions in the UI.

## Recording Flow

### 1. User Initiates Recording

When the user clicks/taps the voice button:
- The Web Speech API (`SpeechRecognition` or `webkitSpeechRecognition`) is initialized
- The microphone starts listening
- The UI shows "Listening..." with a red pulsing button

### 2. Audio Processing (Two Options)

**Option A: Send Audio Directly to Backend (RECOMMENDED)**
- Record audio → Convert to base64 → Send to `/process-singlish` with `audio` parameter
- Backend uses Whisper STT to transcribe (handles Singlish correctly)
- Get back: correct Singlish transcript + English translation
- Then send transcript to `/voice` endpoint

**Option B: Use Browser Speech Recognition First**
- Browser STT transcribes (may be incorrect for Singlish)
- **BUT**: Still send the original AUDIO to `/process-singlish` (not the wrong transcript)
- Backend Whisper will give correct transcription
- Get back: correct Singlish transcript + English translation

**Important**: Do NOT send incorrect browser transcript to `/process-singlish` - it won't fix it. Always send the original audio for accurate transcription.

### 3. Processing Pipeline

#### Step 1: Get Correct Transcript + Translation
```javascript
// Send AUDIO (not transcript) to process-singlish
const audioBlob = /* recorded audio */;
const base64Audio = /* convert blob to base64 */;

const singlishData = await processSinglish(userId, null, base64Audio);
// OR if you have correct transcript already:
// const singlishData = await processSinglish(userId, correctTranscript);

// Response includes:
// - singlish_raw: The correct Singlish transcript (from Whisper or your input)
// - clean_english: The translated standard English version
// - sentiment: Emotion detected
// - tone: Tone description
```

#### Step 2: Send to Orchestrator for Intent Processing
```javascript
// Use the CORRECT transcript from singlish_raw (not browser's wrong transcript)
const correctTranscript = singlishData.singlish_raw;

const data = await sendToVoiceEndpoint(userId, correctTranscript);
// OR: const data = await sendMessage(userId, correctTranscript);

// Response includes:
// - intent: Detected intent (book_event, emergency, list_events, etc.)
// - message: Orchestrator's response message
// - action_executed: Whether action was automatically executed
// - action_result: Result of the action
```

### 4. State Management

The component maintains separate state for:
- `audioBlob`: Recorded audio (for sending to backend)
- `singlishRaw`: Correct Singlish transcript (from `/process-singlish` API - `singlish_raw` field)
- `cleanEnglish`: Translated standard English (from `/process-singlish` API - `clean_english` field)
- `sentiment`: Detected sentiment (from `/process-singlish` API)
- `tone`: Detected tone (from `/process-singlish` API)
- `response`: Orchestrator's response message (from `/voice` endpoint)
- `intent`: Detected intent (from `/voice` endpoint)

## UI Display Structure

### Display Order

1. **Error Messages** (if any)
   - Red background box
   - Shows microphone or connection errors

2. **Singlish & English Translation** (NEW)
   - Blue background box
   - Two sections:
     - **🗣️ Singlish:** Shows the original Singlish input
     - **📝 English:** Shows the translated standard English
   - English section only appears if it differs from Singlish

3. **Orchestrator Response**
   - Green background box
   - Shows the AI's response
   - Includes intent badge

### Visual Example

```
┌─────────────────────────────────────┐
│ 🗣️ Singlish:                        │
│ walao this uncle cut queue sia      │
├─────────────────────────────────────┤
│ 📝 English:                         │
│ Oh my goodness, this man is cutting │
│ in line!                            │
└─────────────────────────────────────┘
```

## Implementation Details

### API Endpoints Used

1. **`/api/orchestrator/process-singlish`**
   - Purpose: Transcribe audio (if audio provided) OR translate Singlish transcript to standard English
   - Method: POST
   - Request (Option 1 - Send Audio):
     ```json
     {
       "user_id": "string",
       "audio": "base64_encoded_audio_string"
     }
     ```
   - Request (Option 2 - Send Transcript):
     ```json
     {
       "user_id": "string",
       "transcript": "walao this uncle cut queue sia"
     }
     ```
   - Response:
     ```json
     {
       "success": true,
       "singlish_raw": "walao this uncle cut queue sia",  // From Whisper if audio sent, or your transcript if text sent
       "clean_english": "Oh my goodness, this man is cutting in line!",
       "sentiment": "frustrated",
       "tone": "informal, colloquial"
     }
     ```
   - **Important**: If you send audio, Whisper will transcribe it correctly. If you send a wrong transcript, it won't fix it - it will just translate whatever you give it.

2. **`/api/orchestrator/voice`**
   - Purpose: Process voice transcript and detect intent (auto-executes actions)
   - Method: POST
   - Request:
     ```json
     {
       "user_id": "string",
       "transcript": "correct transcribed text",  // Use singlish_raw from process-singlish response
       "location": "string (optional)"
     }
     ```
   - Response:
     ```json
     {
       "success": true,
       "intent": "book_event | emergency | list_events | ...",
       "message": "Response message",
       "transcript": "Original transcript",
       "source": "voice",
       "action_executed": true,
       "action_result": {...},
       "sos_triggered": false
     }
     ```

### Code Flow

**Recommended Flow (Send Audio to Backend)**:
```javascript
// 1. Record audio
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
  setIsProcessing(true);
  
  try {
    // 2. Convert audio to base64
    const base64Audio = await blobToBase64(audioBlob);
    
    // 3. Send AUDIO to process-singlish (not transcript!)
    const singlishData = await processSinglish(userId, null, base64Audio);
    
    if (singlishData.success) {
      // 4. Get correct transcript and translation
      const correctTranscript = singlishData.singlish_raw;
      setSinglishRaw(correctTranscript);
      setCleanEnglish(singlishData.clean_english);
      setSentiment(singlishData.sentiment);
      setTone(singlishData.tone);
      
      // 5. Send CORRECT transcript to voice endpoint
      const orchestratorData = await sendToVoiceEndpoint(userId, correctTranscript);
      setResponse(orchestratorData.message);
      setIntent(orchestratorData.intent);
    }
  } catch (error) {
    console.error('Processing error:', error);
    // Handle error
  } finally {
    setIsProcessing(false);
  }
};

// Helper function to convert blob to base64
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
```

**Alternative Flow (If Using Browser STT)**:
```javascript
// 1. Browser STT (may be wrong, but we'll fix it)
recognitionRef.current.onresult = async (event) => {
  const browserTranscript = event.results[0][0].transcript; // May be wrong!
  const audioBlob = /* get the recorded audio blob */;
  
  // 2. Send AUDIO (not the wrong transcript!) to process-singlish
  const base64Audio = await blobToBase64(audioBlob);
  const singlishData = await processSinglish(userId, null, base64Audio);
  
  // 3. Use correct transcript from backend
  const correctTranscript = singlishData.singlish_raw; // This is correct!
  setSinglishRaw(correctTranscript);
  setCleanEnglish(singlishData.clean_english);
  
  // 4. Send correct transcript to orchestrator
  await sendToVoiceEndpoint(userId, correctTranscript);
};
```

### UI Rendering Logic

```javascript
{/* Display both Singlish and English */}
{(singlishRaw || cleanEnglish) && (
  <div className="mt-4 rounded-2xl bg-blue-50 p-4 border-2 border-blue-200">
    {/* Show original Singlish */}
    {singlishRaw && (
      <div className="mb-3">
        <p className="text-sm font-bold text-blue-900">🗣️ Singlish:</p>
        <p className="text-lg text-blue-700 mt-1">{singlishRaw}</p>
      </div>
    )}
    
    {/* Show English translation only if different */}
    {cleanEnglish && singlishRaw !== cleanEnglish && (
      <div className="pt-3 border-t border-blue-300">
        <p className="text-sm font-bold text-blue-900">📝 English:</p>
        <p className="text-lg text-blue-700 mt-1">{cleanEnglish}</p>
      </div>
    )}
  </div>
)}
```

## Why This Approach?

### Problem Solved

**Before:** Browser speech recognition incorrectly transcribes Singlish:
- User says: "walao this uncle cut queue sia"
- Browser STT shows: "what love is this Uncle cut kills you" ❌
- Sending wrong transcript to backend doesn't fix it ❌

**After:** Send audio to backend Whisper (handles Singlish correctly):
- User says: "walao this uncle cut queue sia"
- Backend Whisper transcribes: "walao this uncle cut queue sia" ✅
- Backend translates: "Oh my goodness, this man is cutting in line!" ✅
- Display shows both correctly ✅

### Benefits

1. **Accuracy**: Users see what they actually said (Singlish)
2. **Clarity**: Users see the correct English translation
3. **Transparency**: Both versions are visible for verification
4. **Fallback**: If translation fails, raw transcript is still shown

## Error Handling

### Translation API Failure

If `processSinglish` fails:
- **If audio was sent**: Falls back to browser STT (may be incorrect)
- **If transcript was sent**: Uses the transcript you provided
- User still sees the transcript (even if incorrect)
- System continues to work with orchestrator
- Consider showing error message to user

### Network Issues

If API calls fail:
- Error message is displayed
- User can retry recording
- No data is lost (transcript is preserved)

## User Experience

### Expected Behavior

1. User taps voice button
2. User speaks in Singlish: "walao this uncle cut queue sia"
3. System processes:
   - **Captures audio** → Converts to base64
   - **Sends AUDIO to `/process-singlish`** → Whisper transcribes correctly → Gets correct Singlish + English translation
   - **Sends correct transcript to `/voice`** → Gets intent and auto-executes actions
4. UI displays:
   - **🗣️ Singlish:** "walao this uncle cut queue sia" (from `singlish_raw`)
   - **📝 English:** "Oh my goodness, this man is cutting in line!" (from `clean_english`)
   - **😊 Sentiment:** "frustrated" (optional display)
   - **🎭 Tone:** "informal, colloquial" (optional display)
   - **🤖 Orchestrator Response:** [AI's response based on intent]

### Edge Cases

- **Pure English input**: Both Singlish and English sections show the same text (or English section hidden if identical)
- **Translation fails**: Shows transcript from browser STT (may be incorrect) or falls back gracefully
- **No speech detected**: Error message displayed
- **Microphone denied**: Permission error with helpful tip
- **Audio too large**: Backend may reject - compress or limit recording duration

## Technical Notes

### Files Modified

- `pages/components/VoiceRecorder.jsx`
- `app/components/VoiceRecorder.jsx`

### Dependencies

- `react-hot-toast`: For toast notifications
- `react`: React hooks (useState, useRef, useEffect)
- `next/router` or `next/navigation`: For routing
- Web Speech API: Browser-native speech recognition

### API Functions Used

- `processSinglish(userId, transcript)`: From `lib/api.js`
- `sendMessage(userId, message)`: From `lib/api.js`

## Future Enhancements

Potential improvements:
1. Show sentiment and tone from translation API
2. Allow users to edit/correct the translation
3. Save translation history
4. Support for other dialects/languages
5. Real-time translation during recording

