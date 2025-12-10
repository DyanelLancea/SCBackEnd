# SC Backend Architecture Overview

## 📋 Quick Answers to Your Questions

### ❓ Does `/api/voice/conversation` endpoint exist in your backend?
**Answer:** ❌ **NO** - This endpoint does not exist.

### ❓ What endpoints DO exist?
```
✅ /api/orchestrator/message      - Process text messages & detect intent
✅ /api/orchestrator/history/{id} - Get conversation history
✅ /api/events/*                  - Event management
✅ /api/safety/sos                - Emergency SOS
✅ /api/wellness/*                - Wellness features
```

### ❓ What's the intended flow?
**Answer:** **Option A** is the recommended approach:

```
Voice Input (Frontend)
    ↓
Speech-to-Text (Browser/Deepgram)
    ↓
Text Message
    ↓
POST /api/orchestrator/message
    ↓
Intent Detection
    ↓
Route to appropriate agent
```

### ❓ Should the voice button use orchestrator endpoints?
**Answer:** ✅ **YES** - Here's how:

1. **Frontend captures voice** → Speech-to-Text transcription
2. **Send transcribed text** → `/api/orchestrator/message`
3. **Orchestrator detects intent** → Routes to appropriate service
4. **NO BACKEND CHANGES NEEDED** ✅

---

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                     (React/Next.js)                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Text Input   │  │ Voice Input  │  │ Emergency Button│  │
│  │ (Keyboard)   │  │ (Microphone) │  │ (SOS)          │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│         │                  │                    │           │
│         │           ┌──────▼───────┐           │           │
│         │           │ Web Speech   │           │           │
│         │           │ API / Deep-  │           │           │
│         │           │ gram STT     │           │           │
│         │           └──────┬───────┘           │           │
│         │                  │                    │           │
│         └─────────┬────────┘                    │           │
│                   │ "What events are           │           │
│                   │  happening?"                │           │
└───────────────────┼─────────────────────────────┼───────────┘
                    │                             │
                    │ HTTP POST                   │ HTTP POST
                    │                             │
┌───────────────────▼─────────────────────────────▼───────────┐
│                    BACKEND API                               │
│                  (FastAPI Python)                            │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATOR AGENT                       │  │
│  │         (Main Coordinator & Router)                   │  │
│  │                                                        │  │
│  │  POST /api/orchestrator/message                       │  │
│  │  {                                                     │  │
│  │    user_id: "123",                                     │  │
│  │    message: "What events are happening?"              │  │
│  │  }                                                     │  │
│  │                                                        │  │
│  │  ┌─────────────────────────────────────┐             │  │
│  │  │  Intent Detection Engine            │             │  │
│  │  │  (Keyword matching - upgradeable)   │             │  │
│  │  └─────────────┬───────────────────────┘             │  │
│  │                │                                       │  │
│  │    ┌───────────┼───────────┬──────────────┐          │  │
│  │    │           │           │              │          │  │
│  └────┼───────────┼───────────┼──────────────┼──────────┘  │
│       │           │           │              │             │
│   ┌───▼────┐  ┌──▼──────┐ ┌──▼────────┐ ┌──▼─────────┐   │
│   │ EVENTS │  │ SAFETY  │ │ WELLNESS  │ │ GENERAL    │   │
│   │ AGENT  │  │ AGENT   │ │ AGENT     │ │ RESPONSE   │   │
│   └───┬────┘  └──┬──────┘ └──┬────────┘ └──┬─────────┘   │
│       │          │            │              │             │
└───────┼──────────┼────────────┼──────────────┼─────────────┘
        │          │            │              │
        │          │            │              │
┌───────▼──────────▼────────────▼──────────────▼─────────────┐
│                   SUPABASE DATABASE                         │
│                    (PostgreSQL)                             │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ events   │  │ sos_logs │  │ reminders │  │ location │ │
│  │ table    │  │ table    │  │ table     │  │ _logs    │ │
│  └──────────┘  └──────────┘  └───────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Detailed Flow Examples

### Example 1: Voice → Events

