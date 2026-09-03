import uuid
from fastapi import APIRouter, HTTPException
from src.data.database import create_session, get_session
from src.api.models import CreateSessionRequest, CreateSessionResponse, SessionResponse

router = APIRouter()

@router.post("/session", response_model=CreateSessionResponse)
async def create_session_endpoint(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    session = create_session(session_id, req.customer_name)
    return CreateSessionResponse(session_id=session_id, status=session["status"])

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)