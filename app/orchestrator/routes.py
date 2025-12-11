"""
Orchestrator Routes
Main coordinator and request routing
Includes Singlish-to-English translation with sentiment analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import httpx
import json
import os
import re
import tempfile
from app.shared.supabase import get_supabase_client


def get_api_base_url() -> str:
    """
    Get the API base URL for internal service calls.
    Tries to auto-detect from environment or use sensible defaults.
    """
    # First, check if explicitly set
    api_url = os.getenv("API_BASE_URL")
    if api_url:
        return api_url.rstrip('/')
    
    # Try to detect from RENDER environment (Render.com)
    render_service_url = os.getenv("RENDER_SERVICE_URL")
    if render_service_url:
        return render_service_url.rstrip('/')
    
    # Try to detect from RENDER_EXTERNAL_URL (Render.com sets this)
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_external_url:
        return render_external_url.rstrip('/')
    
    # Try to detect from other common environment variables
    # For Vercel/other platforms that might set this
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        return f"https://{vercel_url}".rstrip('/')
    
    # Try to detect from request context (if available)
    # This is a fallback for when we're running in production but env vars aren't set
    # We can infer from common production patterns
    
    # Check if we're in production (common indicators)
    is_production = (
        os.getenv("ENVIRONMENT") == "production" or 
        os.getenv("PRODUCTION") == "true" or
        os.getenv("RENDER") == "true" or  # Render.com sets this
        "render.com" in os.getenv("RENDER_SERVICE_URL", "").lower() or
        "render.com" in os.getenv("RENDER_EXTERNAL_URL", "").lower()
    )
    
    # Default fallback - use localhost for development
    # In production, this should be set via API_BASE_URL
    if is_production:
        # In production without API_BASE_URL set, we can't make internal calls
        # This will cause an error, but at least it's clear
        raise ValueError(
            "API_BASE_URL environment variable must be set in production. "
            "Set it to your backend's public URL (e.g., https://your-backend.onrender.com). "
            "Note: Do NOT include /api in the URL - just the base URL."
        )
    
    return "http://localhost:8000"


router = APIRouter()

# Initialize OpenAI client lazily (only when needed)
def get_openai_client():
    """Get OpenAI client, initializing if needed"""
    try:
        from openai import OpenAI
    except ImportError:
        # Return 400 instead of 500 to avoid triggering frontend error detection
        raise HTTPException(
            status_code=400,
            detail="Audio transcription requires OpenAI package. Please provide 'transcript' field instead (use frontend speech-to-text)."
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Return 400 instead of 500 to avoid triggering frontend error detection
        raise HTTPException(
            status_code=400,
            detail="Audio transcription requires OPENAI_API_KEY. Please provide 'transcript' field instead (use frontend speech-to-text)."
        )
    return OpenAI(api_key=api_key)


# Initialize GROQ client lazily (only when needed)
def get_groq_client():
    """Get GROQ client for fast intent detection"""
    try:
        from groq import Groq
    except ImportError:
        raise HTTPException(
            status_code=400,
            detail="Intent detection requires GROQ package. Install with: pip install groq"
        )
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Intent detection requires GROQ_API_KEY environment variable."
        )
    return Groq(api_key=api_key)


# ==================== REQUEST MODELS ====================

class TextMessage(BaseModel):
    """Text message from user"""
    user_id: str
    message: str
    location: Optional[str] = None  # Optional location from voice/message


class VoiceMessage(BaseModel):
    """Voice recording message from user"""
    user_id: str
    transcript: Optional[str] = None  # Transcribed text from voice recording (if frontend did transcription)
    audio: Optional[str] = None  # Base64 encoded audio (if frontend sends raw audio)
    location: Optional[str] = None  # Optional location


class SinglishProcessRequest(BaseModel):
    """Request for Singlish processing with audio or transcript"""
    user_id: str
    audio: Optional[str] = None  # Base64 encoded audio
    transcript: Optional[str] = None  # Direct text transcript


# ==================== ENDPOINTS ====================

@router.get("/")
def orchestrator_info():
    """Get information about the Orchestrator module"""
    # Voice processing is always available with transcripts (frontend speech-to-text)
    # Audio transcription (backend Whisper) requires OPENAI_API_KEY
    audio_transcription_available = False
    intent_detection_available = False
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            audio_transcription_available = True
    except:
        pass
    
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            intent_detection_available = True
    except:
        pass
    
    return {
        "module": "Orchestrator",
        "description": "Main coordinator and request routing agent",
        "capabilities": [
            "Natural language understanding",
            "Intent classification (GROQ-powered for speed)",
            "Request routing to specialized modules",
            "Conversation management",
            "Voice message processing",
            "Automatic action execution"
        ],
        "endpoints": {
            "message": "/api/orchestrator/message",
            "voice": "/api/orchestrator/voice",
            "process_singlish": "/api/orchestrator/process-singlish",
            "history": "/api/orchestrator/history/{user_id}"
        },
        "status": "ready",
        "voice_processing_available": True,  # Always available with transcript-based processing
        "audio_transcription_available": audio_transcription_available,  # Requires OPENAI_API_KEY
        "intent_detection_available": intent_detection_available,  # Requires GROQ_API_KEY
        "intent_detection_note": "Intent detection uses GROQ (Llama 3.1) for ultra-fast inference. Requires GROQ_API_KEY.",
        "voice_processing_note": "Voice processing works with transcripts (frontend speech-to-text). Audio transcription requires OPENAI_API_KEY."
    }


def detect_emergency_intent(text: str) -> bool:
    """
    Detect if message contains emergency intent keywords
    """
    message_lower = text.lower()
    emergency_keywords = [
        "emergency", "sos", "help", "urgent", "danger", "accident",
        "injured", "hurt", "pain", "need help", "call help", "assistance",
        "rescue", "ambulance", "hospital", "911", "999"
    ]
    return any(keyword in message_lower for keyword in emergency_keywords)


def validate_and_get_uuid(value: Any) -> Optional[str]:
    """
    Safely validate and return a UUID string, or None if invalid.
    This function ensures we NEVER use non-UUID values like "1".
    """
    if not value:
        return None
    
    value_str = str(value).strip()
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    # Strict validation: must be exactly 36 chars with 4 hyphens
    if (uuid_pattern.match(value_str) and 
        len(value_str) == 36 and 
        value_str.count('-') == 4):
        return value_str
    
    # Reject anything that's not a valid UUID (including "1", numbers, etc.)
    return None


def find_event_by_name_or_id(events: list, event_name: Optional[str] = None, event_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find an event by name or ID with improved matching logic.
    Returns the best matching event or None.
    
    Args:
        events: List of event dictionaries
        event_name: Event name to search for (case-insensitive, partial matching)
        event_id: Event ID (UUID) to search for
    
    Returns:
        Event dictionary if found, None otherwise
    """
    if not events:
        return None
    
    # First, try to find by ID if provided and valid
    if event_id:
        validated_id = validate_and_get_uuid(event_id)
        if validated_id:
            for event in events:
                event_uuid = validate_and_get_uuid(event.get("id"))
                if event_uuid and event_uuid == validated_id:
                    return event
    
    # If no ID match and no name provided, return None
    if not event_name:
        return None
    
    # Normalize search name (remove extra spaces, lowercase, remove punctuation)
    normalized_search = re.sub(r'[\s\-_]+', ' ', event_name.lower().strip())
    normalized_search = re.sub(r'[^\w\s]', '', normalized_search)
    # Remove common articles and prepositions at the start
    normalized_search = re.sub(r'^(the|a|an)\s+', '', normalized_search, flags=re.IGNORECASE).strip()
    # Filter out short words and common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    search_words = [w for w in normalized_search.split() if len(w) > 2 and w not in stop_words]
    
    if not search_words:
        return None
    
    best_match = None
    best_score = 0.0
    
    for event in events:
        # Validate event has valid UUID
        event_uuid = validate_and_get_uuid(event.get("id"))
        if not event_uuid:
            continue
        
        event_title = event.get("title", "").strip()
        if not event_title:
            continue
        
        # Normalize event title
        normalized_title = re.sub(r'[\s\-_]+', ' ', event_title.lower().strip())
        normalized_title = re.sub(r'[^\w\s]', '', normalized_title)
        title_words = normalized_title.split()
        
        # Calculate match score
        score = 0.0
        
        # Strategy 1: Exact normalized match (highest priority)
        if normalized_search == normalized_title:
            score = 1.0
        # Strategy 2: All search words found in title (high priority)
        elif all(any(search_word in title_word or title_word in search_word for title_word in title_words) for search_word in search_words):
            matched_words = sum(1 for search_word in search_words 
                              if any(search_word in title_word or title_word in search_word for title_word in title_words))
            score = matched_words / len(search_words)
        # Strategy 3: Substring match
        elif normalized_search in normalized_title or normalized_title in normalized_search:
            # Calculate how much of the search string matches
            if normalized_search in normalized_title:
                score = len(normalized_search) / len(normalized_title)
            else:
                score = len(normalized_title) / len(normalized_search)
        # Strategy 4: Word overlap (partial match)
        else:
            matched_words = sum(1 for search_word in search_words 
                              if any(search_word in title_word or title_word in search_word for title_word in title_words))
            if matched_words > 0:
                score = matched_words / max(len(search_words), len(title_words))
        
        # Prefer matches with higher scores
        if score > best_score:
            best_score = score
            best_match = event
    
    # Only return match if score is above threshold (60% match)
    if best_match and best_score >= 0.6:
        return best_match
    
    return None


async def detect_intent_and_extract_info(user_message: str, user_id: str) -> Dict[str, Any]:
    """
    Use GROQ (Llama 3.1) to intelligently detect user intent and extract relevant information
    Returns intent type and extracted parameters
    Falls back to simple keyword detection if GROQ is not available
    """
    try:
        # Try to get GROQ client - if not available, fall back to keyword detection
        try:
            client = get_groq_client()
        except HTTPException:
            # GROQ not available - fall through to keyword detection
            raise Exception("GROQ not available - using fallback")
        
        # Get available events to help GPT understand context
        available_events = []
        try:
            base_url = get_api_base_url()
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                events_response = await http_client.get(f"{base_url}/api/events/list?limit=10")
                if events_response.status_code == 200:
                    events_data = events_response.json()
                    available_events = events_data.get("events", [])
        except (httpx.ConnectError, httpx.ConnectTimeout, ValueError) as e:
            # Connection failed - log but continue without events context
            print(f"Warning: Could not fetch events for context: {str(e)}")
            pass  # Continue without events if fetch fails
        except Exception as e:
            # Other errors - also continue
            print(f"Warning: Error fetching events: {str(e)}")
            pass
        
        events_context = ""
        if available_events:
            events_list = "\n".join([
                f"- ID: {e.get('id')}, Title: {e.get('title')}, Date: {e.get('date')}"
                for e in available_events[:10]
            ])
            events_context = f"\n\nAvailable Events:\n{events_list}"
        
        prompt = f"""You are an intelligent assistant that understands user requests and extracts actionable information.

User message: "{user_message}"
User ID: {user_id}{events_context}

Analyze the user's intent and extract relevant information. Possible intents:
1. "emergency" - User needs emergency help/SOS (keywords: help, emergency, sos, urgent, danger)
2. "book_event" or "register_event" - User wants to register/book for a SPECIFIC event (keywords: book, register, join, sign up, enroll, attend)
3. "list_events" - User wants to see available events (keywords: list, show, find, what events, available events, upcoming)
4. "get_event" - User wants details about a SPECIFIC event (keywords: details, info, information, tell me about, what is)
5. "cancel_event" or "unregister_event" - User wants to cancel/unregister from a SPECIFIC event (keywords: cancel, unregister, remove, leave, withdraw)
6. "update_location" - User wants to update their location
7. "general" - General conversation, questions, or unclear intent (use this for questions that don't match other intents)

CRITICAL RULES for event-related intents (book_event, get_event, cancel_event, unregister_event):
1. ALWAYS extract the SPECIFIC event name the user mentioned, even if partial
2. event_name: Extract the event name/title from the user's message, REMOVING articles like "the", "a", "an"
   - If user says "join the workout" → extract "workout" (NOT "the workout")
   - If user says "book pickleball" → extract "pickleball"
   - If user says "register for yoga class" → extract "yoga class"
   - Extract the core event name without articles, prepositions, or filler words
3. event_id: ONLY use the exact UUID from the available events list if you can MATCH the event_name to a specific event in the list. Otherwise use null.
4. Match event names intelligently:
   - "pickleball" should match "Pickleball Tournament"
   - "yoga class" should match "Yoga Class for Seniors"
   - "workout" should match "Workout" or "Morning Workout Session"
   - Use partial matching - if user says part of the event name, extract that part
5. DO NOT make up UUIDs or use numbers like "1" - only use actual UUIDs from the events list
6. If user mentions multiple events or is unclear, set event_id to null but still extract event_name
7. IMPORTANT: When extracting event_name, remove leading articles ("the", "a", "an") and common prepositions

For "general" intent:
- Use for questions like "what is this app?", "how do I use this?", "what can you do?"
- Use for general conversation that doesn't match other intents

Respond ONLY with valid JSON (no markdown):
{{
    "intent": "intent_type",
    "event_id": "exact-uuid-from-events-list-or-null",
    "event_name": "extracted-event-name-or-null",
    "event_date": "YYYY-MM-DD-or-null",
    "confidence": 0.0-1.0
}}"""

        try:
            # Use Llama 3.1 70B for intent detection (fast and accurate)
            model = "llama-3.1-70b-versatile"
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an intent detection expert. Always respond with valid JSON only, no markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}  # Force JSON output for better reliability
            )
        except Exception as e:
            # Fallback to Llama 3.1 8B if 70B is unavailable
            try:
                model = "llama-3.1-8b-instant"
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an intent detection expert. Always respond with valid JSON only, no markdown."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
            except Exception as e2:
                # If both fail, raise the original error
                raise e
        
        result_text = response.choices[0].message.content.strip()
        
        # Remove markdown if present (shouldn't happen with response_format, but handle it anyway)
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        # Parse JSON response (GROQ with response_format should return clean JSON)
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from text
            # This handles cases where the model adds extra text
            import re
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from GROQ response: {result_text}")
        
        # If event_id not found but event_name is, try to match with available events
        if result.get("intent") in ["book_event", "register_event", "get_event", "cancel_event", "unregister_event"]:
            if not result.get("event_id") and result.get("event_name") and available_events:
                event_name_lower = result.get("event_name", "").lower()
                for event in available_events:
                    if event_name_lower in event.get("title", "").lower():
                        result["event_id"] = event.get("id")
                        break
        
        return result
        
    except HTTPException:
        # If GROQ is not available (HTTPException from get_groq_client), fall back to keyword detection
        # Don't re-raise HTTPException here - use fallback instead
        pass
    except Exception as e:
        # Other errors - also fall back to keyword detection
        print(f"GROQ intent detection failed: {e}, using keyword fallback")
        pass
    
    # Fallback to simple keyword detection (used when GROQ is not available or fails)
    message_lower = user_message.lower()
    if detect_emergency_intent(user_message):
        return {"intent": "emergency", "confidence": 0.8}
    elif any(word in message_lower for word in ["book", "register", "join", "sign up", "enroll"]):
        return {"intent": "book_event", "confidence": 0.7}
    elif any(word in message_lower for word in ["list", "show", "find", "what events", "available"]):
        return {"intent": "list_events", "confidence": 0.7}
    elif any(word in message_lower for word in ["cancel", "unregister", "remove", "leave"]):
        return {"intent": "cancel_event", "confidence": 0.7}
    else:
        return {"intent": "general", "confidence": 0.5}


