"""
Events API Routes
Create, read, update, and delete events with Supabase
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time

from app.shared.supabase import get_supabase_client


router = APIRouter()


# ==================== REQUEST MODELS ====================

class EventCreate(BaseModel):
    """Model for creating a new event"""
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    date: str = Field(..., description="Event date (YYYY-MM-DD)")
    time: str = Field(..., description="Event time (HH:MM)")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum number of participants")
    created_by: Optional[str] = Field(None, description="User ID who created the event")


class EventUpdate(BaseModel):
    """Model for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    max_participants: Optional[int] = Field(None, ge=1)


class EventRegistration(BaseModel):
    """Model for registering to an event"""
    event_id: str = Field(..., description="Event ID")
    user_id: str = Field(..., description="User ID registering for the event")


# ==================== HELPER FUNCTIONS ====================

def validate_date_format(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_time_format(time_str: str) -> bool:
    """Validate time format (HH:MM)"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


# ==================== EVENT ENDPOINTS ====================

@router.get("/")
def events_info():
    """Get information about the Events module"""
    return {
        "module": "Events",
        "description": "Create, manage, and register for community events",
        "endpoints": {
            "list_events": "GET /api/events/list",
            "get_event": "GET /api/events/{event_id}",
            "create_event": "POST /api/events/create",
            "update_event": "PUT /api/events/{event_id}",
            "delete_event": "DELETE /api/events/{event_id}",
            "register": "POST /api/events/register",
            "participants": "GET /api/events/{event_id}/participants"
        }
    }


@router.get("/list")
def get_events(
    date_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get all events with optional filters
    
    Parameters:
    - date_filter: Filter by date (YYYY-MM-DD) or special values ('today', 'upcoming')
    - limit: Maximum number of events to return (default: 50)
    - offset: Number of events to skip (default: 0)
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table('events').select('*')
        
        # Apply filters
        if date_filter == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            query = query.eq('date', today)
        elif date_filter == "upcoming":
            today = datetime.now().strftime("%Y-%m-%d")
            query = query.gte('date', today)
        elif date_filter:
            # Specific date filter
            if validate_date_format(date_filter):
                query = query.eq('date', date_filter)
            else:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Order by date and time
        query = query.order('date', desc=False).order('time', desc=False)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        return {
            "success": True,
            "events": response.data,
            "count": len(response.data),
            "filter": date_filter or "all",
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching events: {str(e)}"
        )


@router.get("/{event_id}")
def get_event(event_id: str):
    """
    Get a specific event by ID
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('events').select('*').eq('id', event_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {
            "success": True,
            "event": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching event: {str(e)}"
        )


@router.post("/create")
def create_event(event: EventCreate):
    """
    Create a new event
    """
    try:
        # Validate date and time formats
        if not validate_date_format(event.date):
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        if not validate_time_format(event.time):
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM (24-hour format)"
            )
        
        supabase = get_supabase_client()
        
        # Prepare event data
        event_data = {
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "time": event.time,
            "location": event.location,
            "max_participants": event.max_participants,
            "created_by": event.created_by
        }
        
        # Insert into Supabase
        response = supabase.table('events').insert(event_data).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create event"
            )
        
        return {
            "success": True,
            "message": "Event created successfully!",
            "event": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating event: {str(e)}"
        )


@router.put("/{event_id}")
def update_event(event_id: str, event_update: EventUpdate):
    """
    Update an existing event
    """
    try:
        supabase = get_supabase_client()
        
        # Check if event exists
        existing = supabase.table('events').select('*').eq('id', event_id).execute()
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Prepare update data (only include provided fields)
        update_data = {}
        if event_update.title is not None:
            update_data["title"] = event_update.title
        if event_update.description is not None:
            update_data["description"] = event_update.description
        if event_update.date is not None:
            if not validate_date_format(event_update.date):
                raise HTTPException(status_code=400, detail="Invalid date format")
            update_data["date"] = event_update.date
        if event_update.time is not None:
            if not validate_time_format(event_update.time):
                raise HTTPException(status_code=400, detail="Invalid time format")
            update_data["time"] = event_update.time
        if event_update.location is not None:
            update_data["location"] = event_update.location
        if event_update.max_participants is not None:
            update_data["max_participants"] = event_update.max_participants
        
        # Update in Supabase
        response = supabase.table('events').update(update_data).eq('id', event_id).execute()
        
        return {
            "success": True,
            "message": "Event updated successfully!",
            "event": response.data[0] if response.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating event: {str(e)}"
        )


@router.delete("/{event_id}")
def delete_event(event_id: str):
    """
    Delete an event
    """
    try:
        supabase = get_supabase_client()
        
        # Check if event exists
        existing = supabase.table('events').select('*').eq('id', event_id).execute()
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Delete from Supabase
        response = supabase.table('events').delete().eq('id', event_id).execute()
        
        return {
            "success": True,
            "message": "Event deleted successfully!",
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting event: {str(e)}"
        )


# ==================== EVENT REGISTRATION ENDPOINTS ====================

@router.post("/register")
def register_for_event(registration: EventRegistration):
    """
    Register a user for an event
    """
    try:
        supabase = get_supabase_client()
        
        # Check if event exists
        event = supabase.table('events').select('*').eq('id', registration.event_id).execute()
        if not event.data or len(event.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if already registered
        existing = supabase.table('event_registrations').select('*').eq(
            'event_id', registration.event_id
        ).eq('user_id', registration.user_id).execute()
        
        if existing.data and len(existing.data) > 0:
            return {
                "success": True,
                "message": "Already registered for this event",
                "already_registered": True,
                "registration": existing.data[0]
            }
        
        # Create registration
        registration_data = {
            "event_id": registration.event_id,
            "user_id": registration.user_id
        }
        
        response = supabase.table('event_registrations').insert(registration_data).execute()
        
        return {
            "success": True,
            "message": "Successfully registered for event!",
            "registration": response.data[0] if response.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registering for event: {str(e)}"
        )


@router.delete("/register/{event_id}/{user_id}")
def unregister_from_event(event_id: str, user_id: str):
    """
    Unregister a user from an event
    """
    try:
        supabase = get_supabase_client()
        
        # Check if registration exists
        existing = supabase.table('event_registrations').select('*').eq(
            'event_id', event_id
        ).eq('user_id', user_id).execute()
        
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Delete registration
        response = supabase.table('event_registrations').delete().eq(
            'event_id', event_id
        ).eq('user_id', user_id).execute()
        
        return {
            "success": True,
            "message": "Successfully unregistered from event",
            "event_id": event_id,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering from event: {str(e)}"
        )


@router.get("/{event_id}/participants")
def get_event_participants(event_id: str):
    """
    Get list of participants registered for an event
    """
    try:
        supabase = get_supabase_client()
        
        # Check if event exists
        event = supabase.table('events').select('*').eq('id', event_id).execute()
        if not event.data or len(event.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get registrations
        response = supabase.table('event_registrations').select(
            '*'
        ).eq('event_id', event_id).execute()
        
        return {
            "success": True,
            "event_id": event_id,
            "participants": response.data,
            "count": len(response.data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching participants: {str(e)}"
        )

