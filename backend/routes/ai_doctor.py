from fastapi import APIRouter
router = APIRouter(prefix="/api/ai-doctor", tags=["ai-doctor"])
@router.get("/status")
async def status(): return {"agent": "ai_doctor", "status": "coming_soon"}
