# Endpoint Data Input Guide

This document explains the expected data input for each endpoint related to the four main activities.

## Overview

All four activities use the same primary endpoints:
- **Text Messages**: `POST /api/orchestrator/message`
- **Voice Messages**: `POST /api/orchestrator/voice`

The system automatically detects the intent from the user's message and routes to the appropriate action.

---

## 1. Book a Specific Event

### Endpoint
```
POST /api/orchestrator/message
POST /api/orchestrator/voice
```

### Request Model

#### For Text Messages (`TextMessage`):
```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "location": "string (optional)"
}
```

#### For Voice Messages (`VoiceMessage`):
```json
{
  "user_id": "string (required)",
  "transcript": "string (optional, recommended)",
  "audio": "string (optional, base64 encoded)",
  "location": "string (optional)"
}
```

### Expected Input Examples

#### ✅ **Good Examples (Specific Event Name):**
```json
{
  "user_id": "user-123",
  "message": "I want to book the Pickleball Tournament"
}
```

```json
{
  "user_id": "user-123",
  "message": "Register me for yoga class"
}
```

```json
{
  "user_id": "user-123",
  "message": "Sign me up for the workout session on December 20th"
}
```

#### ✅ **Good Examples (Event ID - if known):**
```json
{
  "user_id": "user-123",
  "message": "Book event abc123-def456-ghi789"
}
```

#### ⚠️ **Current Issue - Ambiguous Input:**
```json
{
  "user_id": "user-123",
  "message": "I want to book an event"
}
```
**Problem**: If no specific event name is mentioned, the system may default to the latest event.

### How It Works

1. **Intent Detection**: The system uses GROQ (Llama 3.1) to detect `book_event` or `register_event` intent
2. **Event Extraction**: Extracts `event_name` and/or `event_id` from the message
3. **Event Matching**: Uses `find_event_by_name_or_id()` to match the event:
   - First tries to match by `event_id` (if provided and valid UUID)
   - Then tries to match by `event_name` (case-insensitive, partial matching)
   - Uses scoring algorithm (60% threshold) to find best match
4. **Registration**: Calls `POST /api/events/register` with matched event

### Required Fields
- `user_id`: **Required** - User identifier (string)
- `message`: **Required** - User's text message (string)
- `transcript`: **Required for voice** - Transcribed text (string)
- `location`: **Optional** - User's location (string)

### Response Structure
```json
{
  "success": true,
  "intent": "book_event",
  "message": "Successfully registered you for 'Event Name'!",
  "user_id": "user-123",
  "action_executed": true,
  "action_result": {
    "booking_confirmed": true,
    "event_details": { ... },
    "navigation": {
      "action": "navigate_to_booking_confirmation",
      "route": "/events/booking/confirmation",
      "event_id": "uuid-here",
      "should_navigate": true
    }
  }
}
```

### Important Notes
- **Event Name Matching**: The system uses fuzzy matching, so partial names work (e.g., "pickleball" matches "Pickleball Tournament")
- **Event ID Format**: Must be a valid UUID (36 characters with hyphens)
- **Current Limitation**: If no event name/ID is detected, it may default to the latest event

---

## 2. Unregister from Events

### Endpoint
```
POST /api/orchestrator/message
POST /api/orchestrator/voice
```

### Request Model

Same as Booking - uses `TextMessage` or `VoiceMessage`:

```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "location": "string (optional)"
}
```

### Expected Input Examples

#### ✅ **Good Examples:**
```json
{
  "user_id": "user-123",
  "message": "Cancel my registration for Pickleball Tournament"
}
```

```json
{
  "user_id": "user-123",
  "message": "Unregister me from yoga class"
}
```

```json
{
  "user_id": "user-123",
  "message": "Remove me from the workout event"
}
```

#### ⚠️ **Ambiguous Input:**
```json
{
  "user_id": "user-123",
  "message": "Cancel my event"
}
```
**Problem**: If no specific event name is mentioned, the system may not find the correct event.

### How It Works

1. **Intent Detection**: Detects `cancel_event` or `unregister_event` intent
2. **Event Extraction**: Extracts `event_name` and/or `event_id` from the message
3. **Event Matching**: Uses `find_event_by_name_or_id()` to find the specific event
4. **Unregistration**: Calls `DELETE /api/events/register/{event_id}/{user_id}`

