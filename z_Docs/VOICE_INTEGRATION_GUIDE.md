# Voice Integration Guide - Frontend Implementation

## 🎤 Architecture Overview

**Flow:** Voice Input → Speech-to-Text (Frontend) → Text → Orchestrator API

This approach requires **NO backend changes** - we use your existing `/api/orchestrator/message` endpoint.

---

## 🚀 Implementation Options

### Option 1: Web Speech API (Browser Native) - FREE

**Pros:**
- ✅ Free
- ✅ No API keys needed
- ✅ Works offline
- ✅ Fast (client-side)
- ✅ Good accuracy for English

**Cons:**
- ❌ Browser support varies (works best in Chrome)
- ❌ Requires HTTPS in production
- ❌ Less accurate than cloud services

---

### Option 2: Deepgram API - BEST QUALITY

**Pros:**
- ✅ Excellent accuracy
- ✅ Real-time streaming
- ✅ Multiple languages
- ✅ Low latency
- ✅ First $200 free

**Cons:**
- ❌ Requires API key
- ❌ Costs money after free tier

---

### Option 3: OpenAI Whisper API - GOOD BALANCE

**Pros:**
- ✅ Very accurate
- ✅ 50+ languages
- ✅ Handles accents well
- ✅ Affordable ($0.006/minute)

**Cons:**
- ❌ Requires API key
- ❌ Not real-time (file-based)

---

## 💻 Implementation Code

### 1. Web Speech API Implementation (Recommended for MVP)

**`hooks/useVoiceInput.ts`**
```typescript
import { useState, useEffect, useRef } from 'react';

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

// Extend Window interface for browser speech recognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function useVoiceInput() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);
  
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check if browser supports speech recognition
    if (typeof window !== 'undefined') {
      const SpeechRecognition = 
        window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        setIsSupported(true);
        recognitionRef.current = new SpeechRecognition();
        
        // Configure recognition
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';
        
        // Handle results
        recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
          const transcript = event.results[0][0].transcript;
          setTranscript(transcript);
          setIsListening(false);
        };
        
        // Handle errors
        recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
          setError(event.error);
          setIsListening(false);
        };
        
        // Handle end
        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setError(null);
      setTranscript('');
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        setError('Failed to start listening');
        setIsListening(false);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const resetTranscript = () => {
    setTranscript('');
    setError(null);
  };

  return {
    isListening,
    transcript,
    error,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  };
}
```

---

### 2. Voice Chat Component

