# Code Execution Analysis: Intent-Based Actions

This document analyzes whether the current code implementation matches the documented behavior in `ENDPOINT_DATA_INPUT_GUIDE.md` and identifies any discrepancies.

## Executive Summary

✅ **Overall**: The code implementation **DOES** follow user intent correctly for most cases.

⚠️ **Issue Found**: The fallback keyword detection doesn't extract event information, which could cause problems when GROQ is unavailable.

❌ **Critical Gap**: There's no code that defaults to "latest event" - if event matching fails, the system correctly asks the user to specify which event.

---

## Detailed Analysis by Activity

### 1. Book a Specific Event ✅

#### Documented Behavior:
- Uses GROQ to detect `book_event` intent
- Extracts `event_name` and/or `event_id` from message
- Uses `find_event_by_name_or_id()` to match event
- Only books if specific event is found

#### Actual Implementation (lines 537-635):
```python
elif intent in ["book_event", "register_event"]:
    event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
    potential_event_id = intent_data.get("event_id")
    
    # Get available events to search through
    events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
    # ... filter events ...
    
    # Use improved matching function to find the specific event
    matched_event = find_event_by_name_or_id(
        events=events,
        event_name=event_name if event_name else None,
        event_id=potential_event_id if potential_event_id else None
    )
    
    # If no match and user didn't specify an event name, show available events
    if not matched_event and not event_name:
        # Lists events for user to choose - DOES NOT book latest
        message = f"I found {len(events)} events. Please specify which one..."
    elif not matched_event:
        # Event name mentioned but not found - provides suggestions
        message = f"I couldn't find an event matching '{event_name}'..."
    else:
        # Found the event - register user
        register_resp = await client.post(...)
```

#### ✅ Verification:
- **Correctly uses intent detection**: ✅ Yes
- **Extracts event_name and event_id**: ✅ Yes (from `intent_data`)
- **Uses find_event_by_name_or_id()**: ✅ Yes
- **Does NOT default to latest event**: ✅ Correct - shows list instead
- **Books only when event is matched**: ✅ Yes

#### ⚠️ Potential Issue:
If GROQ fails and falls back to keyword detection, `event_name` and `event_id` will be `None` because the fallback doesn't extract them (see lines 463-474).

---

### 2. Unregister from Events ✅

#### Documented Behavior:
- Detects `cancel_event` or `unregister_event` intent
- Extracts event information
- Uses `find_event_by_name_or_id()` to find specific event
- Unregisters only if event is found

#### Actual Implementation (lines 752-823):
```python
elif intent in ["cancel_event", "unregister_event"]:
    event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
    potential_event_id = intent_data.get("event_id")
    
    # Get events to search
    events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
    # ... filter events ...
    
    # Use improved matching function to find the specific event
    matched_event = find_event_by_name_or_id(
        events=events,
        event_name=event_name if event_name else None,
        event_id=potential_event_id if potential_event_id else None
    )
    
    if matched_event:
        # Unregister user from the event
        unregister_resp = await client.delete(...)
    else:
        # Event not found - provide helpful suggestions
        if event_name and events:
            # Shows suggestions
        elif not event_name:
            # Asks user to specify which event
```

#### ✅ Verification:
- **Correctly uses intent detection**: ✅ Yes
- **Extracts event information**: ✅ Yes
- **Uses find_event_by_name_or_id()**: ✅ Yes
- **Does NOT default to latest event**: ✅ Correct - asks user to specify
- **Unregisters only when event is matched**: ✅ Yes

---

### 3. Check Details of an Event ✅

#### Documented Behavior:
- Detects `get_event` intent
- Extracts event information
- Uses `find_event_by_name_or_id()` to find specific event
- Returns event details only if event is found

#### Actual Implementation (lines 657-750):
```python
elif intent == "get_event":
    event_name = intent_data.get("event_name", "").strip() if intent_data.get("event_name") else ""
    potential_event_id = intent_data.get("event_id")
    
    # Get events to search
    events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
    # ... filter events ...
    
    # Use improved matching function to find the specific event
    matched_event = find_event_by_name_or_id(
        events=events,
        event_name=event_name if event_name else None,
        event_id=potential_event_id if potential_event_id else None
    )
    
    if matched_event:
        # Get full event details
        event_resp = await client.get(f"{base_url}/api/events/{event_id_str}")
        # ... format and return details ...
    else:
        # Event not found - provide helpful suggestions
        if event_name and events:
            # Shows suggestions
        elif not event_name:
            # Asks user to specify which event
```

