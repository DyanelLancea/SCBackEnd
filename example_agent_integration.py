"""
Example: How Other Agents Can Call the Orchestrator
Demonstrates internal integration patterns
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

# Import the orchestrator's internal function
from app.ochestrator.routes import internal_process

router = APIRouter()


# ==================== EXAMPLE 1: Wellness Agent Integration ====================

class WellnessMessage(BaseModel):
    """Wellness agent message"""
    user_id: str
    message: str  # Could be Singlish


@router.post("/wellness/analyze")
async def analyze_wellness_message(request: WellnessMessage):
    """
    Wellness agent endpoint that processes user messages
    Uses orchestrator to clean Singlish → English before analysis
    """
    
    # Step 1: Use orchestrator to clean the message
    orchestrator_result = await internal_process(
        transcript_text=request.message
    )
    
    # Step 2: Use cleaned English for wellness analysis
    clean_text = orchestrator_result["clean_english"]
    sentiment = orchestrator_result["sentiment"]
    
    # Step 3: Wellness-specific logic
    wellness_score = calculate_wellness_score(sentiment)
    
    return {
        "success": True,
        "user_id": request.user_id,
        "original_message": orchestrator_result["singlish_raw"],
        "cleaned_message": clean_text,
        "sentiment": sentiment,
        "tone": orchestrator_result["tone"],
        "wellness_score": wellness_score,
        "recommendation": generate_wellness_recommendation(sentiment)
    }


def calculate_wellness_score(sentiment: str) -> int:
    """Calculate wellness score based on sentiment"""
    sentiment_map = {
        "positive": 80,
        "excited": 90,
        "neutral": 60,
        "frustrated": 40,
        "negative": 30,
        "angry": 20
    }
    return sentiment_map.get(sentiment.lower(), 50)


def generate_wellness_recommendation(sentiment: str) -> str:
    """Generate wellness recommendation"""
    if sentiment.lower() in ["frustrated", "negative", "angry"]:
        return "Consider taking a short break or engaging in a calming activity."
    elif sentiment.lower() in ["positive", "excited"]:
        return "Great mood! Keep up the positive energy!"
    else:
        return "Take care of yourself today."


# ==================== EXAMPLE 2: Safety Agent Integration ====================

class SafetyAlert(BaseModel):
    """Safety alert with audio or text"""
    user_id: str
    alert_message: Optional[str] = None


@router.post("/safety/emergency-voice")
async def emergency_voice_alert(
    user_id: str,
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = None
):
    """
    Safety agent that processes emergency voice messages
    Transcribes audio and extracts emergency keywords
    """
    
    # Step 1: Use orchestrator to get clean text
    orchestrator_result = await internal_process(
        audio_file=audio if audio else None,
        transcript_text=text if text else None
    )
    
    clean_text = orchestrator_result["clean_english"].lower()
    tone = orchestrator_result["tone"]
    
    # Step 2: Detect emergency keywords
    emergency_keywords = ["help", "emergency", "danger", "accident", "hurt", "injured"]
    is_emergency = any(keyword in clean_text for keyword in emergency_keywords)
    
    # Step 3: Assess urgency based on tone
    urgent_tones = ["urgent", "panicked", "distressed", "anxious"]
    is_urgent = tone.lower() in urgent_tones
    
    # Step 4: Return safety assessment
    return {
        "success": True,
        "user_id": user_id,
        "transcript": orchestrator_result["singlish_raw"],
        "cleaned_text": clean_text,
        "is_emergency": is_emergency,
        "urgency_level": "HIGH" if is_urgent else "MEDIUM" if is_emergency else "LOW",
        "tone": tone,
        "sentiment": orchestrator_result["sentiment"],
        "action_taken": "Notifying caregivers" if is_emergency else "Monitoring"
    }


# ==================== EXAMPLE 3: Events Agent Integration ====================

class EventFeedback(BaseModel):
    """Event feedback"""
    event_id: str
    user_id: str
    feedback: str  # Singlish feedback


@router.post("/events/feedback")
async def process_event_feedback(request: EventFeedback):
    """
    Events agent that processes user feedback
    Translates Singlish feedback to English for storage and analysis
    """
    
    # Step 1: Clean the feedback using orchestrator
    orchestrator_result = await internal_process(
        transcript_text=request.feedback
    )
    
    # Step 2: Store both versions
    feedback_data = {
        "event_id": request.event_id,
        "user_id": request.user_id,
        "original_feedback": orchestrator_result["singlish_raw"],
        "cleaned_feedback": orchestrator_result["clean_english"],
        "sentiment": orchestrator_result["sentiment"],
        "tone": orchestrator_result["tone"]
    }
    
    # Step 3: Calculate event satisfaction
    satisfaction = calculate_satisfaction(orchestrator_result["sentiment"])
    
    return {
        "success": True,
        "feedback_received": True,
        "data": feedback_data,
        "satisfaction_score": satisfaction,
        "message": "Thank you for your feedback!"
    }


def calculate_satisfaction(sentiment: str) -> str:
    """Map sentiment to satisfaction level"""
    sentiment_lower = sentiment.lower()
    if sentiment_lower in ["positive", "excited", "happy"]:
        return "SATISFIED"
    elif sentiment_lower in ["neutral", "calm"]:
        return "NEUTRAL"
    else:
        return "UNSATISFIED"


# ==================== EXAMPLE 4: Direct Python Usage ====================

async def example_standalone_usage():
    """
    Example of using orchestrator in any Python code
    (not in a route handler)
    """
    
    # Example 1: Process text
    result = await internal_process(
        transcript_text="wah lau eh this event damn fun sia!"
    )
    
    print(f"Original: {result['singlish_raw']}")
    print(f"English: {result['clean_english']}")
    print(f"Sentiment: {result['sentiment']}")
    
    # Example 2: Process with audio file object
    # (Assuming you have an UploadFile object from FastAPI)
    # result = await internal_process(audio_file=audio_file_object)


# ==================== USAGE SUMMARY ====================

"""
ORCHESTRATOR INTERNAL API USAGE:

1. Import the function:
   from app.ochestrator.routes import internal_process

2. Call with text:
   result = await internal_process(transcript_text="some singlish text")

3. Call with audio:
   result = await internal_process(audio_file=upload_file_object)

4. Use the result:
   result["singlish_raw"]    # Original transcript
   result["clean_english"]    # Cleaned English translation
   result["sentiment"]        # Detected sentiment
   result["tone"]            # Detected tone

BENEFITS:
- Consistent Singlish handling across all agents
- Automatic sentiment/tone analysis
- Centralized audio transcription
- Reduces code duplication
- Easy to maintain and upgrade

WHEN TO USE:
- User provides Singlish input
- Voice/audio input needs transcription
- Sentiment analysis needed
- Tone detection required
- Standardizing colloquial input
"""


# ==================== TEST THE INTEGRATION ====================

if __name__ == "__main__":
    """
    To test this integration:
    
    1. Start the backend:
       python -m app.main
    
    2. Send a request:
       curl -X POST "http://localhost:8000/wellness/analyze" \
         -H "Content-Type: application/json" \
         -d '{"user_id": "123", "message": "wah lau I feel so tired sia"}'
    
    3. Expected response:
       {
         "success": true,
         "cleaned_message": "Wow, I feel so tired.",
         "sentiment": "negative",
         "wellness_score": 30,
         "recommendation": "Consider taking a short break..."
       }
    """
    print("This is an example file. See docstrings for usage.")

