"""
Orchestrator Routes
Main coordinator and request routing
Includes Singlish-to-English translation with sentiment analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import os
import tempfile
from openai import OpenAI
from app.shared.supabase import get_supabase_client


router = APIRouter()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==================== REQUEST MODELS ====================

class TextMessage(BaseModel):
    """Text message from user"""
    user_id: str
    message: str


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
            "history": "/api/orchestrator/history/{user_id}"
        },
        "status": "ready"
    }


@router.post("/message")
def process_message(request: TextMessage):
    """
    Process a text message from the user
    Routes to appropriate module based on intent
    """
    message_lower = request.message.lower()
    
    # Simple intent detection
    if any(word in message_lower for word in ["event", "activity", "happening"]):
        intent = "find_events"
        message = "Looking for events! Check /api/events/list for available events."
    elif any(word in message_lower for word in ["help", "emergency", "sos"]):
        intent = "emergency"
        message = "Emergency detected! Check /api/safety/emergency for emergency features."
    else:
        intent = "general"
        message = "I can help you find events, manage reminders, or handle emergencies!"
    
    return {
        "success": True,
        "intent": intent,
        "message": message,
        "user_id": request.user_id
    }


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
            with open(temp_audio_path, "rb") as audio_file:
                transcription = openai_client.audio.transcriptions.create(
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

        # Call GPT API
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better Singlish understanding
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
        
        # Parse response
        import json
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

