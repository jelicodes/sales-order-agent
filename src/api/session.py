import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from src.data.database import create_session, get_session

router = APIRouter()

class CreateSessionRequest(BaseModel):
    customer_name: str = ""

@router.post("/session")
async def create_session_endpoint(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    session = create_session(session_id, req.customer_name)
    return {"session_id": session_id, "status": session["status"]}

@router.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session