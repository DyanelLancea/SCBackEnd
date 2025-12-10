# Frontend Integration Guide

**SC Backend API - Frontend Connection Instructions**

This guide provides everything your frontend team needs to connect to the SC Backend API.

---

## 📋 Quick Reference

| Item | Value |
|------|-------|
| **Backend URL (Local)** | `http://localhost:8000` |
| **API Base Path** | `/api` |
| **API Documentation** | `http://localhost:8000/docs` |
| **Health Check** | `http://localhost:8000/health` |
| **CORS** | Pre-configured for `localhost:3000`, `localhost:3001` |

---

## 🚀 Getting Started

### Prerequisites

1. **Backend must be running** on `http://localhost:8000`
   - Contact backend team or see `SETUP_GUIDE.md` to run locally
   - Verify by visiting: http://localhost:8000/health

2. **CORS is pre-configured** for common frontend ports:
   - `http://localhost:3000` (Next.js default)
   - `http://localhost:3001`
   - `http://127.0.0.1:3000`
   - `http://127.0.0.1:3001`
   - If you need a different port, request backend team to add it

---

## 🔌 API Connection Setup

### Step 1: Configure API Base URL

Create an environment variable file in your frontend project:

**For Next.js** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**For Vite/React** (`.env`):
```bash
VITE_API_URL=http://localhost:8000
```

**For Create React App** (`.env`):
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Step 2: Create API Service Layer

Create a centralized API service file to handle all backend requests.

#### JavaScript Version

**File**: `src/services/api.js` or `lib/api.js`

```javascript
// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'API request failed');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// API Methods
export const api = {
  // Health Check
  healthCheck: () => apiCall('/health'),

  // Events API
  events: {
    // Get all events with optional filters
    getAll: (filters = {}) => {
      const params = new URLSearchParams(filters);
      return apiCall(`/api/events/list?${params}`);
    },

    // Get single event by ID
    getById: (eventId) => apiCall(`/api/events/${eventId}`),

    // Create new event
    create: (eventData) => apiCall('/api/events/create', {
      method: 'POST',
      body: JSON.stringify(eventData),
    }),

    // Update event
    update: (eventId, eventData) => apiCall(`/api/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(eventData),
    }),

    // Delete event
    delete: (eventId) => apiCall(`/api/events/${eventId}`, {
      method: 'DELETE',
    }),

    // Register user for event
    register: (eventId, userId) => apiCall('/api/events/register', {
      method: 'POST',
      body: JSON.stringify({ event_id: eventId, user_id: userId }),
    }),

    // Unregister from event
    unregister: (eventId, userId) => apiCall(`/api/events/register/${eventId}/${userId}`, {
      method: 'DELETE',
    }),

    // Get event participants
    getParticipants: (eventId) => apiCall(`/api/events/${eventId}/participants`),
  },

  // Wellness API
  wellness: {
    // Get module info
    getInfo: () => apiCall('/api/wellness/'),

    // Get user reminders
    getReminders: (userId) => apiCall(`/api/wellness/reminders/${userId}`),

    // Create reminder
    createReminder: (reminderData) => apiCall('/api/wellness/reminders', {
      method: 'POST',
      body: JSON.stringify(reminderData),
    }),
  },

  // Safety API
  safety: {
    // Get module info
    getInfo: () => apiCall('/api/safety/'),

    // Trigger emergency alert
    triggerEmergency: (alertData) => apiCall('/api/safety/emergency', {
      method: 'POST',
      body: JSON.stringify(alertData),
    }),

    // Update location
    updateLocation: (locationData) => apiCall('/api/safety/location', {
      method: 'POST',
      body: JSON.stringify(locationData),
    }),
  },

  // Orchestrator API
  orchestrator: {
    // Get module info
    getInfo: () => apiCall('/api/orchestrator/'),

    // Send message
    sendMessage: (userId, message) => apiCall('/api/orchestrator/message', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, message }),
    }),
  },
};

