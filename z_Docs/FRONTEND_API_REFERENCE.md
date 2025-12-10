# Frontend API Reference Guide

## Base URL

**Production**: `https://scbackend-qfh6.onrender.com`  
**Local Development**: `http://localhost:8000`

All endpoints are prefixed with `/api`

---

# 🎯 Orchestrator Agent

The Orchestrator is the main intelligent coordinator that processes user messages, detects intent, and automatically executes actions.

## Base Path: `/api/orchestrator`

---

## 1. Get Orchestrator Info

**Endpoint**: `GET /api/orchestrator/`

**Description**: Returns information about the Orchestrator module and available endpoints.

**Request**: No body required

**Response**:
```json
{
  "module": "Orchestrator",
  "description": "Main coordinator and request routing agent",
  "capabilities": [
    "Natural language understanding",
    "Intent classification",
    "Request routing to specialized modules",
    "Conversation management"
  ],
  "endpoints": {
    "message": "/api/orchestrator/message",
    "voice": "/api/orchestrator/voice",
    "history": "/api/orchestrator/history/{user_id}"
  },
  "status": "ready"
}
```

**Example**:
```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/');
const data = await response.json();
console.log(data);
```

---

## 2. Process Text Message

**Endpoint**: `POST /api/orchestrator/message`

**Description**: Processes a text message, detects intent using AI, and automatically executes actions (SOS calls, event registration, etc.).

**Request Body**:
```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "location": "string (optional)"
}
```

**Response**:
```json
{
  "success": true,
  "intent": "book_event | emergency | list_events | get_event | cancel_event | general",
  "message": "Response message to user",
  "user_id": "user_123",
  "action_executed": true,
  "action_result": {
    // Varies based on action:
    // - Event registration: { "registration": {...}, "event_title": "..." }
    // - SOS call: { "call_successful": true, "call_id": "..." }
    // - Event list: { "events": [...], "count": 5 }
  },
  "sos_triggered": false
}
```

**Example Request**:
```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user_123',
    message: 'I want to join the pickleball event',
    location: 'Singapore' // optional
  })
});

const data = await response.json();
// Response: { "success": true, "intent": "book_event", "message": "Successfully registered you for 'Pickleball Tournament'!", ... }
```

**Intent Types**:
- `emergency` - Automatically triggers SOS call
- `book_event` / `register_event` - Automatically registers user for event
- `list_events` - Returns list of available events
- `get_event` - Returns specific event details
- `cancel_event` / `unregister_event` - Unregisters from event
- `general` - General conversation

**Automatic Actions**:
- **Emergency**: Automatically calls `/api/safety/sos`
- **Event Booking**: Automatically calls `/api/events/register`
- **List Events**: Automatically calls `/api/events/list`
- **Get Event**: Automatically calls `/api/events/{id}`
- **Cancel Event**: Automatically calls `/api/events/register/{event_id}/{user_id}`

---

## 3. Process Voice Message

**Endpoint**: `POST /api/orchestrator/voice`

**Description**: Processes a voice transcript (same as text message). Frontend should send the transcribed text from voice recording.

### What the Backend Does:
1. **Receives transcript** - Gets the transcribed text from your frontend
2. **Processes like text message** - Uses the same AI intent detection as `/message` endpoint
3. **Detects intent** - Identifies what the user wants (emergency, book event, etc.)
4. **Auto-executes actions** - Automatically performs actions based on intent:
   - Emergency → Triggers SOS call
   - Book event → Registers user for event
   - List events → Returns available events
   - etc.
5. **Returns results** - Same response as `/message` but with `source: "voice"` added

### What the Frontend Needs to Do:

**Step 1: Record Audio**
```javascript
// Start recording
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
    await processVoiceRecording(audioBlob);
    audioChunks = [];
  };
  
  mediaRecorder.start();
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
}
```

**Step 2: Transcribe Audio (Choose One Option)**

**Option A: Use Browser Speech Recognition API (Recommended)**
```javascript
function transcribeAudio(audioBlob) {
  return new Promise((resolve, reject) => {
    // Convert blob to audio element
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    // Use Web Speech API
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-SG'; // Singapore English
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      resolve(transcript);
    };
    
    recognition.onerror = (error) => {
      reject(error);
    };
    
    // Start recognition
    recognition.start();
    
    // Play audio and recognize
    audio.play();
  });
}
```

