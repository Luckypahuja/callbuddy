from pydantic import BaseModel
from typing import Optional


class CaseCreate(BaseModel):
    customer_name: Optional[str] = None
    language: Optional[str] = None

    state: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    pincode: Optional[str] = None

    intent: Optional[str] = None

    priority: str = "MEDIUM"


class CaseResponse(CaseCreate):
    id: int

    confidence: Optional[float] = None

    status: str

    summary: Optional[str] = None

    escalation_reason: Optional[str] = None

    recommended_action: Optional[str] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str

    session_id: str = "default"


class ChatResponse(BaseModel):
    session_id: str

    response: str

    language: str

    intent: Optional[str] = None