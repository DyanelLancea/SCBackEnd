from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator.routes import router as orchestrator_router
from app.safety.routes import router as safety_router
from app.wellness.routes import router as wellness_router

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orchestrator_router, prefix="/orchestrator")
app.include_router(wellness_router, prefix="/wellness")
app.include_router(safety_router, prefix="/safety")


@app.get("/")
def root():
    return {"status": "Backend running"}