@router.post("/message")
async def process_message(request: TextMessage):
    """
    Process a text message from the user
    Routes to appropriate module based on intent
    Automatically executes actions like SOS calls, event booking, etc.
    """
    action_executed = False
    action_result = None
    sos_triggered = False
    message = "Processing your request..."  # Initialize message to avoid NameError
    intent = "general"  # Initialize intent to avoid NameError
    
    # Get API base URL for internal calls
    try:
        base_url = get_api_base_url()
    except ValueError as e:
        # API_BASE_URL not set in production
        return {
            "success": False,
            "intent": "general",
            "message": f"Configuration error: {str(e)}. Please set API_BASE_URL environment variable.",
            "user_id": request.user_id,
            "error": str(e)
        }
    
    # Use GPT to detect intent and extract information
    try:
        intent_data = await detect_intent_and_extract_info(request.message, request.user_id)
        intent = intent_data.get("intent", "general")
    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Fallback to simple detection if GPT fails
        error_msg = str(e)
        print(f"Warning: Intent detection failed, using fallback: {error_msg}")
        if detect_emergency_intent(request.message):
            intent = "emergency"
        else:
            intent = "general"
        intent_data = {"intent": intent}
    
    # Execute actions based on intent
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if intent == "emergency":
                # Automatically trigger SOS call
                sos_response = await client.post(
                    f"{base_url}/api/safety/sos",
                    json={
                        "user_id": request.user_id,
                        "location": request.location,
                        "message": request.message
                    }
                )
                if sos_response.status_code == 200:
                    action_result = sos_response.json()
                    sos_triggered = action_result.get("call_successful", False)
                    message = "Emergency SOS call has been triggered automatically. Help is on the way!"
                    action_executed = True
                else:
                    message = f"Emergency detected, but SOS call failed (HTTP {sos_response.status_code})"
                    action_result = {"error": f"HTTP {sos_response.status_code}"}
            
            elif intent in ["book_event", "register_event"]:
                # Register for event
                event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
                potential_event_id = intent_data.get("event_id")
                
                # Debug logging
                print(f"DEBUG: Intent detection extracted - event_name: '{event_name}', event_id: '{potential_event_id}'")
                
                # Clean up event_name: remove common articles and extra words
                if event_name:
                    # Remove common articles and prepositions at the start
                    event_name_cleaned = re.sub(r'^(the|a|an)\s+', '', event_name, flags=re.IGNORECASE).strip()
                    if event_name_cleaned and event_name_cleaned != event_name:
                        print(f"DEBUG: Cleaned event_name from '{event_name}' to '{event_name_cleaned}'")
                        event_name = event_name_cleaned
                
                # Get available events to search through
                events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
                if events_resp.status_code == 200:
                    events_raw = events_resp.json().get("events", [])
                    # Filter out any events with invalid IDs (safety check)
                    uuid_pattern_filter = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                    events = []
                    for event in events_raw:
                        event_id_check = event.get("id")
                        if event_id_check and uuid_pattern_filter.match(str(event_id_check)) and len(str(event_id_check)) == 36:
                            events.append(event)
                    
                    print(f"DEBUG: Found {len(events)} valid events in database")
                    if events:
                        print(f"DEBUG: Event titles: {[e.get('title') for e in events[:5]]}")
                    
                    # Use improved matching function to find the specific event
                    matched_event = find_event_by_name_or_id(
                        events=events,
                        event_name=event_name if event_name else None,
                        event_id=potential_event_id if potential_event_id else None
                    )
                    
                    if matched_event:
                        print(f"DEBUG: Matched event: '{matched_event.get('title')}' (ID: {matched_event.get('id')[:8]}...)")
                    else:
                        print(f"DEBUG: No event matched for event_name='{event_name}', event_id='{potential_event_id}'")
                    
                    # If no match and user didn't specify an event name, show available events
                    if not matched_event and not event_name:
                        if events:
                            # List available events for user to choose
                            event_list = "\n".join([
                                f"{i+1}. {e.get('title')} - {e.get('date')}"
                                for i, e in enumerate(events[:5])
                            ])
                            message = f"I found {len(events)} events. Please specify which one you'd like to join:\n{event_list}"
                            if len(events) > 5:
                                message += f"\n... and {len(events) - 5} more events."
                            action_result = {"events": events[:10], "count": len(events)}
                            action_executed = True
                        else:
                            message = "No events available to register for."
                    elif not matched_event:
                        # Event name mentioned but not found - provide helpful suggestions
                        if events:
                            # Find similar event names
                            suggestions = []
                            search_lower = event_name.lower() if event_name else ""
                            for event in events[:5]:
                                title_lower = event.get("title", "").lower()
                                if any(word in title_lower for word in search_lower.split() if len(word) > 3):
                                    suggestions.append(event.get("title"))
                            
                            if suggestions:
                                suggestions_text = "\n".join([f"- {s}" for s in suggestions[:3]])
                                message = f"I couldn't find an event matching '{event_name}'. Did you mean one of these?\n{suggestions_text}"
                            else:
                                event_list = "\n".join([f"- {e.get('title')}" for e in events[:3]])
                                message = f"I couldn't find an event matching '{event_name}'. Available events:\n{event_list}"
                        else:
                            message = f"I couldn't find an event matching '{event_name}'. No events are currently available."
                    else:
                        # Found the event - register user
                        event_id_str = validate_and_get_uuid(matched_event.get("id"))
                        if not event_id_str:
                            message = "System error: Invalid event ID. Please try again."
                            action_result = {"error": "Invalid event ID format"}
                        else:
                            # Register user for the event
                            register_resp = await client.post(
                                f"{base_url}/api/events/register",
                                json={
                                    "event_id": event_id_str,
                                    "user_id": request.user_id
                                }
                            )
                            if register_resp.status_code == 200:
                                action_result = register_resp.json()
                                event_title = matched_event.get("title", "the event")
                                message = f"Successfully registered you for '{event_title}'! Registration confirmed."
                                
                                # Add navigation and confirmation data for frontend
                                action_result["navigation"] = {
                                    "action": "navigate_to_booking_confirmation",
                                    "route": "/events/booking/confirmation",
                                    "event_id": event_id_str,
                                    "should_navigate": True
                                }
                                action_result["event_details"] = matched_event
                                action_result["confirmation_message"] = f"You're all set! You're registered for '{event_title}' on {matched_event.get('date', 'TBA')} at {matched_event.get('time', 'TBA')}."
                                action_result["booking_confirmed"] = True
                                
                                action_executed = True
                            else:
                                error_detail = register_resp.json().get("detail", register_resp.text) if register_resp.headers.get("content-type", "").startswith("application/json") else register_resp.text
                                if "already registered" in error_detail.lower():
                                    message = f"You're already registered for '{matched_event.get('title', 'this event')}'."
                                else:
                                    message = f"Could not register for event. {error_detail}"
                                action_result = {"error": error_detail}
                else:
                    message = "Could not retrieve events list. Please try again later."
            
            elif intent == "list_events":
                # List available events
                events_resp = await client.get(f"{base_url}/api/events/list?limit=10")
                if events_resp.status_code == 200:
                    action_result = events_resp.json()
                    events = action_result.get("events", [])
                    if events:
                        event_list = "\n".join([
                            f"• {e.get('title')} - {e.get('date')} at {e.get('time')}"
                            for e in events[:5]
                        ])
                        message = f"Here are the available events:\n{event_list}"
                        if len(events) > 5:
                            message += f"\n... and {len(events) - 5} more events."
                    else:
                        message = "No events available at the moment."
                    action_executed = True
                else:
                    message = "Could not retrieve events list."
            
            elif intent == "get_event":
                # Get specific event details
                event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
                potential_event_id = intent_data.get("event_id")
                
                # Get events to search
                events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
                if events_resp.status_code == 200:
                    events_raw = events_resp.json().get("events", [])
                    # Filter out any events with invalid IDs
                    uuid_pattern_filter = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                    events = []
                    for event in events_raw:
                        event_id_check = event.get("id")
                        if event_id_check and uuid_pattern_filter.match(str(event_id_check)) and len(str(event_id_check)) == 36:
                            events.append(event)
                    
                    # Use improved matching function to find the specific event
                    matched_event = find_event_by_name_or_id(
                        events=events,
                        event_name=event_name if event_name else None,
                        event_id=potential_event_id if potential_event_id else None
                    )
                    
                    if matched_event:
                        event_id_str = validate_and_get_uuid(matched_event.get("id"))
                        if event_id_str:
                            # Get full event details
                            event_resp = await client.get(f"{base_url}/api/events/{event_id_str}")
                            if event_resp.status_code == 200:
                                event_data = event_resp.json().get("event", matched_event)
                                action_result = {"event": event_data}
                                
                                # Format detailed message
                                title = event_data.get('title', 'Event')
                                date = event_data.get('date', 'TBA')
                                time = event_data.get('time', 'TBA')
                                location = event_data.get('location', 'TBA')
                                description = event_data.get('description', 'No description available')
                                max_participants = event_data.get('max_participants')
                                
                                message = f"📅 {title}\n\n"
                                message += f"Date: {date} at {time}\n"
                                message += f"Location: {location}\n"
                                if max_participants:
                                    message += f"Max Participants: {max_participants}\n"
                                message += f"\nDescription: {description}"
                                
                                action_executed = True
                            else:
                                # Fallback to matched event data
                                event_data = matched_event
                                title = event_data.get('title', 'Event')
                                date = event_data.get('date', 'TBA')
                                time = event_data.get('time', 'TBA')
                                location = event_data.get('location', 'TBA')
                                description = event_data.get('description', 'No description available')
                                
                                message = f"📅 {title}\n\n"
                                message += f"Date: {date} at {time}\n"
                                message += f"Location: {location}\n"
                                message += f"\nDescription: {description}"
                                
                                action_result = {"event": event_data}
                                action_executed = True
                        else:
                            message = "System error: Invalid event ID. Please try again."
                    else:
                        # Event not found - provide helpful suggestions
                        if event_name and events:
                            # Find similar event names
                            suggestions = []
                            search_lower = event_name.lower()
                            for event in events[:5]:
                                title_lower = event.get("title", "").lower()
                                if any(word in title_lower for word in search_lower.split() if len(word) > 3):
                                    suggestions.append(event.get("title"))
                            
                            if suggestions:
                                suggestions_text = "\n".join([f"- {s}" for s in suggestions[:3]])
                                message = f"I couldn't find an event matching '{event_name}'. Did you mean one of these?\n{suggestions_text}"
                            else:
                                event_list = "\n".join([f"- {e.get('title')}" for e in events[:3]])
                                message = f"I couldn't find an event matching '{event_name}'. Available events:\n{event_list}"
                        elif not event_name:
                            if events:
                                event_list = "\n".join([f"- {e.get('title')} ({e.get('date')})" for e in events[:5]])
                                message = f"Please specify which event you'd like details about. Available events:\n{event_list}"
                            else:
                                message = "No events available at the moment."
                        else:
                            message = f"I couldn't find that event. Please specify the event name."
                else:
                    message = "Could not retrieve events list. Please try again later."
            
            elif intent in ["cancel_event", "unregister_event"]:
                # Unregister from event
                event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
                potential_event_id = intent_data.get("event_id")
                
                # Get events to search (we'll check if user is registered)
                events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
                if events_resp.status_code == 200:
                    events_raw = events_resp.json().get("events", [])
                    # Filter out any events with invalid IDs
                    uuid_pattern_filter = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                    events = []
                    for event in events_raw:
                        event_id_check = event.get("id")
                        if event_id_check and uuid_pattern_filter.match(str(event_id_check)) and len(str(event_id_check)) == 36:
                            events.append(event)
                    
                    # Use improved matching function to find the specific event
                    matched_event = find_event_by_name_or_id(
                        events=events,
                        event_name=event_name if event_name else None,
                        event_id=potential_event_id if potential_event_id else None
                    )
                    
                    if matched_event:
                        event_id_str = validate_and_get_uuid(matched_event.get("id"))
                        if event_id_str:
                            # Unregister user from the event
                            unregister_resp = await client.delete(
                                f"{base_url}/api/events/register/{event_id_str}/{request.user_id}"
                            )
                            if unregister_resp.status_code == 200:
                                action_result = unregister_resp.json()
                                event_title = matched_event.get("title", "the event")
                                message = f"Successfully unregistered you from '{event_title}'."
                                action_executed = True
                            else:
                                error_detail = unregister_resp.json().get("detail", unregister_resp.text) if unregister_resp.headers.get("content-type", "").startswith("application/json") else unregister_resp.text
                                if "not found" in error_detail.lower() or "not registered" in error_detail.lower():
                                    event_title = matched_event.get("title", "this event")
                                    message = f"You're not currently registered for '{event_title}'."
                                else:
                                    message = f"Could not unregister. {error_detail}"
                                action_result = {"error": error_detail}
                        else:
                            message = "System error: Invalid event ID. Please try again."
                    else:
                        # Event not found - provide helpful suggestions
                        if event_name and events:
                            # Find similar event names
                            suggestions = []
                            search_lower = event_name.lower()
                            for event in events[:5]:
                                title_lower = event.get("title", "").lower()
                                if any(word in title_lower for word in search_lower.split() if len(word) > 3):
                                    suggestions.append(event.get("title"))
                            
                            if suggestions:
                                suggestions_text = "\n".join([f"- {s}" for s in suggestions[:3]])
                                message = f"I couldn't find an event matching '{event_name}'. Did you mean one of these?\n{suggestions_text}"
                            else:
                                message = f"I couldn't find an event matching '{event_name}'. Please specify the exact event name you want to cancel."
                        elif not event_name:
                            if events:
                                event_list = "\n".join([f"- {e.get('title')}" for e in events[:5]])
                                message = f"Please specify which event you'd like to cancel. Available events:\n{event_list}"
                            else:
                                message = "No events available to cancel."
                        else:
                            message = "I couldn't find the event you want to cancel. Please specify the event name."
                else:
                    message = "Could not retrieve events list. Please try again later."
            
            else:
                # General intent - use GPT to answer questions intelligently
                try:
                    # Try to get OpenAI client for general question answering
                    try:
                        gpt_client = get_openai_client()
                        
                        # Get available events for context
                        available_events = []
                        try:
                            events_resp = await client.get(f"{base_url}/api/events/list?limit=5")
                            if events_resp.status_code == 200:
                                available_events = events_resp.json().get("events", [])
                        except:
                            pass
                        
                        events_context = ""
                        if available_events:
                            events_list = "\n".join([
                                f"- {e.get('title')} on {e.get('date')}"
                                for e in available_events[:5]
                            ])
                            events_context = f"\n\nAvailable Events:\n{events_list}"
                        
                        # Create prompt for general question answering
                        general_prompt = f"""You are a helpful assistant for a community engagement platform. Answer the user's question in a friendly, concise way.

User question: "{request.message}"
{events_context}

Context about this platform:
- Users can book/register for events
- Users can view event details
- Users can cancel event registrations
- Users can trigger emergency SOS calls
- The platform helps connect community members

Answer the user's question helpfully. If they're asking about how to use the platform, provide clear instructions. If they're asking about events, reference the available events above if relevant. Keep your response concise (2-3 sentences max) and friendly."""
                        
                        try:
                            gpt_response = gpt_client.chat.completions.create(
                                model="gpt-4",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a helpful community platform assistant. Answer questions concisely and friendly."
                                    },
                                    {
                                        "role": "user",
                                        "content": general_prompt
                                    }
                                ],
                                temperature=0.7,
                                max_tokens=200
                            )
                            message = gpt_response.choices[0].message.content.strip()
                            action_executed = True
                        except:
                            # Fallback to gpt-3.5-turbo
                            gpt_response = gpt_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a helpful community platform assistant. Answer questions concisely and friendly."
                                    },
                                    {
                                        "role": "user",
                                        "content": general_prompt
                                    }
                                ],
                                temperature=0.7,
                                max_tokens=200
                            )
                            message = gpt_response.choices[0].message.content.strip()
                            action_executed = True
                    except HTTPException:
                        # OpenAI not available - use default message
                        message = "I can help you with:\n• Booking events (say 'book event' or 'register for event')\n• Viewing events (say 'show events' or 'list events')\n• Getting event details (say 'tell me about [event name]')\n• Canceling events (say 'cancel [event name]')\n• Emergency help (say 'help' or 'emergency')\n• And more! What would you like to do?"
                    except Exception as e:
                        # Error with GPT - use default message
                        print(f"Error in general question answering: {e}")
                        message = "I can help you with:\n• Booking events (say 'book event' or 'register for event')\n• Viewing events (say 'show events' or 'list events')\n• Getting event details (say 'tell me about [event name]')\n• Canceling events (say 'cancel [event name]')\n• Emergency help (say 'help' or 'emergency')\n• And more! What would you like to do?"
                except Exception as e:
                    # Fallback to default message
                    message = "I can help you with:\n• Booking events (say 'book event' or 'register for event')\n• Viewing events (say 'show events' or 'list events')\n• Getting event details (say 'tell me about [event name]')\n• Canceling events (say 'cancel [event name]')\n• Emergency help (say 'help' or 'emergency')\n• And more! What would you like to do?"
    
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        # Connection error - API_BASE_URL likely not set correctly
        error_msg = str(e)
        message = f"Connection error: Could not reach backend API. Please ensure API_BASE_URL is set to your backend's public URL (e.g., https://your-backend.onrender.com). Error: {error_msg}"
        action_result = {"error": error_msg, "error_type": "connection_failed"}
        print(f"Connection error in process_message: {error_msg}")
    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any other errors and return a proper response instead of crashing
        error_msg = str(e)
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in process_message action execution: {error_msg}")
        print(f"Traceback: {error_traceback}")
        message = f"Error processing your request: {error_msg}"
        action_result = {"error": error_msg}
    
    response = {
        "success": True,
        "intent": intent,
        "message": message,
        "user_id": request.user_id,
        "action_executed": action_executed,
        "sos_triggered": sos_triggered
    }
    
    if action_result:
        response["action_result"] = action_result
        # If booking was successful, include navigation info in main response for easy frontend access
        if action_result.get("booking_confirmed") and action_result.get("navigation"):
            response["navigation"] = action_result["navigation"]
            response["event_details"] = action_result.get("event_details")
            response["confirmation_message"] = action_result.get("confirmation_message")
            response["should_navigate"] = True
    
    return response