**Option B: Use Backend Whisper API (via `/process-singlish`)**
```javascript
async function transcribeWithBackend(audioBlob) {
  // Convert to base64
  const reader = new FileReader();
  reader.readAsDataURL(audioBlob);
  
  return new Promise((resolve, reject) => {
    reader.onloadend = async () => {
      const base64Audio = reader.result.split(',')[1];
      
      // Use process-singlish endpoint to get transcript
      const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/process-singlish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'user_123',
          audio: base64Audio
        })
      });
      
      const data = await response.json();
      resolve(data.singlish_raw); // Get the transcript
    };
  });
}
```

**Step 3: Send Transcript to Voice Endpoint**
```javascript
async function processVoiceRecording(audioBlob) {
  try {
    // Step 1: Transcribe audio (choose one method above)
    const transcript = await transcribeAudio(audioBlob);
    // OR: const transcript = await transcribeWithBackend(audioBlob);
    
    // Step 2: Send transcript to voice endpoint
    const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/voice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 'user_123',
        transcript: transcript, // Transcribed text
        location: 'Singapore' // Optional: user's location
      })
    });
    
    const result = await response.json();
    
    // Handle response
    if (result.action_executed) {
      console.log('Action executed:', result.message);
      if (result.sos_triggered) {
        console.log('SOS call triggered!');
      }
    }
    
    return result;
  } catch (error) {
    console.error('Voice processing error:', error);
  }
}
```

**Complete Example Flow**:
```javascript
// 1. User clicks record button
startRecording();

// 2. User speaks: "I want to join the pickleball event"

// 3. User clicks stop
stopRecording(); // Automatically calls processVoiceRecording()

// 4. Frontend transcribes: "I want to join the pickleball event"

// 5. Frontend sends to backend: POST /api/orchestrator/voice

// 6. Backend processes and auto-registers user for event

// 7. Frontend receives: { "success": true, "intent": "book_event", "message": "Successfully registered...", ... }
```

**Request Body**:
```json
{
  "user_id": "string (required)",
  "transcript": "string (required) - Transcribed text from voice recording",
  "location": "string (optional)"
}
```

**Response**:
```json
{
  "success": true,
  "intent": "book_event | emergency | list_events | ...",
  "message": "Response message",
  "user_id": "user_123",
  "transcript": "Original transcript",
  "source": "voice",
  "action_executed": true,
  "action_result": {...},
  "sos_triggered": false
}
```

**Important Notes**:
- ✅ Frontend must transcribe audio BEFORE sending to `/voice` endpoint
- ✅ Backend does NOT do transcription - it only processes the transcript
- ✅ For transcription, use browser Speech Recognition API or send audio to `/process-singlish` first
- ✅ After transcription, send text to `/voice` endpoint
- ✅ Backend automatically executes actions (SOS, event booking, etc.) based on intent

---

## 4. Process Singlish (Translation & Analysis)

**Endpoint**: `POST /api/orchestrator/process-singlish`

**Description**: Translates Singlish to Standard English and analyzes sentiment/tone. Accepts audio (base64) or text transcript.

**Request Body**:
```json
{
  "user_id": "string (required)",
  "audio": "string (optional) - Base64 encoded audio",
  "transcript": "string (optional) - Direct text transcript"
}
```

**Note**: Either `audio` OR `transcript` must be provided (not both required, but at least one).

**Response**:
```json
{
  "success": true,
  "user_id": "user_123",
  "singlish_raw": "walao this uncle cut queue sia",
  "clean_english": "Oh my goodness, this man is cutting in line!",
  "sentiment": "frustrated",
  "tone": "informal, colloquial"
}
```

**Example Request (Text)**:
```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/process-singlish', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user_123',
    transcript: 'walao this uncle cut queue sia'
  })
});

const data = await response.json();
// {
//   "success": true,
//   "singlish_raw": "walao this uncle cut queue sia",
//   "clean_english": "Oh my goodness, this man is cutting in line!",
//   "sentiment": "frustrated",
//   "tone": "informal, colloquial"
// }
```