### Required Fields
- `user_id`: **Required** - User identifier (string)
- `message`: **Required** - User's text message (string)

### Response Structure
```json
{
  "success": true,
  "intent": "cancel_event",
  "message": "Successfully unregistered you from 'Event Name'.",
  "user_id": "user-123",
  "action_executed": true,
  "action_result": {
    "event_id": "uuid-here",
    "user_id": "user-123"
  }
}
```

### Error Cases
- **Event Not Found**: Returns message with suggestions
- **Not Registered**: Returns "You're not currently registered for this event"
- **Invalid Event ID**: Returns "System error: Invalid event ID"

---

## 3. Check Details of an Event

### Endpoint
```
POST /api/orchestrator/message
POST /api/orchestrator/voice
```

### Request Model

Same as Booking - uses `TextMessage` or `VoiceMessage`:

```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "location": "string (optional)"
}
```

### Expected Input Examples

#### ✅ **Good Examples:**
```json
{
  "user_id": "user-123",
  "message": "Tell me about the Pickleball Tournament"
}
```

```json
{
  "user_id": "user-123",
  "message": "What are the details of the yoga class?"
}
```

```json
{
  "user_id": "user-123",
  "message": "Show me information about the workout session"
}
```

#### ⚠️ **Ambiguous Input:**
```json
{
  "user_id": "user-123",
  "message": "What events are there?"
}
```
**Note**: This would trigger `list_events` intent instead of `get_event`.

### How It Works

1. **Intent Detection**: Detects `get_event` intent
2. **Event Extraction**: Extracts `event_name` and/or `event_id` from the message
3. **Event Matching**: Uses `find_event_by_name_or_id()` to find the specific event
4. **Fetch Details**: Calls `GET /api/events/{event_id}` to get full event details

### Required Fields
- `user_id`: **Required** - User identifier (string)
- `message`: **Required** - User's text message (string)

### Response Structure
```json
{
  "success": true,
  "intent": "get_event",
  "message": "📅 Event Title\n\nDate: 2024-12-20 at 10:00\nLocation: Community Center\n\nDescription: ...",
  "user_id": "user-123",
  "action_executed": true,
  "action_result": {
    "event": {
      "id": "uuid-here",
      "title": "Event Title",
      "date": "2024-12-20",
      "time": "10:00",
      "location": "Community Center",
      "description": "...",
      "max_participants": 50
    }
  }
}
```

### Event Details Included
- Event title
- Date and time
- Location
- Description
- Maximum participants (if set)

---

## 4. Answer General Questions

### Endpoint
```
POST /api/orchestrator/message
POST /api/orchestrator/voice
```

### Request Model

Same as other activities - uses `TextMessage` or `VoiceMessage`:

```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "location": "string (optional)"
}
```

### Expected Input Examples

#### ✅ **Good Examples:**
```json
{
  "user_id": "user-123",
  "message": "What can this app do?"
}
```

```json
{
  "user_id": "user-123",
  "message": "How do I use this platform?"
}
```

```json
{
  "user_id": "user-123",
  "message": "What features are available?"
}
```

```json
{
  "user_id": "user-123",
  "message": "Tell me about the community center"
}
```

### How It Works

1. **Intent Detection**: Detects `general` intent (when no other intent matches)
2. **Context Gathering**: Fetches available events for context (optional)
3. **GPT Response**: Uses OpenAI GPT-4 (or GPT-3.5-turbo) to generate helpful answer
4. **Response**: Returns AI-generated answer

### Required Fields
- `user_id`: **Required** - User identifier (string)
- `message`: **Required** - User's question (string)

### Response Structure
```json
{
  "success": true,
  "intent": "general",
  "message": "I can help you with:\n• Booking events (say 'book event' or 'register for event')\n• Viewing events (say 'show events' or 'list events')\n• Getting event details (say 'tell me about [event name]')\n• Canceling events (say 'cancel [event name]')\n• Emergency help (say 'help' or 'emergency')\n• And more! What would you like to do?",
  "user_id": "user-123",
  "action_executed": true
}
```

### Fallback Behavior
If OpenAI API is not available, returns a default helpful message listing available features.

---

## Common Request Models

