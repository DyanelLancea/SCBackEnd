# Orchestrator Agent - Frontend Integration Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Base Configuration](#base-configuration)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Frontend Integration Code](#frontend-integration-code)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## 🤖 Overview

The **Orchestrator Agent** is the main coordinator and intelligent routing system for the SC Backend API. It processes natural language messages from users and routes them to the appropriate specialized agents (Events, Safety, Wellness).

**Base URL (Development):** `http://localhost:8000/api/orchestrator`  
**Base URL (Production):** `https://your-production-url.com/api/orchestrator`

**Capabilities:**
- Natural language understanding
- Intent classification (find_events, emergency, general)
- Request routing to specialized modules
- Conversation management

---

## ⚙️ Base Configuration

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:3000` (Next.js default)
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

### Required Headers
```javascript
{
  "Content-Type": "application/json"
}
```

---

## 🔐 Authentication

**Current Status:** No authentication required for development.

**Future Implementation:** Authentication will be added. You'll need to include:
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

---

## 📡 Endpoints

### 1. Get Orchestrator Information
**Endpoint:** `GET /api/orchestrator/`  
**Purpose:** Get information about the orchestrator module, its capabilities, and available endpoints.

**Request:** No body required

**Response:**
```json
{
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
```

---

### 2. Process User Message (Main Endpoint) ⭐
**Endpoint:** `POST /api/orchestrator/message`  
**Purpose:** Send a user message for intent detection and routing.

**Request Body:**
```typescript
{
  user_id: string;    // Required: Unique identifier for the user
  message: string;    // Required: The user's message text
}
```

**Response:**
```typescript
{
  success: boolean;       // Always true if no error
  intent: string;        // Detected intent: "find_events" | "emergency" | "general"
  message: string;       // Response message with routing suggestion
  user_id: string;       // Echo of the user_id from request
}
```

**Intent Types:**
- `find_events` - Triggered by: "event", "activity", "happening"
- `emergency` - Triggered by: "help", "emergency", "sos"
- `general` - Default for all other messages

---

### 3. Get Conversation History
**Endpoint:** `GET /api/orchestrator/history/{user_id}`  
**Purpose:** Retrieve conversation history for a specific user.

**URL Parameters:**
- `user_id` (required): The user's unique identifier

**Query Parameters:**
- `limit` (optional): Number of conversations to return (default: 20)

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "conversations": [],
  "count": 0,
  "message": "Conversation history - ready for implementation"
}
```

**Note:** This endpoint is currently a placeholder and will be implemented with full conversation storage.

---

## 💻 Request/Response Examples

### Example 1: Detecting Event Intent

**Request:**
```bash
POST /api/orchestrator/message
Content-Type: application/json

{
  "user_id": "user_123",
  "message": "What events are happening this weekend?"
}
```

**Response:**
```json
{
  "success": true,
  "intent": "find_events",
  "message": "Looking for events! Check /api/events/list for available events.",
  "user_id": "user_123"
}
```

---

### Example 2: Detecting Emergency Intent

**Request:**
```bash
POST /api/orchestrator/message
Content-Type: application/json

{
  "user_id": "user_456",
  "message": "Help! I need emergency assistance"
}
```

**Response:**
```json
{
  "success": true,
  "intent": "emergency",
  "message": "Emergency detected! Check /api/safety/emergency for emergency features.",
  "user_id": "user_456"
}
```

---

### Example 3: General Conversation

**Request:**
```bash
POST /api/orchestrator/message
Content-Type: application/json

{
  "user_id": "user_789",
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "success": true,
  "intent": "general",
  "message": "I can help you find events, manage reminders, or handle emergencies!",
  "user_id": "user_789"
}
```

---

## 🎨 Frontend Integration Code

### React/Next.js Implementation

#### 1. Create API Client (Recommended Approach)

**`lib/api/orchestrator.ts`**
```typescript
// Type definitions
export interface OrchestratorMessageRequest {
  user_id: string;
  message: string;
}

export interface OrchestratorMessageResponse {
  success: boolean;
  intent: 'find_events' | 'emergency' | 'general';
  message: string;
  user_id: string;
}

export interface ConversationHistoryResponse {
  success: boolean;
  user_id: string;
  conversations: any[]; // Will be defined when implemented
  count: number;
  message: string;
}

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ORCHESTRATOR_BASE = `${API_BASE_URL}/api/orchestrator`;

// API Functions
export class OrchestratorAPI {
  /**
   * Get orchestrator information
   */
  static async getInfo() {
    const response = await fetch(`${ORCHESTRATOR_BASE}/`);
    if (!response.ok) {
      throw new Error('Failed to fetch orchestrator info');
    }
    return response.json();
  }

  /**
   * Send a message to the orchestrator for intent detection
   */
  static async sendMessage(
    userId: string,
    message: string
  ): Promise<OrchestratorMessageResponse> {
    const response = await fetch(`${ORCHESTRATOR_BASE}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        message: message,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to process message');
    }

    return response.json();
  }

  /**
   * Get conversation history for a user
   */
  static async getHistory(
    userId: string,
    limit: number = 20
  ): Promise<ConversationHistoryResponse> {
    const response = await fetch(
      `${ORCHESTRATOR_BASE}/history/${userId}?limit=${limit}`
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversation history');
    }

    return response.json();
  }
}
```

---

#### 2. React Hook for Orchestrator

**`hooks/useOrchestrator.ts`**
```typescript
import { useState } from 'react';
import { OrchestratorAPI, OrchestratorMessageResponse } from '@/lib/api/orchestrator';