**Example Request (Audio)**:
```javascript
// Convert audio blob to base64
const reader = new FileReader();
reader.readAsDataURL(audioBlob);
reader.onloadend = async () => {
  const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
  
  const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/process-singlish', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: 'user_123',
      audio: base64Audio
    })
  });
  
  const data = await response.json();
};
```

**Sentiment Values**: `happy`, `frustrated`, `angry`, `neutral`, `surprised`, `sad`, etc.

**Tone Values**: `informal`, `casual`, `urgent`, `polite`, `aggressive`, `colloquial`, etc.

---

## 5. Get Conversation History

**Endpoint**: `GET /api/orchestrator/history/{user_id}`

**Description**: Get conversation history for a user (placeholder - ready for implementation).

**URL Parameters**:
- `user_id` (path parameter) - User ID

**Query Parameters**:
- `limit` (optional, default: 20) - Number of conversations to return

**Response**:
```json
{
  "success": true,
  "user_id": "user_123",
  "conversations": [],
  "count": 0,
  "message": "Conversation history - ready for implementation"
}
```

**Example Request**:
```javascript
const userId = 'user_123';
const limit = 20;
const response = await fetch(`https://scbackend-qfh6.onrender.com/api/orchestrator/history/${userId}?limit=${limit}`);
const data = await response.json();
```

---

## 6. Test Route

**Endpoint**: `GET /api/orchestrator/test-route`

**Description**: Simple test endpoint to verify routes are working.

**Response**:
```json
{
  "success": true,
  "message": "Orchestrator routes are working!",
  "endpoint": "/api/orchestrator/test-route"
}
```

---

# 💚 Wellness Agent

The Wellness agent handles health reminders, social engagement tracking, and user analytics.

## Base Path: `/api/wellness`

---

## 1. Get Wellness Info

**Endpoint**: `GET /api/wellness/`

**Description**: Returns information about the Wellness module.

**Response**:
```json
{
  "module": "Wellness & Social Intelligence",
  "description": "Social engagement, health management, and community activities",
  "capabilities": [
    "Interest-based matching",
    "Health reminders",
    "Social engagement tracking",
    "Community activities"
  ],
  "endpoints": {
    "reminders": "/api/wellness/reminders/{user_id}",
    "analytics": "/api/wellness/analytics/{user_id}"
  },
  "status": "ready"
}
```

---

## 2. Get User Reminders

**Endpoint**: `GET /api/wellness/reminders/{user_id}`

**Description**: Get all reminders for a specific user.

**URL Parameters**:
- `user_id` (path parameter) - User ID

**Response**:
```json
{
  "success": true,
  "user_id": "user_123",
  "reminders": [],
  "message": "Reminders feature - ready for implementation"
}
```

**Example Request**:
```javascript
const userId = 'user_123';
const response = await fetch(`https://scbackend-qfh6.onrender.com/api/wellness/reminders/${userId}`);
const data = await response.json();
```

---

## 3. Create Reminder

**Endpoint**: `POST /api/wellness/reminders`

**Description**: Create a new reminder for a user.

**Request Body**:
```json
{
  "user_id": "string (required)",
  "title": "string (required)",
  "description": "string (optional)",
  "reminder_type": "string (required) - appointment | medication | hydration | exercise | custom",
  "scheduled_time": "string (required) - ISO format datetime (e.g., '2024-12-25T10:00:00Z')"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Reminder created",
  "reminder": {
    "user_id": "user_123",
    "title": "Take medication",
    "description": "Morning vitamins",
    "reminder_type": "medication",
    "scheduled_time": "2024-12-25T10:00:00Z"
  }
}
```

**Example Request**:
```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/wellness/reminders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user_123',
    title: 'Take medication',
    description: 'Morning vitamins',
    reminder_type: 'medication',
    scheduled_time: '2024-12-25T10:00:00Z'
  })
});

