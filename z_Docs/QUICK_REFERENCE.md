# ⚡ SC Backend - Quick Reference

**One-page reference for common tasks**

---

## 🔗 Important URLs

| Environment | URL |
|------------|-----|
| **Local API** | http://localhost:8000 |
| **Local Docs** | http://localhost:8000/docs |
| **Production API** | https://[your-service].onrender.com |
| **Production Docs** | https://[your-service].onrender.com/docs |
| **Health Check** | http://localhost:8000/health |

---

## 🚀 Quick Start Commands

```bash
# Activate virtual environment
venv\Scripts\activate              # Windows
source venv/bin/activate           # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main

# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Deploy to Render (auto-deploys on push)
git add .
git commit -m "Update"
git push origin main
```

---

## 📡 API Endpoints

### Events
```
GET    /api/events/list                        # Get all events
GET    /api/events/{id}                        # Get one event
POST   /api/events/create                      # Create event
PUT    /api/events/{id}                        # Update event
DELETE /api/events/{id}                        # Delete event
POST   /api/events/register                    # Register for event
DELETE /api/events/register/{event_id}/{user_id}  # Unregister
GET    /api/events/{id}/participants           # Get participants
```

### Wellness
```
GET    /api/wellness/                          # Module info
GET    /api/wellness/reminders/{user_id}      # Get reminders
POST   /api/wellness/reminders                # Create reminder
```

### Safety
```
GET    /api/safety/                            # Module info
POST   /api/safety/emergency                   # Trigger alert
POST   /api/safety/location                    # Update location
```

### Orchestrator
```
GET    /api/orchestrator/                      # Module info
POST   /api/orchestrator/message               # Send message
```

---

## 📝 Common cURL Commands

```bash
# Get events
curl http://localhost:8000/api/events/list

# Create event
curl -X POST http://localhost:8000/api/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "description": "Event description",
    "date": "2025-12-25",
    "time": "15:00",
    "location": "Community Hall"
  }'

# Get upcoming events
curl "http://localhost:8000/api/events/list?date_filter=upcoming"

# Register for event
curl -X POST http://localhost:8000/api/events/register \
  -H "Content-Type: application/json" \
  -d '{"event_id": "event-uuid", "user_id": "user-uuid"}'

# Health check
curl http://localhost:8000/health
```

---

## 🔧 Environment Variables

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

**Where to set:**
- **Local**: `.env` file in project root
- **Render**: Dashboard → Environment tab

---

## 📂 Project Structure

```
SCBackEnd/
├── app/
│   ├── main.py              # FastAPI app
│   ├── events/routes.py     # Events API
│   ├── wellness/routes.py   # Wellness API
│   ├── safety/routes.py     # Safety API
│   ├── orchestrator/routes.py # Orchestrator API
│   └── shared/supabase.py   # Database connection
├── z_Docs/                  # Documentation
│   ├── API_REFERENCE.md
│   ├── FRONTEND_INTEGRATION.md
│   ├── RENDER_DEPLOYMENT.md
│   ├── SETUP_GUIDE.md
│   └── PROJECT_SUMMARY.md
├── requirements.txt         # Dependencies
├── render.yaml              # Render config
├── build.sh                 # Build script
└── supabase_schema.sql      # Database schema
```

---

## 🎨 Frontend Integration

### JavaScript/React
```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Get events
const response = await fetch(`${API_URL}/api/events/list`);
const data = await response.json();

// Create event
await fetch(`${API_URL}/api/events/create`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: "Event Title",
    date: "2025-12-25",
    time: "15:00",
    location: "Online"
  })
});
```