**`components/VoiceChatButton.tsx`**
```typescript
'use client';

import { useState, useEffect } from 'react';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import { useOrchestrator } from '@/hooks/useOrchestrator';

interface VoiceChatButtonProps {
  userId: string;
  onMessage?: (message: string) => void;
  onResponse?: (response: any) => void;
}

export default function VoiceChatButton({ 
  userId, 
  onMessage, 
  onResponse 
}: VoiceChatButtonProps) {
  const {
    isListening,
    transcript,
    error: voiceError,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  } = useVoiceInput();

  const { sendMessage, loading, error: apiError } = useOrchestrator(userId);

  // Send to orchestrator when transcript is ready
  useEffect(() => {
    if (transcript && !isListening) {
      handleSendMessage(transcript);
    }
  }, [transcript, isListening]);

  const handleSendMessage = async (message: string) => {
    try {
      // Callback for parent component
      if (onMessage) {
        onMessage(message);
      }

      // Send to orchestrator API
      const response = await sendMessage(message);
      
      // Callback for parent component
      if (onResponse) {
        onResponse(response);
      }

      // Reset for next use
      resetTranscript();
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <div className="text-sm text-gray-500">
        Voice input not supported in this browser
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Voice Button */}
      <button
        onClick={handleClick}
        disabled={loading}
        className={`
          relative p-4 rounded-full transition-all duration-200
          ${isListening 
            ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
            : 'bg-blue-500 hover:bg-blue-600'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
          text-white shadow-lg
        `}
        aria-label={isListening ? 'Stop listening' : 'Start voice input'}
      >
        {/* Microphone Icon */}
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>

        {/* Listening indicator */}
        {isListening && (
          <span className="absolute inset-0 rounded-full border-4 border-white animate-ping opacity-75" />
        )}
      </button>

      {/* Status Text */}
      <div className="text-center min-h-[24px]">
        {isListening && (
          <p className="text-sm text-gray-600 animate-pulse">
            🎤 Listening...
          </p>
        )}
        {loading && (
          <p className="text-sm text-gray-600">
            ⏳ Processing...
          </p>
        )}
        {transcript && !isListening && !loading && (
          <p className="text-sm text-green-600">
            ✓ Sent: "{transcript.substring(0, 30)}..."
          </p>
        )}
      </div>

      {/* Error Messages */}
      {(voiceError || apiError) && (
        <div className="text-sm text-red-500">
          {voiceError || apiError}
        </div>
      )}
    </div>
  );
}
```

---

### 3. Complete Voice Chat Interface

**`components/VoiceChat.tsx`**
```typescript
'use client';

import { useState } from 'react';
import VoiceChatButton from './VoiceChatButton';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  intent?: string;
  timestamp: Date;
}

interface VoiceChatProps {
  userId: string;
}

export default function VoiceChat({ userId }: VoiceChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleUserMessage = (message: string) => {
    setMessages(prev => [...prev, {
      sender: 'user',
      text: message,
      timestamp: new Date(),
    }]);
  };

  const handleBotResponse = (response: any) => {
    setMessages(prev => [...prev, {
      sender: 'bot',
      text: response.message,
      intent: response.intent,
      timestamp: new Date(),
    }]);
  };

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto">
      {/* Header */}
      <div className="bg-white border-b p-4">
        <h2 className="text-xl font-bold">Voice Assistant</h2>
        <p className="text-sm text-gray-600">
          Click the microphone and speak
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>👋 Start a conversation!</p>
            <p className="text-sm mt-2">
              Try saying: "What events are happening?" or "Help!"
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs px-4 py-2 rounded-lg ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-800 border'
                }`}
              >
                <p>{msg.text}</p>
                {msg.intent && (
                  <p className="text-xs mt-1 opacity-75">
                    Intent: {msg.intent}
                  </p>
                )}
                <p className="text-xs mt-1 opacity-50">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Voice Button */}
      <div className="bg-white border-t p-6 flex justify-center">
        <VoiceChatButton
          userId={userId}
          onMessage={handleUserMessage}
          onResponse={handleBotResponse}
        />
      </div>
    </div>
  );
}
```

---

### 4. Alternative: Deepgram Implementation (Premium)

**`hooks/useDeepgramVoice.ts`**
```typescript
import { useState, useRef } from 'react';
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk';

export function useDeepgramVoice(apiKey: string) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const deepgramRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const startListening = async () => {
    try {
      // Initialize Deepgram
      const deepgram = createClient(apiKey);
      deepgramRef.current = deepgram.listen.live({
        model: 'nova-2',
        language: 'en-US',
        smart_format: true,
      });

      // Handle transcription results
      deepgramRef.current.on(
        LiveTranscriptionEvents.Transcript,
        (data: any) => {
          const transcript = data.channel.alternatives[0].transcript;
          if (transcript) {
            setTranscript(transcript);
          }
        }
      );

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true 
      });

      // Start recording
      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && deepgramRef.current) {
          deepgramRef.current.send(event.data);
        }
      };

      mediaRecorderRef.current.start(250); // Send data every 250ms
      setIsListening(true);

    } catch (err) {
      setError('Failed to start listening');
      console.error(err);
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    if (deepgramRef.current) {
      deepgramRef.current.finish();
    }
    setIsListening(false);
  };

  return {
    isListening,
    transcript,
    error,
    startListening,
    stopListening,
  };
}
```

---

## 🔧 Setup Instructions

### Using Web Speech API (Free)

1. **Install dependencies:**
```bash
npm install
# No additional dependencies needed!
```

2. **Add the hooks and components** (from code above)

3. **Use in your page:**
```typescript
import VoiceChat from '@/components/VoiceChat';