const data = await response.json();
```

**Reminder Types**:
- `appointment` - Medical or other appointments
- `medication` - Medication reminders
- `hydration` - Water intake reminders
- `exercise` - Exercise/workout reminders
- `custom` - Custom reminders

---

## 4. Get User Analytics

**Endpoint**: `GET /api/wellness/analytics/{user_id}`

**Description**: Get user engagement analytics and statistics.

**URL Parameters**:
- `user_id` (path parameter) - User ID

**Response**:
```json
{
  "success": true,
  "user_id": "user_123",
  "analytics": {
    "events_registered": 5,
    "active_reminders": 3,
    "engagement_score": 85
  }
}
```

**Example Request**:
```javascript
const userId = 'user_123';
const response = await fetch(`https://scbackend-qfh6.onrender.com/api/wellness/analytics/${userId}`);
const data = await response.json();
```

---

# 🔧 Error Handling

## Standard Error Response Format

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input, missing required fields)
- `404` - Not Found (endpoint or resource doesn't exist)
- `500` - Internal Server Error (server-side error)

## Example Error Handling

```javascript
try {
  const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: 'user_123',
      message: 'Hello'
    })
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.detail);
    // Handle error (show to user, retry, etc.)
    return;
  }

  const data = await response.json();
  // Handle success
} catch (error) {
  console.error('Network error:', error);
  // Handle network error
}
```

---

# 📝 Common Request Patterns

## TypeScript/JavaScript Helper Functions

```typescript
const API_BASE_URL = 'https://scbackend-qfh6.onrender.com';

// Process message
async function processMessage(userId: string, message: string, location?: string) {
  const response = await fetch(`${API_BASE_URL}/api/orchestrator/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      message: message,
      location: location
    })
  });
  return response.json();
}

// Process Singlish
async function processSinglish(userId: string, transcript: string) {
  const response = await fetch(`${API_BASE_URL}/api/orchestrator/process-singlish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      transcript: transcript
    })
  });
  return response.json();
}

// Create reminder
async function createReminder(
  userId: string,
  title: string,
  reminderType: string,
  scheduledTime: string,
  description?: string
) {
  const response = await fetch(`${API_BASE_URL}/api/wellness/reminders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      title: title,
      description: description,
      reminder_type: reminderType,
      scheduled_time: scheduledTime
    })
  });
  return response.json();
}
```

---

# 🚀 Quick Start Examples

## Example 1: Send a message and get automatic action

```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    message: 'I want to join the pickleball tournament'
  })
});

const result = await response.json();
if (result.action_executed) {
  console.log('Success!', result.message);
  // User is now registered for the event
}
```

## Example 2: Translate Singlish

```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/orchestrator/process-singlish', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    transcript: 'walao this uncle cut queue sia'
  })
});

const result = await response.json();
console.log('Original:', result.singlish_raw);
console.log('English:', result.clean_english);
console.log('Sentiment:', result.sentiment);
console.log('Tone:', result.tone);
```

## Example 3: Create a health reminder

```javascript
const response = await fetch('https://scbackend-qfh6.onrender.com/api/wellness/reminders', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    title: 'Take vitamins',
    reminder_type: 'medication',
    scheduled_time: new Date('2024-12-25T10:00:00Z').toISOString()
  })
});

const result = await response.json();
console.log('Reminder created:', result.reminder);
```

---

# 📋 Summary

## Orchestrator Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orchestrator/` | Get orchestrator info |
| POST | `/api/orchestrator/message` | Process text message (auto-executes actions) |
| POST | `/api/orchestrator/voice` | Process voice transcript (auto-executes actions) |
| POST | `/api/orchestrator/process-singlish` | Translate Singlish + analyze sentiment |
| GET | `/api/orchestrator/history/{user_id}` | Get conversation history |
| GET | `/api/orchestrator/test-route` | Test endpoint |

## Wellness Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wellness/` | Get wellness info |
| GET | `/api/wellness/reminders/{user_id}` | Get user reminders |
| POST | `/api/wellness/reminders` | Create reminder |
| GET | `/api/wellness/analytics/{user_id}` | Get user analytics |

---

# 🔗 Additional Resources

- **API Documentation (Interactive)**: `https://scbackend-qfh6.onrender.com/docs`
- **Alternative Docs**: `https://scbackend-qfh6.onrender.com/redoc`
- **Health Check**: `https://scbackend-qfh6.onrender.com/health`

---

**Last Updated**: December 2024  
**API Version**: 2.0.0