### TextMessage Model
```python
class TextMessage(BaseModel):
    user_id: str          # Required: User identifier
    message: str          # Required: User's text message
    location: Optional[str] = None  # Optional: User's location
```

### VoiceMessage Model
```python
class VoiceMessage(BaseModel):
    user_id: str          # Required: User identifier
    transcript: Optional[str] = None  # Recommended: Pre-transcribed text
    audio: Optional[str] = None      # Optional: Base64 encoded audio
    location: Optional[str] = None     # Optional: User's location
```

**Note**: For voice messages, `transcript` is recommended (frontend speech-to-text). If `audio` is provided, it requires `OPENAI_API_KEY` for Whisper transcription.

---

## Intent Detection Details

The system uses **GROQ (Llama 3.1)** for intent detection. The prompt includes:

### Supported Intents:
1. `emergency` - Emergency help/SOS
2. `book_event` / `register_event` - Register for a specific event
3. `list_events` - List available events
4. `get_event` - Get details about a specific event
5. `cancel_event` / `unregister_event` - Cancel/unregister from a specific event
6. `update_location` - Update user location
7. `general` - General questions/conversation

### Event Extraction Rules:
- **event_name**: Extracted from user message (e.g., "pickleball", "yoga class")
- **event_id**: Only used if it matches a UUID from available events list
- **Matching**: Uses fuzzy matching with 60% threshold
- **Validation**: Event IDs must be valid UUIDs (36 characters with hyphens)

---

## Best Practices

### ✅ **DO:**
- Include specific event names in messages: "book Pickleball Tournament"
- Use clear, descriptive event names
- Provide `user_id` in all requests
- Use `transcript` for voice messages (faster, more reliable)

### ❌ **DON'T:**
- Send ambiguous messages like "book event" without specifying which event
- Use invalid UUID formats for event IDs
- Omit `user_id` (required field)
- Send empty messages

---

## Troubleshooting

### Issue: "Connection error: Could not reach backend API"
**Cause**: `API_BASE_URL` environment variable not set in production
**Solution**: 
- Set `API_BASE_URL` to your backend's public URL (e.g., `https://scbackend-qfh6.onrender.com`)
- **Important**: Do NOT include `/api` in the URL - just the base URL!
- See `API_BASE_URL_FIX.md` for detailed instructions
- After setting, redeploy your service

### Issue: "Only books the latest event"
**Cause**: Event name not extracted or not matching any events
**Solution**: 
- Ensure event name is mentioned in the message
- Check that event exists in database
- Verify event name spelling matches (case-insensitive, partial matching works)

### Issue: "Event not found"
**Cause**: Event name doesn't match any events
**Solution**:
- Check available events: `GET /api/events/list`
- Use exact or partial event name from the list
- System will suggest similar events if close match found

### Issue: "Intent detection fails"
**Cause**: GROQ_API_KEY not set or invalid
**Solution**:
- Set `GROQ_API_KEY` in environment variables
- System falls back to keyword detection if GROQ unavailable

### Issue: Intent is `register_event` instead of `book_event`
**Note**: This is **not a problem**! Both intents are treated identically by the code. The system handles both `book_event` and `register_event` the same way.

---

## Direct API Endpoints (Alternative)

If you want to bypass intent detection, you can call these endpoints directly:

### Book Event (Direct)
```
POST /api/events/register
Body: {
  "event_id": "uuid-here",
  "user_id": "user-123"
}
```

### Unregister (Direct)
```
DELETE /api/events/register/{event_id}/{user_id}
```

### Get Event Details (Direct)
```
GET /api/events/{event_id}
```

### List Events (Direct)
```
GET /api/events/list?limit=10
```

---

## Summary Table

| Activity | Intent | Required Fields | Event Identification |
|----------|--------|----------------|---------------------|
| **Book Event** | `book_event` | `user_id`, `message` | `event_name` or `event_id` in message |
| **Unregister** | `cancel_event` | `user_id`, `message` | `event_name` or `event_id` in message |
| **Get Details** | `get_event` | `user_id`, `message` | `event_name` or `event_id` in message |
| **General Q&A** | `general` | `user_id`, `message` | N/A |

**Key Point**: All activities use the same endpoint (`/api/orchestrator/message` or `/api/orchestrator/voice`). The system automatically detects the intent and extracts event information from the message text.

