from services.agora_service import AgoraService
class CallingBuddyService:
    def __init__(self): self.agora = AgoraService()
    async def start(self): return await self.agora.start_session()
    async def stop(self, session_id): return await self.agora.stop_session(session_id)
    def status(self): return {"agent": "calling_buddy", "status": self.agora.status()}