@router.post("/voice")
async def process_voice_message(request: VoiceMessage):
    """
    Process a voice recording message from the user
    Transcribed text is analyzed for intent and actions are automatically executed
    Works exactly like text messages but with voice transcript
    
    Accepts either:
    - transcript: Pre-transcribed text (from frontend speech recognition) - RECOMMENDED
    - audio: Base64 encoded audio (will be transcribed using Whisper if transcript not provided)
    
    Note: If using audio, OPENAI_API_KEY must be configured. Transcript-based processing works without it.
    """
    try:
        transcript = request.transcript
        
        # If no transcript but audio is provided, transcribe it using Whisper
        if (not transcript or not transcript.strip()) and request.audio:
            # Check if OpenAI is available before attempting transcription
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Return 400 (Bad Request) instead of 500 to avoid triggering frontend's "voice unavailable" message
                raise HTTPException(
                    status_code=400,
                    detail="Audio transcription requires OPENAI_API_KEY. Please provide 'transcript' field instead (use frontend speech-to-text), or configure OPENAI_API_KEY in backend environment variables."
                )
            
            try:
                transcript = await process_audio_with_whisper(request.audio)
            except Exception as e:
                # Return 400 instead of 500 to avoid triggering frontend error message
                error_msg = str(e)
                # Don't mention "OpenAI package" to avoid triggering frontend's error detection
                if "OpenAI package" in error_msg or "pip install" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail="Audio transcription is not available. Please provide 'transcript' field instead (use frontend speech-to-text)."
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to transcribe audio: {error_msg}. Please provide 'transcript' field instead."
                )
        
        # Validate we have a transcript
        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Either 'transcript' (recommended - use frontend speech-to-text) or 'audio' must be provided. If using audio, OPENAI_API_KEY must be configured in backend."
            )
        
        # Process voice message the same way as text message
        # Convert VoiceMessage to TextMessage format
        text_request = TextMessage(
            user_id=request.user_id,
            message=transcript,
            location=request.location
        )
        
        # Use the same processing logic
        try:
            result = await process_message(text_request)
        except HTTPException:
            # Re-raise HTTPExceptions (they're already properly formatted)
            raise
        except Exception as e:
            # Catch any errors from process_message and return a proper error
            import traceback
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            print(f"Error in process_message: {error_msg}")
            print(f"Traceback: {error_traceback}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process message: {error_msg}"
            )
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            result = {
                "success": True,
                "intent": "general",
                "message": str(result) if result else "Message processed",
                "user_id": request.user_id
            }
        
        # Ensure required fields are present
        if "success" not in result:
            result["success"] = True
        if "intent" not in result:
            result["intent"] = "general"
        if "message" not in result:
            result["message"] = "Voice message processed"
        if "user_id" not in result:
            result["user_id"] = request.user_id
        
        # Add transcript to response
        result["transcript"] = transcript
        result["source"] = "voice"
        
        # Ensure frontend knows actions were executed automatically
        # If action_executed is True, make sure it's clear in the response
        try:
            action_executed = result.get("action_executed", False)
            sos_triggered = result.get("sos_triggered", False)
            should_navigate = result.get("should_navigate", False)
            
            if action_executed or sos_triggered or should_navigate:
                result["voice_action_completed"] = True
                result["requires_manual_action"] = False
            else:
                result["voice_action_completed"] = False
                result["requires_manual_action"] = True
        except Exception as e:
            # If checking action status fails, default to manual action required
            print(f"Warning: Could not determine action status: {e}")
            result["voice_action_completed"] = False
            result["requires_manual_action"] = True
        
        return result
    except HTTPException:
        # Re-raise HTTPExceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any other unexpected errors and return a proper error response
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        print(f"Unexpected error in process_voice_message: {error_msg}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=500,
            detail=f"Backend server error: {error_msg}. Please try again later or contact support."
        )


