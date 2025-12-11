"""
SC Backend - Main FastAPI Application
Multi-agent system for community engagement platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import Supabase connection
from app.shared.supabase import get_supabase_client, test_connection

# Import all module routers
from app.wellness.routes import router as wellness_router
from app.safety.routes import router as safety_router
from app.orchestrator.routes import router as orchestrator_router
from app.events.routes import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Runs on startup and shutdown
    """
    print("\n" + "="*60)
    print("🚀 Starting SC Backend API...")
    print("="*60)
    
    # Test Supabase connection
    try:
        test_connection()
        print("✅ All systems ready!")
    except Exception as e:
        print(f"⚠️ Warning: Database connection issue: {e}")
        print("   Continue anyway, but some features may not work.")
    
    yield
    
    print("\n👋 Shutting down SC Backend...")


# Create FastAPI application
app = FastAPI(
    title="SC Backend API",
    description="Backend API for community engagement and social platform with events management",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS - Allow frontend to make requests
# Note: When allow_credentials=True, you cannot use "*" for allow_origins
# You must specify exact origins or use allow_origin_regex
import os
import re

# Get allowed origins from environment or use defaults
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Parse comma-separated origins from environment
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default origins for development
    allowed_origins = [
        "http://localhost:3000",      # Next.js default
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

# Use regex pattern to allow all subdomains for common hosting platforms
# This allows any Vercel, Netlify, or Render frontend
allowed_origin_regex = r"https://.*\.(vercel\.app|netlify\.app|onrender\.com)$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,  # Set to False if you don't need cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
def root():
    """API welcome message and available endpoints"""
    return {
        "message": "Welcome to SC Backend API! 🎉",
        "status": "running",
        "version": "2.0.0",
        "documentation": {
            "interactive": "/docs",
            "alternative": "/redoc"
        },
        "modules": {
            "events": "/api/events - Event creation and management",
            "wellness": "/api/wellness - Social engagement and wellness",
            "safety": "/api/safety - Safety and emergency response",
            "orchestrator": "/api/orchestrator - Main coordinator"
        },
        "database": "Supabase (PostgreSQL)"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        get_supabase_client()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "message": "API is running",
        "database": db_status,
        "timestamp": "2025-12-10"
    }


# ==================== REGISTER MODULE ROUTERS ====================

# Events Module - Primary feature for event management
app.include_router(
    events_router,
    prefix="/api/events",
    tags=["Events"]
)

# Wellness Module - Social engagement and wellness features
app.include_router(
    wellness_router,
    prefix="/api/wellness",
    tags=["Wellness & Social"]
)

# Safety Module - Emergency and safety features
app.include_router(
    safety_router,
    prefix="/api/safety",
    tags=["Safety & Emergency"]
)

# Orchestrator Module - Main coordinator and AI agent
app.include_router(
    orchestrator_router,
    prefix="/api/orchestrator",
    tags=["Orchestrator"]
)


# ==================== ERROR HANDLERS ====================

from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist",
            "docs": "/docs",
            "available_modules": ["/api/events", "/api/wellness", "/api/safety", "/api/orchestrator"]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong. Please try again later or contact support."
        }
    )


# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 SC BACKEND API")
    print("="*60)
    print("\n📍 Server starting at:")
    print("   http://localhost:8000")
    print("\n📚 API Documentation:")
    print("   http://localhost:8000/docs")
    print("\n🔗 Module Endpoints:")
    print("   • Events:       http://localhost:8000/api/events")
    print("   • Wellness:     http://localhost:8000/api/wellness")
    print("   • Safety:       http://localhost:8000/api/safety")
    print("   • Orchestrator: http://localhost:8000/api/orchestrator")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )

