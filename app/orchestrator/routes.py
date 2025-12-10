"""
Orchestrator Routes
Main coordinator and request routing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.shared.supabase import get_supabase_client


router = APIRouter()


# ==================== REQUEST MODELS ====================

class TextMessage(BaseModel):
    """Text message from user"""
    user_id: str
    message: str


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

