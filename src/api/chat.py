import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage, trim_messages
from langgraph.types import Command
from groq import RateLimitError as GroqRateLimitError
from src.agents.graph import create_sales_agent
from src.api.models import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    checkpointer = request.app.state.checkpointer
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id or str(uuid.uuid4())
    agent = create_sales_agent(checkpointer=checkpointer)

    try:
        # Handle resume from interrupt
        if req.message.upper() == "YA" or req.message.upper() == "BATAL":
            config = {"configurable": {"thread_id": session_id}}
            result = await asyncio.to_thread(
                agent.invoke,
                Command(resume=req.message),
                config,
            )
        else:
            messages = [HumanMessage(content=req.message)]
            messages = trim_messages(
                messages,
                max_tokens=8000,
                token_counter=len,
                strategy="last",
                start_on="human",
            )
            config = {"configurable": {"thread_id": session_id}}
            result = await asyncio.to_thread(
                agent.invoke,
                {
                    "messages": messages,
                    "session_id": session_id,
                    "context": {"request_id": request_id},
                    "customer_id": None,
                    "pending_order": None,
                    "confirmation_status": None,
                },
                config,
            )

        response_content = result["messages"][-1].content
        logger.info(f"[{request_id}] Response sent successfully")

        return ChatResponse(
            response=response_content,
            session_id=session_id,
            request_id=request_id,
        )

    except GroqRateLimitError:
        logger.warning(f"[{request_id}] Groq rate limit exceeded")
        return ChatResponse(
            response="Maaf, layanan AI sedang sibuk. Silakan coba lagi dalam 1-2 menit.",
            session_id=session_id,
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        return ChatResponse(
            response="Terjadi kesalahan. Silakan coba lagi atau hubungi admin.",
            session_id=session_id,
            request_id=request_id,
        )
