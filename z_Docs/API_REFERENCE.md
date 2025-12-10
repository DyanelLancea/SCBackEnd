# SC Backend - API Reference

Complete API documentation for frontend integration.

**Base URL**: `http://localhost:8000`

## Authentication
Currently, the API is open (no authentication required). Authentication can be added later using Supabase Auth.

## Response Format
All responses are in JSON format with the following structure:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

---

## Events API

### 1. Get Events List

**Endpoint**: `GET /api/events/list`

**Description**: Retrieve a list of events with optional filters

**Query Parameters**:
- `date_filter` (optional): Filter by date
  - `"today"` - Events happening today
  - `"upcoming"` - All future events
  - `"YYYY-MM-DD"` - Events on specific date
- `limit` (optional, default: 50): Maximum number of events
- `offset` (optional, default: 0): Pagination offset

**Example Request**:
```bash
GET /api/events/list?date_filter=upcoming&limit=10
```

**Example Response**:
```json
{
  "success": true,
  "events": [
    {
      "id": "uuid-here",
      "title": "Morning Yoga",
      "description": "Start your day with relaxing yoga",
      "date": "2025-12-15",
      "time": "09:00",
      "location": "Community Center",
      "max_participants": 20,
      "created_by": null,
      "created_at": "2025-12-10T12:00:00Z",
      "updated_at": "2025-12-10T12:00:00Z"
    }
  ],
  "count": 1,
  "filter": "upcoming",
  "limit": 10,
  "offset": 0
}
```

---

### 2. Get Single Event

**Endpoint**: `GET /api/events/{event_id}`

**Description**: Get details of a specific event

**Path Parameters**:
- `event_id` (required): UUID of the event

**Example Request**:
```bash
GET /api/events/123e4567-e89b-12d3-a456-426614174000
```

**Example Response**:
```json
{
  "success": true,
  "event": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Morning Yoga",
    "description": "Start your day with relaxing yoga",
    "date": "2025-12-15",
    "time": "09:00",
    "location": "Community Center",
    "max_participants": 20,
    "created_by": null,
    "created_at": "2025-12-10T12:00:00Z",
    "updated_at": "2025-12-10T12:00:00Z"
  }
}
```

**Error Response** (404):
```json
{
  "detail": "Event not found"
}
```

---

### 3. Create Event

**Endpoint**: `POST /api/events/create`

**Description**: Create a new event

**Request Body**:
```json
{
  "title": "string (required, max 200 chars)",
  "description": "string (optional, max 2000 chars)",
  "date": "YYYY-MM-DD (required)",
  "time": "HH:MM (required, 24-hour format)",
  "location": "string (optional, max 500 chars)",
  "max_participants": "integer (optional, min 1)",
  "created_by": "string (optional, user UUID)"
}
```

**Example Request**:
```json
{
  "title": "Community Gathering",
  "description": "Monthly community meetup for networking and fun",
  "date": "2025-12-20",
  "time": "15:00",
  "location": "Community Hall",
  "max_participants": 50
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Event created successfully!",
  "event": {
    "id": "new-uuid-here",
    "title": "Community Gathering",
    "description": "Monthly community meetup for networking and fun",
    "date": "2025-12-20",
    "time": "15:00",
    "location": "Community Hall",
    "max_participants": 50,
    "created_by": null,
    "created_at": "2025-12-10T14:30:00Z",
    "updated_at": "2025-12-10T14:30:00Z"
  }
}
```

**Error Response** (400):
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

---

### 4. Update Event

**Endpoint**: `PUT /api/events/{event_id}`

**Description**: Update an existing event (all fields optional)

**Path Parameters**:
- `event_id` (required): UUID of the event

**Request Body** (all fields optional):
```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "date": "YYYY-MM-DD (optional)",
  "time": "HH:MM (optional)",
  "location": "string (optional)",
  "max_participants": "integer (optional)"
}
```

**Example Request**:
```json
{
  "title": "Updated Event Title",
  "max_participants": 75
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Event updated successfully!",
  "event": {
    "id": "event-uuid",
    "title": "Updated Event Title",
    "description": "Original description",
    "date": "2025-12-20",
    "time": "15:00",
    "location": "Community Hall",
    "max_participants": 75,
    "created_by": null,
    "created_at": "2025-12-10T14:30:00Z",
    "updated_at": "2025-12-10T15:45:00Z"
  }
}
```

---

### 5. Delete Event

**Endpoint**: `DELETE /api/events/{event_id}`

**Description**: Delete an event

**Path Parameters**:
- `event_id` (required): UUID of the event

**Example Request**:
```bash
DELETE /api/events/123e4567-e89b-12d3-a456-426614174000
```

**Example Response**:
```json
{
  "success": true,
  "message": "Event deleted successfully!",
  "event_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

### 6. Register for Event

**Endpoint**: `POST /api/events/register`

**Description**: Register a user for an event

**Request Body**:
```json
{
  "event_id": "string (required, event UUID)",
  "user_id": "string (required, user UUID)"
}
```

**Example Request**:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-uuid-here"
}
```

**Example Response** (First Registration):
```json
{
  "success": true,
  "message": "Successfully registered for event!",
  "registration": {
    "id": "registration-uuid",
    "event_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user-uuid-here",
    "registered_at": "2025-12-10T16:00:00Z"
  }
}
```

