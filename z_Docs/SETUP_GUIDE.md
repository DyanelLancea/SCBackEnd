# SC Backend - Quick Setup Guide 🚀

Follow these steps to get your backend running in minutes!

## Step 1: Set Up Supabase Database

1. **Create a Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Sign up for free (no credit card required)

2. **Create a New Project**
   - Click "New Project"
   - Choose a name (e.g., "sc-backend")
   - Set a strong database password (save it!)
   - Select a region close to you
   - Wait 2-3 minutes for setup

3. **Run the Database Schema**
   - In your Supabase dashboard, go to "SQL Editor"
   - Click "New Query"
   - Open `supabase_schema.sql` from this project
   - Copy all the SQL code
   - Paste it into the Supabase SQL editor
   - Click "Run" or press Ctrl+Enter
   - You should see: "Database schema created successfully! 🎉"

4. **Get Your API Credentials**
   - Go to "Settings" → "API" in your Supabase dashboard
   - Copy your **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - Copy your **anon/public key** (long string starting with `eyJ...`)
   - Keep these safe! You'll need them in the next step

## Step 2: Set Up Backend

1. **Install Python**
   - Make sure you have Python 3.8+ installed
   - Check: `python --version` or `python3 --version`

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy `env_template.txt` to `.env`
   - Open `.env` in a text editor
   - Replace the values:
     ```
     SUPABASE_URL=https://your-project-id.supabase.co
     SUPABASE_KEY=your-supabase-anon-key
     ```
   - Save the file

## Step 3: Start the Server

### Option A: Use Start Script (Recommended)
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

### Option B: Manual Start
```bash
python -m app.main
```

## Step 4: Test Your API

1. **Open Your Browser**
   - Go to: http://localhost:8000
   - You should see a welcome message

2. **Try the Interactive Docs**
   - Go to: http://localhost:8000/docs
   - This is your interactive API documentation
   - Click "Try it out" on any endpoint to test it

3. **Test Event Creation**
   - In the docs, find `POST /api/events/create`
   - Click "Try it out"
   - Fill in the example:
     ```json
     {
       "title": "Test Event",
       "description": "My first event",
       "date": "2025-12-20",
       "time": "15:00",
       "location": "Online"
     }
     ```
   - Click "Execute"
   - You should get a success response!

4. **View Your Events**
   - Find `GET /api/events/list`
   - Click "Try it out" → "Execute"
   - You should see your test event (plus sample events)

## Step 5: Connect Your Frontend

Your backend is now ready for frontend integration!

### Connection Details
- **API Base URL**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### Example Frontend Code (JavaScript/React)

```javascript
// Get all events
async function getEvents() {
  const response = await fetch('http://localhost:8000/api/events/list');
  const data = await response.json();
  console.log(data.events);
  return data.events;
}

// Create an event
async function createEvent(eventData) {
  const response = await fetch('http://localhost:8000/api/events/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(eventData)
  });
  const data = await response.json();
  return data;
}

// Register for an event
async function registerForEvent(eventId, userId) {
  const response = await fetch('http://localhost:8000/api/events/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_id: eventId,
      user_id: userId
    })
  });
  const data = await response.json();
  return data;
}
```

## 📋 Available Endpoints

### Events
- `GET /api/events/list` - List all events
- `POST /api/events/create` - Create new event
- `GET /api/events/{id}` - Get event details
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event
- `POST /api/events/register` - Register for event
- `GET /api/events/{id}/participants` - Get participants

### Wellness (Placeholder)
- `GET /api/wellness/` - Module info
- `GET /api/wellness/reminders/{user_id}` - Get reminders

### Safety (Placeholder)
- `GET /api/safety/` - Module info
- `POST /api/safety/emergency` - Trigger emergency

### Orchestrator (Placeholder)
- `GET /api/orchestrator/` - Module info
- `POST /api/orchestrator/message` - Send message

## 🐛 Troubleshooting

### Error: "Supabase credentials not found"
- Make sure you created the `.env` file
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
- No spaces around the `=` sign

### Error: "Port already in use"
- Another application is using port 8000
- Either stop that application or change the port:
  ```bash
  uvicorn app.main:app --port 8001
  ```

### Error: "Module not found"
- Make sure your virtual environment is activated
- Re-run: `pip install -r requirements.txt`

### Error: "Table 'events' does not exist"
- You forgot to run the SQL schema in Supabase
- Go back to Step 1.3 and run `supabase_schema.sql`

### Can't connect from frontend
- Check that CORS is enabled in `app/main.py`
- Make sure your frontend URL is in the `allow_origins` list
- Try adding `"*"` temporarily for testing (remove in production!)

## ✅ Success Checklist

- [ ] Supabase project created
- [ ] SQL schema executed successfully
- [ ] `.env` file configured with correct credentials
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] Can create events via API docs
- [ ] Can view events via API docs

## 🎉 Next Steps

1. **Test all endpoints** using the interactive docs
2. **Connect your frontend** using the example code above
3. **Customize the events** to fit your needs
4. **Add authentication** (optional, using Supabase Auth)
5. **Deploy to production** (Railway, Render, or other platforms)

## 📞 Need Help?

- Check the main `README.md` for detailed documentation
- Review the API docs at http://localhost:8000/docs
- Check Supabase dashboard for database issues
- Review logs in your terminal for error messages

---

**You're all set! Happy coding! 🚀**