export default api;
```

#### TypeScript Version (Recommended)

**File**: `src/services/api.ts` or `lib/api.ts`

```typescript
// types/api.ts - Create type definitions
export interface Event {
  id: string;
  title: string;
  description?: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM
  location?: string;
  max_participants?: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface EventsResponse {
  success: boolean;
  events: Event[];
  count: number;
  filter?: string;
  limit: number;
  offset: number;
}

export interface CreateEventData {
  title: string;
  description?: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM
  location?: string;
  max_participants?: number;
  created_by?: string;
}

export interface EventResponse {
  success: boolean;
  message: string;
  event: Event;
}

export interface Registration {
  id: string;
  event_id: string;
  user_id: string;
  registered_at: string;
}

export interface RegistrationResponse {
  success: boolean;
  message: string;
  registration: Registration;
  already_registered?: boolean;
}

export interface ApiError {
  detail: string;
}

// api.ts - API service
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error((data as ApiError).detail || 'API request failed');
    }
    
    return data as T;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

export const api = {
  healthCheck: () => apiCall<{ status: string; message: string; database: string }>('/health'),

  events: {
    getAll: (filters: Record<string, string> = {}) => {
      const params = new URLSearchParams(filters);
      return apiCall<EventsResponse>(`/api/events/list?${params}`);
    },

    getById: (eventId: string) => apiCall<EventResponse>(`/api/events/${eventId}`),

    create: (eventData: CreateEventData) => apiCall<EventResponse>('/api/events/create', {
      method: 'POST',
      body: JSON.stringify(eventData),
    }),

    update: (eventId: string, eventData: Partial<CreateEventData>) => 
      apiCall<EventResponse>(`/api/events/${eventId}`, {
        method: 'PUT',
        body: JSON.stringify(eventData),
      }),

    delete: (eventId: string) => apiCall<{ success: boolean; message: string; event_id: string }>(
      `/api/events/${eventId}`, 
      { method: 'DELETE' }
    ),

    register: (eventId: string, userId: string) => 
      apiCall<RegistrationResponse>('/api/events/register', {
        method: 'POST',
        body: JSON.stringify({ event_id: eventId, user_id: userId }),
      }),

    unregister: (eventId: string, userId: string) => 
      apiCall<{ success: boolean; message: string }>(
        `/api/events/register/${eventId}/${userId}`,
        { method: 'DELETE' }
      ),

    getParticipants: (eventId: string) => 
      apiCall<{ success: boolean; participants: Registration[]; count: number }>(
        `/api/events/${eventId}/participants`
      ),
  },

  // Add other modules...
};

export default api;
```

---

## 📖 Usage Examples

### React Hooks Example

```javascript
import { useState, useEffect } from 'react';
import { api } from '@/services/api';

export default function EventsList() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchEvents() {
      try {
        const data = await api.events.getAll({ date_filter: 'upcoming' });
        setEvents(data.events);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching events:', err);
      } finally {
        setLoading(false);
      }
    }
    
    fetchEvents();
  }, []);

  if (loading) return <div>Loading events...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Upcoming Events</h1>
      {events.length === 0 ? (
        <p>No upcoming events</p>
      ) : (
        events.map(event => (
          <div key={event.id} className="event-card">
            <h2>{event.title}</h2>
            <p>{event.description}</p>
            <p>📅 {event.date} at {event.time}</p>
            <p>📍 {event.location}</p>
          </div>
        ))
      )}
    </div>
  );
}
```

### Create Event Form Example

```javascript
import { useState } from 'react';
import { api } from '@/services/api';

export default function CreateEventForm() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: '',
    time: '',
    location: '',
    max_participants: 50,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const result = await api.events.create(formData);
      console.log('Event created:', result);
      alert('Event created successfully!');
      // Reset form or redirect
    } catch (error) {
      console.error('Error creating event:', error);
      alert('Failed to create event: ' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Event Title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        required
      />
      <textarea
        placeholder="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
      />
      <input
        type="date"
        value={formData.date}
        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
        required
      />
      <input
        type="time"
        value={formData.time}
        onChange={(e) => setFormData({ ...formData, time: e.target.value })}
        required
      />
      <input
        type="text"
        placeholder="Location"
        value={formData.location}
        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? 'Creating...' : 'Create Event'}
      </button>
    </form>
  );
}
```

### Event Registration Example

```javascript
import { useState } from 'react';
import { api } from '@/services/api';

