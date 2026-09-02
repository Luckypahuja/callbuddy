from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.calling_buddy_service import CallingBuddyService
router = APIRouter(prefix="/api/calling-buddy", tags=["calling-buddy"])
service = CallingBuddyService()
class StopRequest(BaseModel): session_id: str
@router.post("/start")
async def start():
    try: return await service.start()
    except RuntimeError as exc: raise HTTPException(status_code=503, detail="Unable to connect to Calling Buddy. " + str(exc)) from exc
@router.post("/stop")
async def stop(request: StopRequest):
    try: return await service.stop(request.session_id)
    except RuntimeError as exc: raise HTTPException(status_code=503, detail="Unable to stop Calling Buddy. " + str(exc)) from exc
@router.get("/status")
async def status(): return service.status()