@router.get("/history/{user_id}")
def get_history(user_id: str, limit: int = 20):
    """Get conversation history for a user"""
    return {
        "success": True,
        "user_id": user_id,
        "conversations": [],
        "count": 0,
        "message": "Conversation history - ready for implementation"
    }


# ==================== SINGLISH PROCESSING ====================

@router.get("/test-route")
def test_route():
    """Simple test endpoint to verify route registration"""
    return {
        "success": True,
        "message": "Orchestrator routes are working!",
        "endpoint": "/api/orchestrator/test-route"
    }


@router.get("/voice-status")
def voice_status():
    """Check if voice processing is available - simple endpoint for frontend checks"""
    audio_transcription_available = False
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            audio_transcription_available = True
    except:
        pass
    
    return {
        "success": True,
        "voice_processing_available": True,  # Always available with transcripts
        "audio_transcription_available": audio_transcription_available,
        "message": "Voice processing is available. Send transcripts via /voice endpoint."
    }


@router.post("/process-singlish")
async def process_singlish(request: SinglishProcessRequest):
    """
    Process Singlish audio or text input:
    1. If audio provided: Convert with Whisper STT
    2. If transcript provided: Use directly
    3. Translate Singlish to clean English
    4. Analyze sentiment and tone
    
    Returns:
    {
        "success": true,
        "singlish_raw": "original transcript",
        "clean_english": "translated text",
        "sentiment": "emotion detected",
        "tone": "tone description"
    }
    """
    try:
        # Validate input
        if not request.audio and not request.transcript:
            raise HTTPException(
                status_code=400,
                detail="Either 'audio' or 'transcript' must be provided"
            )
        
        # Step 1: Get transcript (from audio or direct input)
        transcript = None
        
        if request.audio:
            # Decode base64 audio and process with Whisper
            transcript = await process_audio_with_whisper(request.audio)
        else:
            # Use provided transcript
            transcript = request.transcript
        
        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract transcript from audio or transcript is empty"
            )
        
        # Step 2: Process with GPT for translation and analysis
        result = await translate_singlish_to_english(transcript)
        
        return {
            "success": True,
            "user_id": request.user_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Singlish: {str(e)}"
        )


