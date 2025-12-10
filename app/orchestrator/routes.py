from fastapi import APIRouter

from app.supabase import supabase

router = APIRouter()


@router.get("/")
def orchestrator_root():
    return {"status": "Orchestrator agent running"}