```
1. USER SPEAKS: "What events are happening this weekend?"
   ↓
2. FRONTEND (Web Speech API):
   - Captures audio
   - Transcribes to text
   - Result: "What events are happening this weekend?"
   ↓
3. SEND TO BACKEND:
   POST /api/orchestrator/message
   {
     "user_id": "user_123",
     "message": "What events are happening this weekend?"
   }
   ↓
4. ORCHESTRATOR:
   - Detects keyword: "events"
   - Intent: "find_events"
   - Returns: {
       "success": true,
       "intent": "find_events",
       "message": "Looking for events! Check /api/events/list..."
     }
   ↓
5. FRONTEND ROUTING:
   - Receives intent: "find_events"
   - Calls: GET /api/events/list?date_filter=upcoming
   - Displays events to user
```

---

### Example 2: Voice → Emergency

```
1. USER SPEAKS: "Help! Emergency!"
   ↓
2. FRONTEND (Web Speech API):
   - Transcribes to: "Help! Emergency!"
   ↓
3. SEND TO BACKEND:
   POST /api/orchestrator/message
   {
     "user_id": "user_456",
     "message": "Help! Emergency!"
   }
   ↓
4. ORCHESTRATOR:
   - Detects keywords: "help", "emergency"
   - Intent: "emergency"
   - Returns: {
       "success": true,
       "intent": "emergency",
       "message": "Emergency detected! Check /api/safety/emergency..."
     }
   ↓
5. FRONTEND ROUTING:
   - Receives intent: "emergency"
   - Shows emergency modal
   - Calls: POST /api/safety/sos
   - Triggers emergency protocol
```

---

## 📦 Current Backend Modules

### 1. **Orchestrator Agent** 🤖
**Location:** `app/orchestrator/routes.py`  
**Purpose:** Main coordinator and intelligent router

**Endpoints:**
- `GET /api/orchestrator/` - Module info
- `POST /api/orchestrator/message` - Process messages
- `GET /api/orchestrator/history/{user_id}` - Get history

**Intent Detection:**
- `find_events` - Keywords: "event", "activity", "happening"
- `emergency` - Keywords: "help", "emergency", "sos"
- `general` - Default for everything else

---

### 2. **Events Agent** 📅
**Location:** `app/events/routes.py`  
**Purpose:** Event management and registration

**Endpoints:**
- `GET /api/events/list` - List all events
- `GET /api/events/{event_id}` - Get specific event
- `POST /api/events/create` - Create new event
- `PUT /api/events/{event_id}` - Update event
- `DELETE /api/events/{event_id}` - Delete event
- `POST /api/events/register` - Register for event
- `GET /api/events/{event_id}/participants` - Get participants

---

### 3. **Safety Agent** 🚨
**Location:** `app/safety/routes.py`  
**Purpose:** Emergency response and location tracking

**Endpoints:**
- `POST /api/safety/sos` - Trigger emergency (calls Twilio)
- `POST /api/safety/location` - Update user location
- `GET /api/safety/status/{user_id}` - Get safety status

**Features:**
- Twilio integration for emergency calls
- GPS location logging
- Caregiver notification

---

### 4. **Wellness Agent** 💪
**Location:** `app/wellness/routes.py`  
**Purpose:** Health management and social engagement

**Endpoints:**
- `GET /api/wellness/reminders/{user_id}` - Get reminders
- `POST /api/wellness/reminders` - Create reminder
- `GET /api/wellness/analytics/{user_id}` - Get analytics

---

## 🔄 Data Flow Diagram

### Text Input Flow
```
Keyboard → Text → Orchestrator → Intent → Route to Agent
```

### Voice Input Flow (Recommended)
```
Microphone → Audio → STT (Frontend) → Text → Orchestrator → Intent → Route to Agent
```

### Alternative Voice Flow (NOT Implemented)
```
Microphone → Audio → Backend STT → Text → Orchestrator → Intent → Route to Agent
                      ↑
                  NOT IMPLEMENTED
```

---

## 🎨 Frontend Integration Pattern