# ==================== HELPER FUNCTIONS ====================

async def process_audio_with_whisper(audio_base64: str) -> str:
    """
    Convert base64 audio to transcript using OpenAI Whisper
    
    Args:
        audio_base64: Base64 encoded audio string
    
    Returns:
        Transcribed text
    """
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            # Call Whisper API
            client = get_openai_client()
            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Singlish is primarily English-based
                )
            
            return transcription.text
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    except Exception as e:
        raise Exception(f"Whisper STT failed: {str(e)}")


async def translate_singlish_to_english(transcript: str) -> Dict[str, str]:
    """
    Translate Singlish to clean English and analyze sentiment/tone
    Tries SEA-LION/Merlion first (if configured), falls back to OpenAI
    
    Args:
        transcript: Raw Singlish transcript
    
    Returns:
        Dictionary with singlish_raw, clean_english, sentiment, tone
    """
    try:
        # Create prompt for LLM
        prompt = f"""You are an expert in Singlish (Singaporean English) and standard English translation.

Your task:
1. Translate the following Singlish transcript into clear, natural Standard English
2. Preserve the original meaning and intent
3. Interpret Singlish slang, Malay words, Hokkien phrases, and dialect expressions
4. Do NOT preserve slang literally - translate it properly
5. Analyze the sentiment (e.g., happy, frustrated, angry, neutral, surprised)
6. Describe the tone (e.g., informal, casual, urgent, polite, aggressive)

Singlish transcript: "{transcript}"

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
    "clean_english": "your translation here",
    "sentiment": "detected sentiment",
    "tone": "detected tone"
}}"""

        # Try SEA-LION/Merlion first (if configured)
        sea_lion_url = os.getenv("SEA_LION_API_URL")
        sea_lion_api_key = os.getenv("SEA_LION_API_KEY")
        
        if sea_lion_url:
            try:
                return await call_sea_lion_api(sea_lion_url, sea_lion_api_key, prompt, transcript)
            except Exception as e:
                # Fallback to OpenAI if SEA-LION fails
                print(f"SEA-LION API failed: {e}, falling back to OpenAI")
        
        # Fallback to OpenAI
        return await call_openai_api(prompt, transcript)
        
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")


