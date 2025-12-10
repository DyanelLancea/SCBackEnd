"""
Orchestrator Routes
Audio transcription (Whisper STT) + LLM processing for Singlish → English translation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import openai
from openai import OpenAI

router = APIRouter()

# Initialize OpenAI client
client = None

def get_openai_client():
    """Get or initialize OpenAI client"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured. Please set it in your .env file."
            )
        client = OpenAI(api_key=api_key)
    return client


# ==================== REQUEST/RESPONSE MODELS ====================

class TranscriptRequest(BaseModel):
    """Request model for text-only processing (no audio)"""
    transcript: str = Field(..., min_length=1, description="Raw text transcript to process")

class TranscriptionResponse(BaseModel):
    """Response model for orchestrator processing"""
    singlish_raw: str = Field(..., description="Original raw transcript (Singlish/mixed)")
    clean_english: str = Field(..., description="Cleaned Standard English translation")
    sentiment: str = Field(..., description="Detected sentiment (e.g., positive, negative, neutral, frustrated)")
    tone: str = Field(..., description="Detected tone (e.g., casual, urgent, polite, annoyed)")


# ==================== HELPER FUNCTIONS ====================

def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Use OpenAI Whisper API to transcribe audio to text
    
    Args:
        audio_file: Audio file (mp3, wav, m4a, etc.)
    
    Returns:
        Transcribed text
    """
    try:
        client = get_openai_client()
        
        # Read audio file bytes
        audio_bytes = audio_file.file.read()
        
        # Reset file pointer for potential reuse
        audio_file.file.seek(0)
        
        # Create a temporary file-like object with proper filename
        from io import BytesIO
        audio_buffer = BytesIO(audio_bytes)
        audio_buffer.name = audio_file.filename or "audio.mp3"
        
        # Call Whisper API
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer,
            language="en"  # Singlish is English-based
        )
        
        return transcript.text
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )


def process_with_llm(raw_transcript: str) -> Dict[str, str]:
    """
    Process raw transcript with LLM to extract:
    - Cleaned Standard English
    - Sentiment
    - Tone
    
    Uses GPT-4 (or GPT-3.5-turbo as fallback)
    """
    try:
        client = get_openai_client()
        
        # Construct prompt for LLM
        system_prompt = """You are an expert in Singlish, Singaporean English, and Southeast Asian dialects.
Your task is to:
1. Translate Singlish/colloquial text into clear Standard English
2. Interpret slang, Malay, Hokkien, Tamil, and dialect words contextually
3. Preserve the original meaning and intent
4. Identify sentiment and tone

Output ONLY valid JSON with these exact keys:
{
  "clean_english": "<translated text>",
  "sentiment": "<positive/negative/neutral/frustrated/excited/etc>",
  "tone": "<casual/urgent/polite/annoyed/sarcastic/etc>"
}"""

        user_prompt = f"""Raw transcript: "{raw_transcript}"