#### ✅ Verification:
- **Correctly uses intent detection**: ✅ Yes
- **Extracts event information**: ✅ Yes
- **Uses find_event_by_name_or_id()**: ✅ Yes
- **Does NOT default to latest event**: ✅ Correct - asks user to specify
- **Returns details only when event is matched**: ✅ Yes

---

### 4. Answer General Questions ✅

#### Documented Behavior:
- Detects `general` intent
- Uses GPT to answer questions
- Fetches available events for context

#### Actual Implementation (lines 825-910):
```python
else:
    # General intent - use GPT to answer questions intelligently
    try:
        gpt_client = get_openai_client()
        
        # Get available events for context
        available_events = []
        events_resp = await client.get(f"{base_url}/api/events/list?limit=5")
        # ... build context ...
        
        # Create prompt for general question answering
        general_prompt = f"""You are a helpful assistant...
        User question: "{request.message}"
        {events_context}
        ..."""
        
        gpt_response = gpt_client.chat.completions.create(...)
        message = gpt_response.choices[0].message.content.strip()
```

#### ✅ Verification:
- **Correctly uses intent detection**: ✅ Yes
- **Uses GPT for answers**: ✅ Yes
- **Fetches events for context**: ✅ Yes
- **Falls back gracefully**: ✅ Yes (default message if GPT unavailable)

---

## Critical Issue: Fallback Keyword Detection

### Problem (lines 463-474):

When GROQ is unavailable or fails, the code falls back to simple keyword detection:

```python
# Fallback to simple keyword detection
message_lower = user_message.lower()
if detect_emergency_intent(user_message):
    return {"intent": "emergency", "confidence": 0.8}
elif any(word in message_lower for word in ["book", "register", "join", "sign up", "enroll"]):
    return {"intent": "book_event", "confidence": 0.7}  # ❌ NO event_name or event_id!
elif any(word in message_lower for word in ["list", "show", "find", "what events", "available"]):
    return {"intent": "list_events", "confidence": 0.7}
elif any(word in message_lower for word in ["cancel", "unregister", "remove", "leave"]):
    return {"intent": "cancel_event", "confidence": 0.7}  # ❌ NO event_name or event_id!
else:
    return {"intent": "general", "confidence": 0.5}
```

### Impact:

1. **When GROQ fails**: The fallback returns intent but **NO event_name or event_id**
2. **Result**: `find_event_by_name_or_id()` receives `None` for both parameters
3. **Behavior**: System correctly asks user to specify which event (does NOT book latest)
4. **User Experience**: User must send another message with event name

### This is NOT the "books latest event" bug!

The code does NOT default to booking the latest event. If event matching fails, it:
- Shows available events list (for booking)
- Asks user to specify which event (for cancel/get details)
- Provides suggestions (if event name partially matches)

---

## Intent Detection Analysis

### GROQ Intent Detection (lines 299-452):

✅ **Strengths**:
- Fetches available events for context
- Provides detailed prompt with event information
- Extracts `event_name` and `event_id` from message
- Uses JSON response format for reliability
- Has fallback to 8B model if 70B fails

✅ **Event Matching Logic** (lines 443-450):
```python
# If event_id not found but event_name is, try to match with available events
if result.get("intent") in ["book_event", "register_event", "get_event", "cancel_event", "unregister_event"]:
    if not result.get("event_id") and result.get("event_name") and available_events:
        event_name_lower = result.get("event_name", "").lower()
        for event in available_events:
            if event_name_lower in event.get("title", "").lower():
                result["event_id"] = event.get("id")
                break
```

This tries to match event_name to available events and populate event_id automatically.

### Potential Issues:

1. **GROQ might not extract event_name correctly** if:
   - User message is ambiguous
   - Event name is misspelled
   - Event name is very generic (e.g., "class", "session")

2. **Event matching might fail** if:
   - Event name doesn't match any events (60% threshold)
   - Event name is too generic
   - Multiple events match (returns first match, not necessarily best)