async def call_sea_lion_api(api_url: str, api_key: Optional[str], prompt: str, transcript: str) -> Dict[str, str]:
    """
    Call SEA-LION or Merlion LLM API
    
    Args:
        api_url: SEA-LION API endpoint URL
        api_key: Optional API key (if required)
        prompt: The prompt to send
        transcript: Original transcript
    
    Returns:
        Dictionary with translation results
    """
    import httpx
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # SEA-LION API format (official API)
    payload = {
        "model": "aisingapore/Gemma-SEA-LION-v4-27B-IT",
        "messages": [
            {
                "role": "system",
                "content": "You are a Singlish translation expert. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Parse response (adjust based on actual API response format)
        if "choices" in result:
            text = result["choices"][0]["message"]["content"].strip()
        elif "text" in result:
            text = result["text"].strip()
        else:
            text = str(result).strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        
        result_data = json.loads(text)
        
        return {
            "singlish_raw": transcript,
            "clean_english": result_data.get("clean_english", ""),
            "sentiment": result_data.get("sentiment", "neutral"),
            "tone": result_data.get("tone", "informal")
        }


async def call_openai_api(prompt: str, transcript: str) -> Dict[str, str]:
    """
    Call OpenAI API for translation (fallback)
    
    Args:
        prompt: The prompt to send
        transcript: Original transcript
    
    Returns:
        Dictionary with translation results
    """
    # Call GPT API (try gpt-4, fallback to gpt-3.5-turbo)
    client = get_openai_client()
    try:
        model = "gpt-4"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Singlish translation expert. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
    except Exception as e:
        # Fallback to gpt-3.5-turbo if gpt-4 is not available
        if "gpt-4" in str(e).lower() or "model" in str(e).lower():
            model = "gpt-3.5-turbo"
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Singlish translation expert. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
        else:
            raise
        
    # Parse response
    result_text = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
        result_text = result_text.strip()
    
    try:
        result = json.loads(result_text)
        
        return {
            "singlish_raw": transcript,
            "clean_english": result.get("clean_english", ""),
            "sentiment": result.get("sentiment", "neutral"),
            "tone": result.get("tone", "informal")
        }
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "singlish_raw": transcript,
            "clean_english": "Translation error - invalid response format",
            "sentiment": "unknown",
            "tone": "unknown"
        }
    except Exception as e:
        raise Exception(f"OpenAI translation failed: {str(e)}")

