import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message
from src.api.models import ChatRequest, ChatResponse

router = APIRouter()
agent = create_sales_agent()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")
    
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        create_session(session_id, req.customer_name)
        logger.info(f"[{request_id}] New session created: {session_id}")

    history = get_conversation_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    result = await asyncio.to_thread(
        agent.invoke,
        {
            "messages": messages,
            "session_id": session_id,
            "context": {"request_id": request_id},
        }
    )

    save_message(session_id, "user", req.message)
    response_content = result["messages"][-1].content
    save_message(session_id, "assistant", response_content)
    
    logger.info(f"[{request_id}] Response sent successfully")

    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )