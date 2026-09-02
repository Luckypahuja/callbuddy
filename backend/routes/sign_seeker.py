from fastapi import APIRouter
router = APIRouter(prefix="/api/sign-seeker", tags=["sign-seeker"])
@router.get("/status")
async def status(): return {"agent": "sign_seeker", "status": "coming_soon"}
