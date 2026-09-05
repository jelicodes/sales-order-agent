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


def _extract_response(result: dict) -> str:
    """Extract response content, handling both normal and interrupt states."""
    # Check if graph hit an interrupt (HITL pause)
    if "__interrupt__" in result:
        interrupts = result["__interrupt__"]
        if interrupts:
            item = interrupts[0]
            # Interrupt objects have a .value attribute
            payload = item.value if hasattr(item, "value") else item
            if isinstance(payload, dict):
                lines = []
                if payload.get("action") == "create_order":
                    lines.append("Konfirmasi Order")
                    if payload.get("summary"):
                        lines.append(payload["summary"])
                    lines.append("")
                    lines.append(payload.get("message", "Ketik YA untuk konfirmasi atau BATAL untuk membatalkan."))
                else:
                    lines.append(str(payload))
                return "\n".join(lines)
            return str(payload)

    # Normal response
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        content = last.content if hasattr(last, "content") else str(last)
        if content:
            return content

    return "Maaf, tidak ada respons. Silakan coba lagi."


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    checkpointer = request.app.state.checkpointer
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id or str(uuid.uuid4())
    agent = create_sales_agent(checkpointer=checkpointer)

    try:
        config = {"configurable": {"thread_id": session_id}}
        upper = req.message.strip().upper()

        # Handle resume from interrupt
        if upper in ("YA", "BATAL"):
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
            result = await asyncio.to_thread(
                agent.invoke,
                {
                    "messages": messages,
                    "session_id": session_id,
                    "context": {"request_id": request_id},
                },
                config,
            )

        response_content = _extract_response(result)
        logger.info(f"[{request_id}] Result type={type(result).__name__}, keys={list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        if isinstance(result, dict):
            if "__interrupt__" in result:
                logger.info(f"[{request_id}] HITL INTERRUPT detected")
            msgs = result.get("messages", [])
            logger.info(f"[{request_id}] Messages: {len(msgs)}")
            if msgs:
                last = msgs[-1]
                c = last.content if hasattr(last, "content") else str(last)
                logger.info(f"[{request_id}] Last msg: {type(last).__name__}, content={str(c)[:150]}")
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
