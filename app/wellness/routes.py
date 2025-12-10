"""
Wellness & Social Intelligence Routes
Social engagement, health management, and community activities
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.shared.supabase import get_supabase_client


router = APIRouter()


# ==================== REQUEST MODELS ====================

class ReminderCreate(BaseModel):
    """Create a new reminder"""
    user_id: str
    title: str
    description: Optional[str] = None
    reminder_type: str  # appointment, medication, hydration, exercise, custom
    scheduled_time: str  # ISO format datetime


# ==================== ENDPOINTS ====================

@router.get("/")
def wellness_info():
    """Get information about the Wellness module"""
    return {
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


@router.get("/reminders/{user_id}")
def get_reminders(user_id: str):
    """Get reminders for a user"""
    return {
        "success": True,
        "user_id": user_id,
        "reminders": [],
        "message": "Reminders feature - ready for implementation"
    }


@router.post("/reminders")
def create_reminder(reminder: ReminderCreate):
    """Create a new reminder"""
    return {
        "success": True,
        "message": "Reminder created",
        "reminder": reminder.dict()
    }


@router.get("/analytics/{user_id}")
def get_user_analytics(user_id: str):
    """Get user engagement analytics"""
    return {
        "success": True,
        "user_id": user_id,
        "analytics": {
            "events_registered": 0,
            "active_reminders": 0,
            "engagement_score": 0
        }
    }

