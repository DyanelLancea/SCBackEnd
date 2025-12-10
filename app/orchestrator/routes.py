from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def orchestrator_root():
    return {"status": "Orchestrator agent running"}