export default function ChatPage() {
  return <VoiceChat userId="user_123" />;
}
```

4. **Done!** No backend changes needed.

---

### Using Deepgram (Premium)

1. **Sign up:** https://deepgram.com
2. **Get API key**
3. **Install SDK:**
```bash
npm install @deepgram/sdk
```

4. **Add to `.env.local`:**
```bash
NEXT_PUBLIC_DEEPGRAM_API_KEY=your_api_key_here
```

5. **Use the Deepgram hook** (from code above)

---

## 🎯 Integration with Orchestrator

The voice components automatically use your existing orchestrator endpoint:

```typescript
// Inside the component, after transcription:
const response = await fetch('http://localhost:8000/api/orchestrator/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    message: transcribedText, // From voice input
  }),
});
```

**No backend changes required!** ✅

---

## 🚀 Quick Start

### Step 1: Add Environment Variable (Optional)
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 2: Copy Files
- `hooks/useVoiceInput.ts`
- `hooks/useOrchestrator.ts` (from orchestrator guide)
- `components/VoiceChatButton.tsx`
- `components/VoiceChat.tsx`

### Step 3: Use in Your App
```typescript
import VoiceChat from '@/components/VoiceChat';

export default function Home() {
  return (
    <main className="h-screen">
      <VoiceChat userId="user_123" />
    </main>
  );
}
```

---

## 🔍 Testing

### Browser Compatibility
```typescript
// Test if browser supports speech recognition
if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
  console.log('✅ Voice input supported!');
} else {
  console.log('❌ Voice input not supported');
}
```

### Test Flow
1. Click microphone button
2. Say: "What events are happening today?"
3. Speech → Text transcription
4. Text sent to `/api/orchestrator/message`
5. Response received with intent
6. Display response

---

## 📊 Comparison Table

| Feature | Web Speech API | Deepgram | OpenAI Whisper |
|---------|---------------|----------|----------------|
| **Cost** | Free | $0.0043/min | $0.006/min |
| **Accuracy** | Good | Excellent | Excellent |
| **Real-time** | Yes | Yes | No |
| **Offline** | Yes | No | No |
| **Languages** | Limited | 30+ | 50+ |
| **Setup** | Easy | Medium | Medium |
| **Backend Required** | No | No | Optional |

---

## ⚠️ Important Notes

### HTTPS Required in Production
Speech recognition requires HTTPS in production:
```bash
# Development (localhost works with HTTP)
http://localhost:3000 ✅

# Production (needs HTTPS)
https://yourapp.com ✅
http://yourapp.com ❌
```

### Browser Support
- ✅ Chrome/Edge: Full support
- ✅ Safari: Partial support
- ⚠️ Firefox: Limited support
- ❌ IE: No support

### Microphone Permissions
Users must grant microphone access:
```typescript
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(() => console.log('✅ Microphone access granted'))
  .catch(() => console.log('❌ Microphone access denied'));
```

---

## 🎨 UI Enhancements

### Add Visual Feedback
```typescript
// Animated waveform while listening
{isListening && <Waveform />}

// Transcript preview
{transcript && <div className="text-sm">{transcript}</div>}

// Intent badge
{intent && <Badge color={getColorForIntent(intent)}>{intent}</Badge>}
```

---

## 📱 Mobile Considerations

### iOS Safari
- Requires user gesture to start recording
- Can't autoplay audio without user interaction

### Android Chrome
- Works well with Web Speech API
- May need fallback for older versions

---

## 🔐 Security Best Practices

1. **Never expose API keys in frontend**
```typescript
// ❌ BAD
const apiKey = 'your_deepgram_key';

// ✅ GOOD
const apiKey = process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY;
```

2. **Validate on backend**
Even though frontend does STT, validate message content on backend

3. **Rate limiting**
Implement rate limiting for voice requests

---

## 📈 Next Steps

1. ✅ Implement Web Speech API (Start here)
2. ✅ Test with orchestrator endpoint
3. ⏭️ Add visual feedback (waveforms)
4. ⏭️ Implement Deepgram for better accuracy (optional)
5. ⏭️ Add language selection
6. ⏭️ Add voice output (text-to-speech)

---

## 🆘 Troubleshooting

### "Speech recognition not working"
- Check HTTPS in production
- Verify browser support
- Check microphone permissions

### "No transcription appearing"
- Speak clearly and loud enough
- Check microphone is not muted
- Try different browser (Chrome recommended)

### "API calls failing"
- Verify backend is running
- Check CORS settings
- Verify orchestrator endpoint URL

---

**Remember:** This approach requires **ZERO backend changes**! Your existing `/api/orchestrator/message` endpoint handles everything. 🎉