---

## Event Matching Function Analysis

### `find_event_by_name_or_id()` (lines 207-296):

✅ **Strengths**:
- Validates UUIDs strictly (rejects invalid IDs like "1")
- Uses multiple matching strategies (exact, word match, substring, overlap)
- Requires 60% match threshold
- Returns `None` if no match (does NOT default to first/latest event)

✅ **Matching Strategies**:
1. **Exact normalized match**: Score = 1.0
2. **All search words found**: Score = matched_words / total_words
3. **Substring match**: Score = length ratio
4. **Word overlap**: Score = matched_words / max(words)

⚠️ **Potential Issue**:
If multiple events match with the same score, it returns the **first one** in the list (which might be the latest if events are sorted by date). However, this is only if they have the same score, which is unlikely.

---

## Root Cause Analysis: "Books Latest Event" Issue

### Hypothesis 1: GROQ Not Extracting Event Name
**Scenario**: User says "book event" without specifying which one
- GROQ might return `intent: "book_event"` but `event_name: null`
- Code correctly shows list of events (does NOT book latest)
- **This is NOT the bug**

### Hypothesis 2: Event Matching Returns First Match
**Scenario**: User says "book workout" and there are multiple workout events
- `find_event_by_name_or_id()` might match the first event in the list
- If events are sorted by date (ascending), first = oldest
- If events are sorted by date (descending), first = latest
- **This could be the bug!**

### Hypothesis 3: Events List Ordering
**Check**: How are events ordered when fetched?
```python
events_resp = await client.get(f"{base_url}/api/events/list?limit=50")
```

Looking at `app/events/routes.py` line 121:
```python
query = query.order('date', desc=False).order('time', desc=False)
```

Events are ordered by date **ascending** (oldest first), so the first event would be the **oldest**, not latest.

**But wait**: If `find_event_by_name_or_id()` iterates through all events and finds multiple matches, it returns the one with the highest score. If scores are equal, it returns the last one checked (which would be the latest in an ascending list).

Actually, looking at the code more carefully:
```python
for event in events:  # Iterates in order
    # ... calculate score ...
    if score > best_score:  # Only updates if score is HIGHER
        best_score = score
        best_match = event
```

If multiple events have the same score, it keeps the **first one** that matched (not the last). So if events are sorted oldest-first, it would match the **oldest** event, not the latest.

---

## Conclusion

### ✅ Code Execution Matches Documentation:
1. **Book Event**: ✅ Correctly uses intent, extracts event info, matches event, does NOT default to latest
2. **Unregister**: ✅ Correctly uses intent, extracts event info, matches event, asks user if not found
3. **Get Event Details**: ✅ Correctly uses intent, extracts event info, matches event, asks user if not found
4. **General Questions**: ✅ Correctly uses intent, uses GPT for answers

### ⚠️ Issues Found:

1. **Fallback Keyword Detection**: Doesn't extract `event_name` or `event_id`, causing user to send second message
2. **Event Matching**: If multiple events match with same score, returns first match (might be oldest, not latest)
3. **GROQ Extraction**: Might not extract event name correctly from ambiguous messages

### ❌ "Books Latest Event" Bug:

**The code does NOT default to booking the latest event.** If the bug exists, it's likely due to:
- GROQ extracting wrong event name
- Event matching logic matching wrong event
- Events being sorted in unexpected order

### Recommendations:

1. **Improve Fallback Detection**: Extract event name from message using regex/simple parsing
2. **Add Logging**: Log which event was matched and why
3. **Improve Event Matching**: When multiple events match, ask user to disambiguate
4. **Add Event Ordering Option**: Allow specifying "latest" or "upcoming" in matching

---

## Verification Checklist

- [x] Intent detection uses GROQ (with fallback)
- [x] Event extraction from intent_data
- [x] Event matching uses find_event_by_name_or_id()
- [x] No default to latest event in code
- [x] Proper error handling when event not found
- [x] General questions use GPT
- [ ] Fallback keyword detection extracts event info (❌ Missing)
- [ ] Logging for debugging (❌ Not visible in code)
- [ ] Disambiguation for multiple matches (❌ Missing)

