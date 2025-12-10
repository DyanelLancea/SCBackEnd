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


router = APIRouter()

# Initialize OpenAI client lazily (only when needed)
def get_openai_client():
    """Get OpenAI client, initializing if needed"""
    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="OpenAI package is not installed. Please install it with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set. Please configure it in your environment."
        )
    return OpenAI(api_key=api_key)


# ==================== REQUEST MODELS ====================

class TextMessage(BaseModel):
    """Text message from user"""
    user_id: str
    message: str
    location: Optional[str] = None  # Optional location from voice/message


class VoiceMessage(BaseModel):
    """Voice recording message from user"""
    user_id: str
    transcript: str  # Transcribed text from voice recording
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
    return {
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


async def detect_intent_and_extract_info(user_message: str, user_id: str) -> Dict[str, Any]:
    """
    Use GPT to intelligently detect user intent and extract relevant information
    Returns intent type and extracted parameters
    """
    try:
        client = get_openai_client()
        
        # Get available events to help GPT understand context
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        available_events = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                events_response = await http_client.get(f"{base_url}/api/events/list?limit=10")
                if events_response.status_code == 200:
                    events_data = events_response.json()
                    available_events = events_data.get("events", [])
        except:
            pass  # Continue without events if fetch fails
        
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
1. "emergency" - User needs emergency help/SOS
2. "book_event" or "register_event" - User wants to register/book for an event
3. "list_events" - User wants to see available events
4. "get_event" - User wants details about a specific event
5. "cancel_event" or "unregister_event" - User wants to cancel/unregister from an event
6. "update_location" - User wants to update their location
7. "general" - General conversation or unclear intent

IMPORTANT for event-related intents:
- event_id: ONLY use the exact UUID from the available events list above, or null if not found
- event_name: Extract the event name/title mentioned by the user (partial matches are OK)
- event_date: Date if mentioned (YYYY-MM-DD format)
- DO NOT make up UUIDs or use numbers like "1" - only use actual UUIDs from the events list

Respond ONLY with valid JSON (no markdown):
{{
    "intent": "intent_type",
    "event_id": "exact-uuid-from-events-list-or-null",
    "event_name": "extracted-event-name-or-null",
    "event_date": "YYYY-MM-DD-or-null",
    "confidence": 0.0-1.0
}}"""

        try:
            model = "gpt-4"
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
                max_tokens=300
            )
        except:
            # Fallback to gpt-3.5-turbo
            model = "gpt-3.5-turbo"
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
                max_tokens=300
            )
        
        result_text = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        # If event_id not found but event_name is, try to match with available events
        if result.get("intent") in ["book_event", "register_event", "get_event", "cancel_event", "unregister_event"]:
            if not result.get("event_id") and result.get("event_name") and available_events:
                event_name_lower = result.get("event_name", "").lower()
                for event in available_events:
                    if event_name_lower in event.get("title", "").lower():
                        result["event_id"] = event.get("id")
                        break
        
        return result
        
    except Exception as e:
        # Fallback to simple keyword detection
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
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    action_executed = False
    action_result = None
    sos_triggered = False
    
    # Use GPT to detect intent and extract information
    try:
        intent_data = await detect_intent_and_extract_info(request.message, request.user_id)
        intent = intent_data.get("intent", "general")
    except:
        # Fallback to simple detection
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
                event_id = None
                # Try to get event name from intent_data, or extract from original message
                event_name = intent_data.get("event_name", "").lower() if intent_data.get("event_name") else ""
                
                # If GPT didn't extract event name, try to extract from original message
                if not event_name:
                    # Look for common patterns like "join [event]", "book [event]", "register for [event]"
                    message_lower = request.message.lower()
                    # Remove common booking phrases to get event name
                    patterns_to_remove = [
                        r"i want to (join|book|register for|sign up for) (the )?",
                        r"(join|book|register for|sign up for) (the )?",
                        r"i'd like to (join|book|register for) (the )?",
                        r"can i (join|book|register for) (the )?",
                        r"please (join|book|register me for) (the )?",
                    ]
                    for pattern in patterns_to_remove:
                        message_lower = re.sub(pattern, "", message_lower)
                    # Extract potential event name (take first few words after cleaning)
                    words = message_lower.strip().split()
                    if words:
                        # Remove common words like "event", "class", "workshop" from the end
                        common_words = {"event", "class", "workshop", "session", "meeting"}
                        filtered_words = []
                        for word in words[:4]:  # Take up to 4 words
                            word_clean = re.sub(r'[.,!?]+$', '', word)
                            if word_clean not in common_words or not filtered_words:
                                # Keep common words only if it's the first word (might be part of name)
                                filtered_words.append(word_clean)
                        event_name = " ".join(filtered_words).strip()
                        # Remove trailing punctuation
                        event_name = re.sub(r'[.,!?]+$', '', event_name)
                
                # First, get available events to search through
                events_resp = await client.get(f"{base_url}/api/events/list?limit=20")
                if events_resp.status_code == 200:
                    events = events_resp.json().get("events", [])
                    
                    # Try to find event by ID from intent_data (validate it's a UUID)
                    potential_id = intent_data.get("event_id")
                    if potential_id:
                        # Validate UUID format (basic check) - reject if it's just a number like "1"
                        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                        potential_id_str = str(potential_id).strip()
                        # Reject simple numbers or non-UUID strings
                        if uuid_pattern.match(potential_id_str) and len(potential_id_str) == 36:
                            # Check if this event exists
                            for event in events:
                                event_uuid = event.get("id")
                                if event_uuid and str(event_uuid) == potential_id_str:
                                    event_id = event_uuid
                                    break
                        # If potential_id is invalid (like "1"), ignore it and continue to name matching
                    
                    # If no valid ID found, try to match by name with improved matching
                    if not event_id and event_name:
                        # Normalize event name (remove spaces, punctuation for better matching)
                        # This helps match "pickleball" with "pickle ball"
                        normalized_search = re.sub(r'[\s\-_]', '', event_name.lower())
                        best_match = None
                        best_score = 0
                        
                        for event in events:
                            # Ensure we have a valid event with an ID
                            event_uuid = event.get("id")
                            if not event_uuid:
                                continue
                                
                            event_title = event.get("title", "").lower()
                            normalized_title = re.sub(r'[\s\-_]', '', event_title)
                            
                            # Strategy 1: Normalized string match (handles "pickleball" vs "pickle ball")
                            if normalized_search == normalized_title or normalized_search in normalized_title or normalized_title in normalized_search:
                                # Validate UUID before setting
                                uuid_pattern_check = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                                if uuid_pattern_check.match(str(event_uuid)):
                                    event_id = event_uuid
                                    break
                            
                            # Strategy 2: Substring match in original strings
                            if event_name in event_title or event_title in event_name:
                                uuid_pattern_check = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                                if uuid_pattern_check.match(str(event_uuid)):
                                    event_id = event_uuid
                                    break
                            
                            # Strategy 3: Word-based matching with scoring
                            search_words = [w.strip() for w in re.split(r'[\s\-_]', event_name) if len(w.strip()) > 2]
                            title_words = [w.strip() for w in re.split(r'[\s\-_]', event_title) if len(w.strip()) > 0]
                            
                            if search_words:
                                # Check how many search words match title words
                                matched_count = 0
                                for search_word in search_words:
                                    for title_word in title_words:
                                        # Check if words match (handles partial matches)
                                        if search_word in title_word or title_word in search_word or normalized_search in normalized_title:
                                            matched_count += 1
                                            break
                                
                                score = matched_count / len(search_words) if search_words else 0
                                if score > best_score:
                                    # Validate UUID before storing as best match
                                    uuid_pattern_check = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                                    if uuid_pattern_check.match(str(event_uuid)):
                                        best_score = score
                                        best_match = event_uuid
                        
                        # Use best match if no exact match found but we have a good candidate
                        if not event_id and best_match and best_score >= 0.6:
                            # Validate best_match is a proper UUID
                            uuid_pattern_check = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                            if uuid_pattern_check.match(str(best_match)):
                                event_id = best_match
                            else:
                                # Invalid UUID in best_match - clear it
                                event_id = None
                    
                    # If still no match and user just said "book event" without specifics, show available events
                    if not event_id and not event_name:
                        if events:
                            # List available events for user to choose
                            event_list = "\n".join([
                                f"{i+1}. {e.get('title')} - {e.get('date')}"
                                for i, e in enumerate(events[:5])
                            ])
                            message = f"I found {len(events)} events. Please specify which one:\n{event_list}"
                            action_result = {"events": events[:10], "count": len(events)}
                            action_executed = True
                        else:
                            message = "No events available to register for."
                    elif not event_id:
                        # Event name mentioned but not found
                        message = f"I couldn't find an event matching '{intent_data.get('event_name', 'your request')}'. Please try again with the exact event name."
                    else:
                        # Validate event_id is a proper UUID before using it
                        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                        if not uuid_pattern.match(str(event_id)):
                            # Invalid UUID - this shouldn't happen, but log it and try to find event by name again
                            message = f"Error: Invalid event ID format detected ({event_id}). Searching by name instead..."
                            action_result = {"error": f"Invalid event_id format: {event_id}"}
                            # Try to re-match by name
                            if event_name:
                                for event in events:
                                    event_title = event.get("title", "").lower()
                                    normalized_title = re.sub(r'[\s\-_]', '', event_title)
                                    normalized_search = re.sub(r'[\s\-_]', '', event_name.lower())
                                    if normalized_search in normalized_title or event_name in event_title:
                                        event_id = event.get("id")
                                        # Validate the new ID
                                        if uuid_pattern.match(str(event_id)):
                                            break
                                        else:
                                            event_id = None
                            
                            if not event_id or not uuid_pattern.match(str(event_id)):
                                message = f"I couldn't find a valid event matching '{event_name}'. Please try again with the exact event name."
                                action_result = {"error": "Could not find valid event"}
                        
                        # Only proceed if we have a valid UUID
                        if event_id and uuid_pattern.match(str(event_id)):
                            # Found event with valid UUID, register user
                            register_resp = await client.post(
                                f"{base_url}/api/events/register",
                                json={
                                    "event_id": event_id,
                                    "user_id": request.user_id
                                }
                            )
                            if register_resp.status_code == 200:
                                action_result = register_resp.json()
                                # Get event title for confirmation message
                                event_title = "the event"
                                for event in events:
                                    if event.get("id") == event_id:
                                        event_title = event.get("title", "the event")
                                        break
                                message = f"Successfully registered you for '{event_title}'! Registration confirmed."
                                action_executed = True
                            else:
                                error_detail = register_resp.json().get("detail", register_resp.text) if register_resp.headers.get("content-type", "").startswith("application/json") else register_resp.text
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
                event_id = None
                event_name = intent_data.get("event_name", "").lower() if intent_data.get("event_name") else ""
                
                # Get events to search
                events_resp = await client.get(f"{base_url}/api/events/list?limit=20")
                if events_resp.status_code == 200:
                    events = events_resp.json().get("events", [])
                    
                    # Try to find event by ID (validate UUID)
                    potential_id = intent_data.get("event_id")
                    if potential_id:
                        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                        if uuid_pattern.match(str(potential_id)):
                            for event in events:
                                if event.get("id") == potential_id:
                                    event_id = potential_id
                                    break
                    
                    # If no valid ID, try to match by name
                    if not event_id and event_name:
                        for event in events:
                            event_title = event.get("title", "").lower()
                            if event_name in event_title or any(word in event_title for word in event_name.split() if len(word) > 3):
                                event_id = event.get("id")
                                break
                
                if event_id:
                    event_resp = await client.get(f"{base_url}/api/events/{event_id}")
                    if event_resp.status_code == 200:
                        action_result = event_resp.json()
                        event = action_result.get("event", {})
                        message = f"Event: {event.get('title')}\nDate: {event.get('date')} at {event.get('time')}\nLocation: {event.get('location', 'TBA')}\nDescription: {event.get('description', 'No description')}"
                        action_executed = True
                    else:
                        message = "Event not found."
                else:
                    message = "I couldn't find that event. Please specify the event name."
            
            elif intent in ["cancel_event", "unregister_event"]:
                # Unregister from event
                event_id = None
                event_name = intent_data.get("event_name", "").lower() if intent_data.get("event_name") else ""
                
                # Get user's registered events or all events to search
                events_resp = await client.get(f"{base_url}/api/events/list?limit=20")
                if events_resp.status_code == 200:
                    events = events_resp.json().get("events", [])
                    
                    # Try to find event by ID (validate UUID)
                    potential_id = intent_data.get("event_id")
                    if potential_id:
                        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                        if uuid_pattern.match(str(potential_id)):
                            for event in events:
                                if event.get("id") == potential_id:
                                    event_id = potential_id
                                    break
                    
                    # If no valid ID, try to match by name
                    if not event_id and event_name:
                        for event in events:
                            event_title = event.get("title", "").lower()
                            if event_name in event_title or any(word in event_title for word in event_name.split() if len(word) > 3):
                                event_id = event.get("id")
                                break
                
                if event_id:
                    unregister_resp = await client.delete(
                        f"{base_url}/api/events/register/{event_id}/{request.user_id}"
                    )
                    if unregister_resp.status_code == 200:
                        action_result = unregister_resp.json()
                        message = "Successfully unregistered from the event."
                        action_executed = True
                    else:
                        error_detail = unregister_resp.json().get("detail", unregister_resp.text) if unregister_resp.headers.get("content-type", "").startswith("application/json") else unregister_resp.text
                        message = f"Could not unregister. {error_detail}"
                        action_result = {"error": error_detail}
                else:
                    message = "I couldn't find the event you want to cancel. Please specify the event name."
            
            else:
                # General intent - provide helpful message
                message = "I can help you with:\n• Booking events (say 'book event' or 'register for event')\n• Viewing events (say 'show events' or 'list events')\n• Emergency help (say 'help' or 'emergency')\n• And more! What would you like to do?"
    
    except Exception as e:
        message = f"Error processing your request: {str(e)}"
        action_result = {"error": str(e)}
    
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
    
    return response


@router.post("/voice")
async def process_voice_message(request: VoiceMessage):
    """
    Process a voice recording message from the user
    Transcribed text is analyzed for intent and actions are automatically executed
    Works exactly like text messages but with voice transcript
    """
    # Process voice message the same way as text message
    # Convert VoiceMessage to TextMessage format
    text_request = TextMessage(
        user_id=request.user_id,
        message=request.transcript,
        location=request.location
    )
    
    # Use the same processing logic
    result = await process_message(text_request)
    
    # Add transcript to response
    result["transcript"] = request.transcript
    result["source"] = "voice"
    
    return result


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
    
    Args:
        transcript: Raw Singlish transcript
    
    Returns:
        Dictionary with singlish_raw, clean_english, sentiment, tone
    """
    try:
        # Create prompt for GPT
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
        raise Exception(f"GPT translation failed: {str(e)}")

