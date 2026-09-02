from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, Case
from schemas import CaseCreate, CaseResponse



from routes.ai_doctor import router as ai_doctor_router
from routes.calling_buddy import router as calling_buddy_router
from routes.sign_seeker import router as sign_seeker_router

from mcp_server import mcp, mcp_app


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="EchoSphere API",
    description="Multilingual assistance platform",
    version="1.0.0",
    lifespan=lifespan,
)


# MCP web-search endpoint
app.mount("/mcp", mcp_app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(calling_buddy_router)
app.include_router(ai_doctor_router)
app.include_router(sign_seeker_router)


@app.get("/")
def root():
    return {
        "message": "EchoSphere backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post(
    "/api/cases",
    response_model=CaseResponse,
)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db),
):
    item = Case(
        **case.model_dump()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@app.get(
    "/api/cases",
    response_model=list[CaseResponse],
)
def get_cases(
    db: Session = Depends(get_db),
):
    return db.query(Case).all()


@app.get(
    "/api/cases/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(Case)
        .filter(Case.id == case_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return item