### Environment Variables (Frontend)
```bash
# Next.js (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000              # Local
NEXT_PUBLIC_API_URL=https://your-service.onrender.com  # Production

# Vite (.env)
VITE_API_URL=http://localhost:8000                     # Local

# Create React App (.env)
REACT_APP_API_URL=http://localhost:8000                # Local
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port in use** | Change port: `uvicorn app.main:app --port 8001` |
| **Module not found** | Activate venv, reinstall: `pip install -r requirements.txt` |
| **Supabase error** | Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY` |
| **CORS error** | Add frontend URL to `allow_origins` in `app/main.py` |
| **Build failed (Render)** | Check Logs tab, verify `requirements.txt` |
| **Deploy crashes (Render)** | Check environment variables are set |
| **Cold start (Render)** | Upgrade to Starter plan or use ping service |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Project overview & setup |
| **z_Docs/SETUP_GUIDE.md** | Detailed setup instructions |
| **z_Docs/API_REFERENCE.md** | Complete API documentation |
| **z_Docs/FRONTEND_INTEGRATION.md** | Frontend connection guide |
| **z_Docs/RENDER_DEPLOYMENT.md** | Production deployment guide |
| **z_Docs/PROJECT_SUMMARY.md** | Project architecture & overview |
| **DEPLOYMENT_CHECKLIST.md** | Step-by-step deployment checklist |
| **QUICK_REFERENCE.md** | This file |

---

## 🔑 Render Deployment (Quick)

```bash
# 1. Push to GitHub
git push origin main

# 2. On Render.com
#    - New → Web Service
#    - Connect repo
#    - Build: pip install -r requirements.txt
#    - Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
#    - Add environment variables

# 3. Test
curl https://your-service.onrender.com/health
```

---

## 📊 Request/Response Examples

### Create Event Request
```json
{
  "title": "Community Gathering",
  "description": "Monthly meetup",
  "date": "2025-12-20",
  "time": "15:00",
  "location": "Community Hall",
  "max_participants": 50
}
```

### Create Event Response
```json
{
  "success": true,
  "message": "Event created successfully!",
  "event": {
    "id": "uuid-here",
    "title": "Community Gathering",
    "date": "2025-12-20",
    "time": "15:00",
    ...
  }
}
```

### Get Events Response
```json
{
  "success": true,
  "events": [
    {
      "id": "uuid",
      "title": "Event Title",
      "date": "2025-12-25",
      "time": "10:00",
      ...
    }
  ],
  "count": 1
}
```

---

## 🎯 Common Tasks

### Add New Endpoint
1. Edit `app/[module]/routes.py`
2. Add function with `@router.get()` or `@router.post()`
3. Test locally
4. Push to GitHub (auto-deploys on Render)

### Update CORS Origins
1. Edit `app/main.py` → `allow_origins` list
2. Add your frontend URL
3. Commit and push

### View Logs (Render)
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab

### Update Dependencies
1. Add to `requirements.txt`
2. Test locally: `pip install -r requirements.txt`
3. Push to GitHub

---

## 🔐 Security Checklist

- [ ] `.env` in `.gitignore`
- [ ] No hardcoded credentials
- [ ] CORS restricted (no `"*"` in production)
- [ ] HTTPS only in production
- [ ] Environment variables in Render dashboard
- [ ] Supabase RLS policies enabled

---

## ⚡ Performance Tips

### Free Tier (Render)
- Cold starts after 15 min inactivity
- Use cron-job.org to ping `/health` every 10 min
- Or upgrade to Starter ($7/mo)

### Database
- Use indexes on frequently queried fields
- Enable connection pooling (Supabase)
- Monitor query performance

---

## 📞 Support

| Issue Type | Resource |
|------------|----------|
| **Setup Help** | See `z_Docs/SETUP_GUIDE.md` |
| **API Questions** | See `z_Docs/API_REFERENCE.md` |
| **Frontend Help** | See `z_Docs/FRONTEND_INTEGRATION.md` |
| **Deployment Issues** | See `z_Docs/RENDER_DEPLOYMENT.md` |
| **Interactive Testing** | Visit `/docs` endpoint |
| **Render Support** | support@render.com |
| **Supabase Support** | support.supabase.com |

---

**Last Updated:** December 10, 2025  
**Version:** 2.0.0  
**Backend URL:** http://localhost:8000 (local) | https://[your-service].onrender.com (prod)

---

**🚀 Happy Coding! 🚀**