Convert this to Standard English, then analyze sentiment and tone.
Output JSON only."""

        # Call GPT API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o-mini for cost efficiency, can upgrade to gpt-4 or gpt-4-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=500
        )
        
        # Extract response
        llm_output = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        try:
            parsed = json.loads(llm_output)
            return {
                "clean_english": parsed.get("clean_english", ""),
                "sentiment": parsed.get("sentiment", "neutral"),
                "tone": parsed.get("tone", "casual")
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "clean_english": llm_output,
                "sentiment": "neutral",
                "tone": "casual"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing with LLM: {str(e)}"
        )


# ==================== ENDPOINTS ====================

@router.get("/")
def orchestrator_info():
    """Get information about the Orchestrator module"""
    return {
        "module": "Orchestrator",
        "version": "2.0",
        "description": "Audio transcription + Singlish → English translation with sentiment analysis",
        "capabilities": [
            "Speech-to-text transcription (Whisper)",
            "Singlish to Standard English translation",
            "Multi-dialect interpretation (Malay, Hokkien, Tamil, etc.)",
            "Sentiment analysis",
            "Tone detection"
        ],
        "endpoints": {
            "process_audio": "POST /api/orchestrator/process - Upload audio file",
            "process_text": "POST /api/orchestrator/process/text - Submit text transcript",
            "test": "POST /api/orchestrator/test - Quick test endpoint"
        },
        "models": {
            "stt": "OpenAI Whisper",
            "llm": "GPT-4o-mini (configurable)"
        },
        "status": "ready"
    }


@router.post("/process", response_model=TranscriptionResponse)
async def process_audio(
    audio: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None)
):
    """
    Main orchestrator endpoint - processes audio OR text
    
    Input:
    - audio: Audio file (mp3, wav, m4a, etc.) - optional
    - transcript: Text transcript - optional
    
    At least one of audio or transcript must be provided.
    
    Output:
    - singlish_raw: Original transcript
    - clean_english: Cleaned Standard English
    - sentiment: Detected sentiment
    - tone: Detected tone
    """
    
    # Validate input
    if not audio and not transcript:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'audio' file or 'transcript' text"
        )
    
    try:
        # Step 1: Get raw transcript
        if transcript:
            # Use provided transcript
            raw_transcript = transcript
        elif audio:
            # Transcribe audio with Whisper
            raw_transcript = transcribe_audio(audio)
        else:
            raise HTTPException(status_code=400, detail="Invalid input")
        
        # Step 2: Process with LLM
        llm_result = process_with_llm(raw_transcript)
        
        # Step 3: Return result
        return TranscriptionResponse(
            singlish_raw=raw_transcript,
            clean_english=llm_result["clean_english"],
            sentiment=llm_result["sentiment"],
            tone=llm_result["tone"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/process/text", response_model=TranscriptionResponse)
def process_text(request: TranscriptRequest):
    """
    Process text-only transcript (no audio)
    Convenience endpoint for JSON requests
    
    Input:
    {
      "transcript": "walao this uncle cut queue sia"
    }
    
    Output:
    {
      "singlish_raw": "walao this uncle cut queue sia",
      "clean_english": "Oh my, this man cut in line.",
      "sentiment": "frustrated",
      "tone": "annoyed"
    }
    """
    try:
        # Process with LLM
        llm_result = process_with_llm(request.transcript)
        
        return TranscriptionResponse(
            singlish_raw=request.transcript,
            clean_english=llm_result["clean_english"],
            sentiment=llm_result["sentiment"],
            tone=llm_result["tone"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text: {str(e)}"
        )


@router.post("/test")
def test_orchestrator():
    """
    Test endpoint with predefined Singlish example
    Tests the LLM processing without requiring audio/transcript input
    """
    test_transcript = "walao this uncle cut queue sia"
    
    try:
        llm_result = process_with_llm(test_transcript)
        
        return {
            "success": True,
            "test_input": test_transcript,
            "result": {
                "singlish_raw": test_transcript,
                "clean_english": llm_result["clean_english"],
                "sentiment": llm_result["sentiment"],
                "tone": llm_result["tone"]
            },
            "message": "Test completed successfully!"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Test failed. Check OpenAI API key configuration."
        }


# ==================== INTERNAL HELPER (for other agents) ====================

async def internal_process(audio_file=None, transcript_text=None) -> Dict[str, str]:
    """
    Internal function for other agents to call
    
    Usage from other agents:
        from app.ochestrator.routes import internal_process
        result = await internal_process(transcript_text="some singlish text")
    
    Returns:
        {
            "singlish_raw": str,
            "clean_english": str,
            "sentiment": str,
            "tone": str
        }
    """
    if not audio_file and not transcript_text:
        raise ValueError("Must provide either audio_file or transcript_text")
    
    # Get raw transcript
    if transcript_text:
        raw = transcript_text
    elif audio_file:
        raw = transcribe_audio(audio_file)
    else:
        raise ValueError("Invalid input")
    
    # Process with LLM
    llm_result = process_with_llm(raw)
    
    return {
        "singlish_raw": raw,
        "clean_english": llm_result["clean_english"],
        "sentiment": llm_result["sentiment"],
        "tone": llm_result["tone"]
    }