export function useOrchestrator(userId: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<OrchestratorMessageResponse | null>(null);

  const sendMessage = async (message: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await OrchestratorAPI.sendMessage(userId, message);
      setResponse(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getHistory = async (limit?: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await OrchestratorAPI.getHistory(userId, limit);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    sendMessage,
    getHistory,
    loading,
    error,
    response,
  };
}
```

---

#### 3. Chat Component Example

**`components/ChatWithOrchestrator.tsx`**
```typescript
'use client';

import { useState } from 'react';
import { useOrchestrator } from '@/hooks/useOrchestrator';

export default function ChatWithOrchestrator({ userId }: { userId: string }) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{
    sender: 'user' | 'bot';
    text: string;
    intent?: string;
  }>>([]);

  const { sendMessage, loading, error } = useOrchestrator(userId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim()) return;

    // Add user message to chat
    const userMessage = message;
    setChatHistory(prev => [...prev, { sender: 'user', text: userMessage }]);
    setMessage('');

    try {
      // Send to orchestrator
      const response = await sendMessage(userMessage);
      
      // Add bot response to chat
      setChatHistory(prev => [...prev, {
        sender: 'bot',
        text: response.message,
        intent: response.intent,
      }]);

      // Handle routing based on intent
      handleIntentRouting(response.intent);
      
    } catch (err) {
      console.error('Failed to send message:', err);
      setChatHistory(prev => [...prev, {
        sender: 'bot',
        text: 'Sorry, I encountered an error. Please try again.',
      }]);
    }
  };

  const handleIntentRouting = (intent: string) => {
    // Route to appropriate page/component based on intent
    switch (intent) {
      case 'find_events':
        console.log('Routing to events page...');
        // router.push('/events');
        break;
      case 'emergency':
        console.log('Triggering emergency protocol...');
        // router.push('/emergency');
        break;
      case 'general':
        console.log('General conversation');
        break;
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto p-4">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {chatHistory.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-4 py-2 rounded-lg ${
                msg.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {msg.text}
              {msg.intent && (
                <div className="text-xs mt-1 opacity-75">
                  Intent: {msg.intent}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 px-4 py-2 rounded-lg">
              Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4">
          {error}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
```

---

#### 4. Simple Fetch Example (Vanilla JavaScript)

```javascript
// Send a message to orchestrator
async function sendMessageToOrchestrator(userId, message) {
  try {
    const response = await fetch('http://localhost:8000/api/orchestrator/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Intent detected:', data.intent);
    console.log('Response:', data.message);
    
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage
sendMessageToOrchestrator('user_123', 'What events are happening today?')
  .then(response => {
    if (response.intent === 'find_events') {
      // Redirect to events page
      window.location.href = '/events';
    }
  });
```

---

#### 5. Using Axios

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Send message
export const sendMessage = async (userId: string, message: string) => {
  const response = await api.post('/orchestrator/message', {
    user_id: userId,
    message: message,
  });
  return response.data;
};

// Get history
export const getHistory = async (userId: string, limit: number = 20) => {
  const response = await api.get(`/orchestrator/history/${userId}`, {
    params: { limit },
  });
  return response.data;
};

// Usage in component
const handleSendMessage = async () => {
  try {
    const result = await sendMessage('user_123', 'Show me events');
    console.log('Intent:', result.intent);
    // Handle routing based on intent
  } catch (error) {
    console.error('Error:', error);
  }
};
```

---

## 🚨 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "user_id is required"
}
```

#### 404 Not Found
```json
{
  "error": "Endpoint not found",
  "message": "The requested endpoint does not exist",
  "docs": "/docs",
  "available_modules": [
    "/api/events",
    "/api/wellness",
    "/api/safety",
    "/api/orchestrator"
  ]
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Something went wrong. Please try again later or contact support."
}
```

### Error Handling Example

```typescript
try {
  const response = await OrchestratorAPI.sendMessage(userId, message);
  // Handle success
} catch (error) {
  if (error instanceof Error) {
    // Network error
    if (error.message.includes('Failed to fetch')) {
      alert('Network error. Please check your connection.');
    }
    // API error
    else {
      alert(`Error: ${error.message}`);
    }
  }
}
```

---

## 🎯 Best Practices

### 1. Environment Variables
Store API URLs in environment variables:

**`.env.local`**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL_PRODUCTION=https://your-production-url.com
```

### 2. User ID Management
```typescript
// Get or generate user ID
function getUserId(): string {
  let userId = localStorage.getItem('user_id');
  
  if (!userId) {
    // Generate UUID or use your auth system's user ID
    userId = crypto.randomUUID();
    localStorage.setItem('user_id', userId);
  }
  
  return userId;
}
```

### 3. Loading States
Always show loading indicators:
```typescript
{loading && <LoadingSpinner />}
{!loading && <ChatMessages messages={messages} />}
```

### 4. Debouncing
For real-time suggestions, debounce API calls:
```typescript
import { debounce } from 'lodash';

const debouncedSendMessage = debounce(async (message) => {
  await sendMessage(userId, message);
}, 500);
```

### 5. Intent-Based Routing
Route users based on detected intent:
```typescript
const handleIntent = (intent: string, router: NextRouter) => {
  switch (intent) {
    case 'find_events':
      router.push('/events');
      break;
    case 'emergency':
      router.push('/emergency');
      // Or trigger emergency modal
      break;
    case 'general':
      // Stay in chat
      break;
  }
};
```

### 6. Caching Conversations
Cache conversation history locally:
```typescript
// Save to localStorage
localStorage.setItem('chat_history', JSON.stringify(chatHistory));

// Load from localStorage
const savedHistory = localStorage.getItem('chat_history');
if (savedHistory) {
  setChatHistory(JSON.parse(savedHistory));
}
```

### 7. Retry Logic
Implement retry for failed requests:
```typescript
async function fetchWithRetry(fn: () => Promise<any>, retries = 3) {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      return fetchWithRetry(fn, retries - 1);
    }
    throw error;
  }
}
```

---

## 🔄 Complete Integration Flow

```
User types message
       ↓
Frontend sends to /api/orchestrator/message
       ↓
Orchestrator detects intent
       ↓
Returns intent + suggestion message
       ↓
Frontend routes based on intent:
  - find_events → Call /api/events/list
  - emergency → Show emergency modal or call /api/safety/sos
  - general → Display response in chat
```

---

## 📝 Quick Reference

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/orchestrator/` | GET | Get module info | No |
| `/api/orchestrator/message` | POST | Process user message | No* |
| `/api/orchestrator/history/{user_id}` | GET | Get conversation history | No* |

*Authentication will be required in production

---

## 🔗 Related Endpoints

After getting intent from orchestrator, you may want to call:

- **Events Agent:** `/api/events/list` (for `find_events` intent)
- **Safety Agent:** `/api/safety/sos` (for `emergency` intent)
- **Wellness Agent:** `/api/wellness/reminders` (for wellness-related intents)

See respective documentation:
- [Events API Documentation](./FRONTEND_INTEGRATION.md)
- Safety API Documentation (coming soon)
- Wellness API Documentation (coming soon)

---

## 📞 Support

**Backend URL:** http://localhost:8000  
**API Documentation:** http://localhost:8000/docs  
**Alternative Docs:** http://localhost:8000/redoc  

**Need Help?**
- Check the interactive API docs at `/docs`
- Review the test script: `test_orchestrator.py`
- Contact the backend team

---

## 🚀 Getting Started Checklist

- [ ] Set up environment variables (`NEXT_PUBLIC_API_URL`)
- [ ] Create API client (`lib/api/orchestrator.ts`)
- [ ] Create React hook (`hooks/useOrchestrator.ts`)
- [ ] Implement chat component
- [ ] Add error handling
- [ ] Test with different message types
- [ ] Implement intent-based routing
- [ ] Add loading states
- [ ] Cache conversation history locally
- [ ] Test with backend running on `http://localhost:8000`

---

**Last Updated:** December 10, 2025  
**API Version:** 2.0.0  
**Backend Status:** Development

