# SC Backend API

A comprehensive FastAPI backend for community engagement platform with events management, wellness features, and safety monitoring. Built with Supabase (PostgreSQL) for data persistence.

## 🚀 Features

### ✅ Core Features (Implemented)
- **Events Management**: Create, read, update, delete events
- **Event Registration**: Users can register/unregister for events
- **RESTful API**: Well-structured HTTP endpoints
- **Supabase Integration**: PostgreSQL database with Row Level Security
- **CORS Support**: Ready for frontend integration
- **API Documentation**: Auto-generated with FastAPI

### 🔜 Coming Soon
- Wellness & Social Intelligence
- Safety & Emergency Response
- AI-powered Orchestrator
- Voice integration

## 📋 Prerequisites

- Python 3.8 or higher
- Supabase account (free tier works)
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd SCBackEnd
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the template
cp env_template.txt .env

# Edit .env with your Supabase credentials
# SUPABASE_URL=https://your-project-id.supabase.co
# SUPABASE_KEY=your-supabase-anon-key
```

### 5. Set Up Supabase Database
1. Go to [Supabase](https://supabase.com) and create a new project
2. Go to SQL Editor in your Supabase dashboard
3. Copy the contents of `supabase_schema.sql`
4. Run the SQL script in the editor
5. Your database is now ready! 🎉

### 6. Run the Application
```bash
# Development mode (auto-reload)
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentation

### API Documentation
Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Root Endpoint**: http://localhost:8000/

### Complete Guides
- **[Setup Guide](z_Docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[API Reference](z_Docs/API_REFERENCE.md)** - Complete API documentation
- **[Frontend Integration](z_Docs/FRONTEND_INTEGRATION.md)** - Connect your frontend
- **[Render Deployment](z_Docs/RENDER_DEPLOYMENT.md)** - Deploy to production
- **[Project Summary](z_Docs/PROJECT_SUMMARY.md)** - Project overview

## 🔗 API Endpoints

### Events API
- `GET /api/events/list` - Get all events (with filters)
- `GET /api/events/{event_id}` - Get specific event
- `POST /api/events/create` - Create new event
- `PUT /api/events/{event_id}` - Update event
- `DELETE /api/events/{event_id}` - Delete event
- `POST /api/events/register` - Register for event
- `DELETE /api/events/register/{event_id}/{user_id}` - Unregister from event
- `GET /api/events/{event_id}/participants` - Get event participants

### Wellness API
- `GET /api/wellness/` - Module information
- `GET /api/wellness/reminders/{user_id}` - Get user reminders
- `POST /api/wellness/reminders` - Create reminder
- `GET /api/wellness/analytics/{user_id}` - Get user analytics

### Safety API
- `GET /api/safety/` - Module information
- `POST /api/safety/emergency` - Trigger emergency alert
- `POST /api/safety/location` - Update user location
- `GET /api/safety/location/{user_id}` - Get user location

### Orchestrator API
- `GET /api/orchestrator/` - Module information
- `POST /api/orchestrator/message` - Process text message
- `GET /api/orchestrator/history/{user_id}` - Get conversation history

## 📝 Example Usage

### Create an Event
```bash
curl -X POST "http://localhost:8000/api/events/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Community Gathering",
    "description": "Monthly community meetup",
    "date": "2025-12-20",
    "time": "15:00",
    "location": "Community Hall",
    "max_participants": 50
  }'
```

### Get All Events
```bash
curl "http://localhost:8000/api/events/list"
```

### Get Upcoming Events
```bash
curl "http://localhost:8000/api/events/list?date_filter=upcoming"
```

### Register for Event
```bash
curl -X POST "http://localhost:8000/api/events/register" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "your-event-uuid",
    "user_id": "your-user-uuid"
  }'
```

## 🏗️ Project Structure

```
SCBackEnd/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── events/
│   │   ├── __init__.py
│   │   └── routes.py          # Events endpoints
│   ├── wellness/
│   │   └── routes.py          # Wellness endpoints
│   ├── safety/
│   │   └── routes.py          # Safety endpoints
│   ├── orchestrator/
│   │   └── routes.py          # Orchestrator endpoints
│   └── shared/
│       └── supabase.py        # Supabase connection
├── z_Docs/                    # Complete documentation
│   ├── API_REFERENCE.md       # Full API docs
│   ├── FRONTEND_INTEGRATION.md # Frontend guide
│   ├── RENDER_DEPLOYMENT.md   # Deployment guide
│   ├── SETUP_GUIDE.md         # Setup instructions
│   └── PROJECT_SUMMARY.md     # Project overview
├── requirements.txt           # Python dependencies
├── render.yaml                # Render deployment config
├── build.sh                   # Build script
├── supabase_schema.sql        # Database schema
├── env_template.txt           # Environment variables template
├── DEPLOYMENT_CHECKLIST.md    # Deployment checklist
├── QUICK_REFERENCE.md         # One-page quick reference
├── README.md                  # This file
└── .gitignore                # Git ignore rules
```

## 🔐 Security Notes

- Never commit your `.env` file
- Keep your Supabase keys secure
- In production, use proper authentication (Supabase Auth)
- Restrict RLS policies for production use
- Enable HTTPS in production

## 🧪 Testing

### Manual Testing
Use the interactive API docs at http://localhost:8000/docs to test all endpoints.

### With cURL
See example commands above.

### With Postman/Insomnia
Import the OpenAPI schema from http://localhost:8000/openapi.json

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Your Supabase anon/public key | Yes |
| `API_HOST` | API host (default: 0.0.0.0) | No |
| `API_PORT` | API port (default: 8000) | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |

## 📦 Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Supabase**: PostgreSQL database client
- **Pydantic**: Data validation
- **python-dotenv**: Environment variables

See `requirements.txt` for full list.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Frontend Integration

This backend is designed to be consumed by a frontend application.

**📖 See [FRONTEND_INTEGRATION.md](z_Docs/FRONTEND_INTEGRATION.md) for complete integration guide** including:
- API service setup (JavaScript/TypeScript)
- React hooks examples
- Error handling patterns
- Type definitions

### Quick Example (JavaScript/React)
```javascript
// Get events
const response = await fetch('http://localhost:8000/api/events/list');
const data = await response.json();
console.log(data.events);

// Create event
const newEvent = {
  title: "New Event",
  date: "2025-12-25",
  time: "10:00",
  location: "Community Center"
};

const response = await fetch('http://localhost:8000/api/events/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(newEvent)
});
```

## 🚀 Production Deployment

### Deploy to Render (Recommended)

**📖 See [RENDER_DEPLOYMENT.md](z_Docs/RENDER_DEPLOYMENT.md) for complete deployment guide**

Quick steps:
1. Push code to GitHub
2. Connect to Render.com
3. Add environment variables
4. Deploy! 🎉

Your backend will be live at: `https://your-service.onrender.com`

**Deployment files included**:
- `render.yaml` - Render configuration
- `build.sh` - Build script

## 🐛 Troubleshooting

### Supabase Connection Error
- Check your `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Ensure you've run the SQL schema in Supabase
- Verify your Supabase project is active

### Port Already in Use
- Change the port: `uvicorn app.main:app --port 8001`
- Or kill the process using port 8000

### Module Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## 📄 License

[Add your license here]

## 👨‍💻 Author

[Your name/organization]

---

**Ready to integrate with your frontend! 🎉**

For questions or support, please open an issue on GitHub.