```typescript
// 1. Setup voice input hook
const { transcript, startListening, stopListening } = useVoiceInput();

// 2. Setup orchestrator hook
const { sendMessage } = useOrchestrator(userId);

// 3. When user speaks
const handleVoiceInput = async () => {
  startListening(); // Start recording
  
  // Wait for transcription...
  // transcript automatically updates
  
  // Send to orchestrator
  const response = await sendMessage(transcript);
  
  // Handle intent
  switch (response.intent) {
    case 'find_events':
      router.push('/events');
      break;
    case 'emergency':
      triggerEmergency();
      break;
    case 'general':
      showResponse(response.message);
      break;
  }
};
```

---

## 🛠️ What You Need to Implement

### Backend (NO CHANGES NEEDED) ✅
Your current orchestrator already handles everything!

### Frontend (Implement This) 📱
1. ✅ Voice capture (Web Speech API / Deepgram)
2. ✅ Speech-to-Text conversion
3. ✅ Send transcribed text to `/api/orchestrator/message`
4. ✅ Handle intent-based routing
5. ✅ Display responses

**All code provided in:** `VOICE_INTEGRATION_GUIDE.md`

---

## 📊 Technology Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **External Services:**
  - Twilio (Emergency calls)
  - (Future: OpenAI for better NLP)

### Frontend (Recommended)
- **Framework:** React / Next.js
- **Voice Input:** Web Speech API (free) or Deepgram (premium)
- **API Client:** Fetch API / Axios
- **State Management:** React Hooks

---

## 🚀 Implementation Checklist

### Phase 1: Basic Voice (No Backend Changes)
- [ ] Add Web Speech API hook (`useVoiceInput.ts`)
- [ ] Create voice button component
- [ ] Connect to orchestrator endpoint
- [ ] Test with simple phrases
- [ ] Add error handling

### Phase 2: Enhanced Experience
- [ ] Add visual feedback (waveforms)
- [ ] Implement loading states
- [ ] Add conversation history display
- [ ] Improve intent-based routing
- [ ] Add voice output (TTS)

### Phase 3: Advanced Features (Optional)
- [ ] Upgrade to Deepgram for better accuracy
- [ ] Add multi-language support
- [ ] Implement conversation context
- [ ] Add voice commands
- [ ] Analytics tracking

---

## 🎯 Recommended Approach

### Option A: Frontend STT (Recommended) ⭐
**Pros:**
- ✅ No backend changes needed
- ✅ Faster (client-side processing)
- ✅ Lower server costs
- ✅ Works with existing orchestrator
- ✅ Easier to implement

**Cons:**
- ⚠️ Requires HTTPS in production
- ⚠️ Browser compatibility varies

### Option B: Backend Voice Module (Future)
**Pros:**
- ✅ Centralized audio processing
- ✅ Better analytics
- ✅ More control over STT service

**Cons:**
- ❌ Requires new backend module
- ❌ Need to handle audio uploads
- ❌ Higher server costs
- ❌ More complexity

---

## 📞 Integration Summary

### What Frontend Needs to Do:

1. **Capture voice** using Web Speech API
2. **Get transcript** from the API
3. **Send transcript** to `/api/orchestrator/message`
4. **Receive intent** from orchestrator
5. **Route user** based on intent

### What Backend Already Does:

1. ✅ Receives text messages
2. ✅ Detects intent
3. ✅ Returns routing suggestions
4. ✅ Handles all business logic

**No backend changes needed!** 🎉

---

## 📚 Documentation Files

- **`ORCHESTRATOR_FRONTEND_GUIDE.md`** - Complete orchestrator API docs
- **`VOICE_INTEGRATION_GUIDE.md`** - Voice implementation guide (this file)
- **`ARCHITECTURE_OVERVIEW.md`** - System architecture overview
- **`test_orchestrator.py`** - Backend testing script

---

## 🆘 Need Help?

### Questions About:
- **Architecture** → See this file
- **API Integration** → See `ORCHESTRATOR_FRONTEND_GUIDE.md`
- **Voice Implementation** → See `VOICE_INTEGRATION_GUIDE.md`
- **Testing** → Run `python test_orchestrator.py`

### Test Your Integration:
1. Start backend: `uvicorn app.main:app --reload`
2. Test API: `python test_orchestrator.py`
3. Check docs: http://localhost:8000/docs

---

**Last Updated:** December 10, 2025  
**Version:** 2.0.0  
**Status:** Production Ready