export function RegisterButton({ eventId, userId }) {
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    setLoading(true);
    try {
      const result = await api.events.register(eventId, userId);
      setRegistered(true);
      alert(result.message);
    } catch (error) {
      alert('Registration failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUnregister = async () => {
    setLoading(true);
    try {
      await api.events.unregister(eventId, userId);
      setRegistered(false);
      alert('Successfully unregistered');
    } catch (error) {
      alert('Unregistration failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={registered ? handleUnregister : handleRegister}
      disabled={loading}
    >
      {loading ? 'Processing...' : registered ? 'Unregister' : 'Register'}
    </button>
  );
}
```

---

## 🔍 API Endpoints Reference

### Events Module

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/events/list` | GET | Get all events | `date_filter`, `limit`, `offset` |
| `/api/events/{id}` | GET | Get single event | `id` (path) |
| `/api/events/create` | POST | Create event | Event data (body) |
| `/api/events/{id}` | PUT | Update event | `id` (path), data (body) |
| `/api/events/{id}` | DELETE | Delete event | `id` (path) |
| `/api/events/register` | POST | Register for event | `event_id`, `user_id` (body) |
| `/api/events/register/{event_id}/{user_id}` | DELETE | Unregister | `event_id`, `user_id` (path) |
| `/api/events/{id}/participants` | GET | Get participants | `id` (path) |

### Wellness Module

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wellness/` | GET | Module info |
| `/api/wellness/reminders/{user_id}` | GET | Get user reminders |
| `/api/wellness/reminders` | POST | Create reminder |

### Safety Module

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/safety/` | GET | Module info |
| `/api/safety/emergency` | POST | Trigger emergency |
| `/api/safety/location` | POST | Update location |

### Orchestrator Module

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/orchestrator/` | GET | Module info |
| `/api/orchestrator/message` | POST | Send message |

---

## 📝 Request/Response Examples

### Create Event

**Request:**
```json
POST /api/events/create
Content-Type: application/json

{
  "title": "Community Gathering",
  "description": "Monthly meetup for networking",
  "date": "2025-12-20",
  "time": "15:00",
  "location": "Community Hall",
  "max_participants": 50
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event created successfully!",
  "event": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Community Gathering",
    "description": "Monthly meetup for networking",
    "date": "2025-12-20",
    "time": "15:00",
    "location": "Community Hall",
    "max_participants": 50,
    "created_by": null,
    "created_at": "2025-12-10T10:00:00Z",
    "updated_at": "2025-12-10T10:00:00Z"
  }
}
```

### Get Events List

**Request:**
```
GET /api/events/list?date_filter=upcoming&limit=10
```

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Morning Yoga",
      "description": "Relaxing yoga session",
      "date": "2025-12-15",
      "time": "09:00",
      "location": "Community Center",
      "max_participants": 20,
      "created_by": null,
      "created_at": "2025-12-10T10:00:00Z",
      "updated_at": "2025-12-10T10:00:00Z"
    }
  ],
  "count": 1,
  "filter": "upcoming",
  "limit": 10,
  "offset": 0
}
```

### Register for Event

**Request:**
```json
POST /api/events/register
Content-Type: application/json

{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-uuid-here"
}
```

**Response (First time):**
```json
{
  "success": true,
  "message": "Successfully registered for event!",
  "registration": {
    "id": "reg-uuid",
    "event_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user-uuid-here",
    "registered_at": "2025-12-10T11:00:00Z"
  }
}
```

**Response (Already registered):**
```json
{
  "success": true,
  "message": "Already registered for this event",
  "already_registered": true,
  "registration": {
    "id": "reg-uuid",
    "event_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user-uuid-here",
    "registered_at": "2025-12-10T11:00:00Z"
  }
}
```

---

## 🛠️ Error Handling

### Error Response Format

All errors follow this format:
```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input, check request data |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Backend issue, contact backend team |

### Recommended Error Handling Pattern

```javascript
async function safeApiCall(apiFunction, errorMessage = 'An error occurred') {
  try {
    return await apiFunction();
  } catch (error) {
    console.error(errorMessage, error);
    // Show user-friendly error
    alert(errorMessage + ': ' + error.message);
    // Optional: Send to error tracking service
    // trackError(error);
    throw error;
  }
}

// Usage
const events = await safeApiCall(
  () => api.events.getAll(),
  'Failed to load events'
);
```

---

## 🧪 Testing the Connection

### 1. Quick Browser Test

Open browser console and run:
```javascript
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('✅ Backend connected:', data))
  .catch(err => console.error('❌ Connection failed:', err));
```

### 2. Test Component

Create a test page to verify connection:

```javascript
import { useEffect, useState } from 'react';
import { api } from '@/services/api';

export default function ConnectionTest() {
  const [status, setStatus] = useState('Testing...');

  useEffect(() => {
    async function testConnection() {
      try {
        const health = await api.healthCheck();
        setStatus(`✅ Connected! Status: ${health.status}`);
      } catch (error) {
        setStatus(`❌ Connection failed: ${error.message}`);
      }
    }
    testConnection();
  }, []);

  return (
    <div>
      <h1>Backend Connection Test</h1>
      <p>{status}</p>
    </div>
  );
}
```

---

## 🚨 Troubleshooting

### Issue: CORS Error

**Error Message**: 
```
Access to fetch at 'http://localhost:8000/api/events/list' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution**: 
- Your frontend port is not in the allowed origins list
- Contact backend team to add your port (e.g., `http://localhost:5173`)
- Backend file to update: `app/main.py` (lines 56-68)

### Issue: Connection Refused

**Error Message**: `Failed to fetch` or `net::ERR_CONNECTION_REFUSED`

**Solution**:
1. Verify backend is running: Visit http://localhost:8000/health
2. Check if backend is on correct port (should be 8000)
3. Backend team: Run `python -m app.main` or `start.bat`

### Issue: 404 Not Found

**Error Message**: `{"detail": "Endpoint not found"}`

**Solution**:
- Check endpoint URL is correct (case-sensitive)
- Verify API path includes `/api/` prefix
- Example: `/api/events/list` not `/events/list`

### Issue: 400 Bad Request

**Error Message**: `{"detail": "Invalid date format. Use YYYY-MM-DD"}`

**Solution**:
- Check request data format matches API requirements
- Date format: `YYYY-MM-DD` (e.g., "2025-12-20")
- Time format: `HH:MM` (e.g., "15:00")
- Required fields must be included

---

## 📚 Additional Resources

### Interactive API Documentation

Visit http://localhost:8000/docs for:
- Interactive endpoint testing
- Request/response schemas
- Try endpoints directly from browser

### Backend Documentation Files

- `API_REFERENCE.md` - Detailed API documentation
- `PROJECT_SUMMARY.md` - Project overview
- `SETUP_GUIDE.md` - Backend setup instructions

### Contact Backend Team

If you need:
- Additional CORS origins
- New API endpoints
- Bug fixes or support
- Database schema changes

---

## 🔐 Production Deployment

When deploying to production:

### 1. Update Environment Variables

```bash
# Production frontend .env
NEXT_PUBLIC_API_URL=https://api.yourapp.com
```

### 2. Backend Requirements

- Request backend team to:
  - Add production frontend URL to CORS
  - Update Supabase to production instance
  - Enable HTTPS
  - Remove development-only CORS wildcards

### 3. Security Considerations

- Never expose API keys in frontend code
- Use environment variables for all configuration
- Implement proper authentication when ready
- Use HTTPS for all production requests

---

## ✅ Quick Checklist

Before starting frontend development:

- [ ] Backend is running on http://localhost:8000
- [ ] Can access http://localhost:8000/health
- [ ] Created `.env.local` with `NEXT_PUBLIC_API_URL`
- [ ] Created `api.js` or `api.ts` service file
- [ ] Tested connection from browser console
- [ ] Reviewed API endpoints in interactive docs
- [ ] Understood request/response formats
- [ ] Set up error handling

---

**Last Updated**: December 10, 2025

**Backend Version**: 2.0.0

**Questions?** Contact the backend team or check http://localhost:8000/docs