**Example Response** (Already Registered):
```json
{
  "success": true,
  "message": "Already registered for this event",
  "already_registered": true,
  "registration": {
    "id": "registration-uuid",
    "event_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user-uuid-here",
    "registered_at": "2025-12-10T16:00:00Z"
  }
}
```

---

### 7. Unregister from Event

**Endpoint**: `DELETE /api/events/register/{event_id}/{user_id}`

**Description**: Cancel a user's registration for an event

**Path Parameters**:
- `event_id` (required): UUID of the event
- `user_id` (required): UUID of the user

**Example Request**:
```bash
DELETE /api/events/register/123e4567-e89b-12d3-a456-426614174000/user-uuid-here
```

**Example Response**:
```json
{
  "success": true,
  "message": "Successfully unregistered from event",
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-uuid-here"
}
```

---

### 8. Get Event Participants

**Endpoint**: `GET /api/events/{event_id}/participants`

**Description**: Get list of users registered for an event

**Path Parameters**:
- `event_id` (required): UUID of the event

**Example Request**:
```bash
GET /api/events/123e4567-e89b-12d3-a456-426614174000/participants
```

**Example Response**:
```json
{
  "success": true,
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "participants": [
    {
      "id": "registration-uuid-1",
      "event_id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "user-uuid-1",
      "registered_at": "2025-12-10T16:00:00Z"
    },
    {
      "id": "registration-uuid-2",
      "event_id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "user-uuid-2",
      "registered_at": "2025-12-10T17:30:00Z"
    }
  ],
  "count": 2
}
```

---

## Wellness API (Placeholder)

### Get Module Info
**Endpoint**: `GET /api/wellness/`

### Get User Reminders
**Endpoint**: `GET /api/wellness/reminders/{user_id}`

### Create Reminder
**Endpoint**: `POST /api/wellness/reminders`

**Request Body**:
```json
{
  "user_id": "string",
  "title": "string",
  "description": "string (optional)",
  "reminder_type": "appointment | medication | hydration | exercise | custom",
  "scheduled_time": "ISO datetime string"
}
```

---

## Safety API (Placeholder)

### Get Module Info
**Endpoint**: `GET /api/safety/`

### Trigger Emergency Alert
**Endpoint**: `POST /api/safety/emergency`

**Request Body**:
```json
{
  "user_id": "string",
  "alert_type": "fall | sos | health | wandering",
  "latitude": "number (optional)",
  "longitude": "number (optional)",
  "description": "string (optional)"
}
```

### Update Location
**Endpoint**: `POST /api/safety/location`

**Request Body**:
```json
{
  "user_id": "string",
  "latitude": "number",
  "longitude": "number",
  "address": "string (optional)"
}
```

---

## Orchestrator API (Placeholder)

### Get Module Info
**Endpoint**: `GET /api/orchestrator/`

### Process Message
**Endpoint**: `POST /api/orchestrator/message`

**Request Body**:
```json
{
  "user_id": "string",
  "message": "string"
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Internal Server Error |

---

## Frontend Integration Examples

### React/Next.js

```javascript
// api.js
const API_BASE_URL = 'http://localhost:8000';

export const eventsAPI = {
  // Get all events
  getAll: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${API_BASE_URL}/api/events/list?${params}`);
    return response.json();
  },

  // Get single event
  getById: async (id) => {
    const response = await fetch(`${API_BASE_URL}/api/events/${id}`);
    return response.json();
  },

  // Create event
  create: async (eventData) => {
    const response = await fetch(`${API_BASE_URL}/api/events/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData)
    });
    return response.json();
  },

  // Update event
  update: async (id, eventData) => {
    const response = await fetch(`${API_BASE_URL}/api/events/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData)
    });
    return response.json();
  },

  // Delete event
  delete: async (id) => {
    const response = await fetch(`${API_BASE_URL}/api/events/${id}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  // Register for event
  register: async (eventId, userId) => {
    const response = await fetch(`${API_BASE_URL}/api/events/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_id: eventId, user_id: userId })
    });
    return response.json();
  },

  // Get participants
  getParticipants: async (eventId) => {
    const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/participants`);
    return response.json();
  }
};
```

### Vue.js

```javascript
// eventService.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export default {
  getAllEvents(filters = {}) {
    return axios.get(`${API_BASE_URL}/api/events/list`, { params: filters });
  },

  getEvent(id) {
    return axios.get(`${API_BASE_URL}/api/events/${id}`);
  },

  createEvent(eventData) {
    return axios.post(`${API_BASE_URL}/api/events/create`, eventData);
  },

  registerForEvent(eventId, userId) {
    return axios.post(`${API_BASE_URL}/api/events/register`, {
      event_id: eventId,
      user_id: userId
    });
  }
};
```

---

## Testing with cURL

```bash
# Get all events
curl http://localhost:8000/api/events/list

# Get upcoming events
curl "http://localhost:8000/api/events/list?date_filter=upcoming"

# Create event
curl -X POST http://localhost:8000/api/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "date": "2025-12-25",
    "time": "10:00",
    "location": "Online"
  }'

# Register for event
curl -X POST http://localhost:8000/api/events/register \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "your-event-uuid",
    "user_id": "your-user-uuid"
  }'
```

---

## Need Help?

- **Interactive Docs**: Visit http://localhost:8000/docs for an interactive API explorer
- **OpenAPI Schema**: Available at http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

---

**Last Updated**: December 10, 2025

