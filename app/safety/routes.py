from fastapi import APIRouter

from app.supabase import supabase

router = APIRouter()


@router.post("/sos")
def send_sos(data: dict):
    response = supabase.table("sos_logs").insert(data).execute()
    return {"success": True, "data": response.data}

