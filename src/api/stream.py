import json
import uuid
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from langgraph.types import Command
from groq import RateLimitError as GroqRateLimitError
from src.agents.graph import create_sales_agent
from src.api.models import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)


def _sse_event(event: str, data: dict | str) -> str:
    """Format a single SSE event."""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_chat(req: ChatRequest, request: Request) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE events from the sales agent."""
    checkpointer = request.app.state.checkpointer
    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())

    logger.info(f"[{request_id}] SSE stream request: session={session_id}")

    # Send session info first
    yield _sse_event("session_info", {
        "session_id": session_id,
        "request_id": request_id,
    })

    agent = create_sales_agent(checkpointer=checkpointer)

    try:
        config = {"configurable": {"thread_id": session_id}}
        upper = req.message.strip().upper()

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

        # Handle HITL interrupt
        if isinstance(result, dict) and "__interrupt__" in result:
            interrupts = result["__interrupt__"]
            if interrupts:
                item = interrupts[0]
                payload = item.value if hasattr(item, "value") else item
                yield _sse_event("hitl_interrupt", {
                    "type": "hitl_interrupt",
                    "data": payload if isinstance(payload, dict) else {"message": str(payload)},
                })
                yield _sse_event("text_delta", "[Menunggu konfirmasi Anda]")
                yield _sse_event("stream_end", {"status": "interrupted"})
                return

        # Process messages from result
        messages = result.get("messages", []) if isinstance(result, dict) else []
        for msg in messages:
            # Skip HumanMessage - only process AI responses
            if isinstance(msg, HumanMessage):
                continue

            content = msg.content if hasattr(msg, "content") else str(msg)

            # Handle ORDER_PENDING in dict format
            if isinstance(content, dict):
                if content.get("ORDER_PENDING"):
                    yield _sse_event("tool_output", {
                        "type": "order_pending",
                        "data": content["ORDER_PENDING"] if isinstance(content["ORDER_PENDING"], str) else json.dumps(content["ORDER_PENDING"], ensure_ascii=False),
                    })
                    continue
                # Check for structured tool outputs
                for key in ("product_cards", "price_breakdown", "order_summary", "reorder_suggestions"):
                    if key in content:
                        yield _sse_event("tool_output", {
                            "type": key,
                            "data": content[key],
                        })
                        break
                else:
                    logger.warning(f"[{request_id}] Unknown dict content type: {list(content.keys())}")
                    continue

            # Handle string content
            if isinstance(content, str) and content:
                # Check for ORDER_PENDING in string format
                if "ORDER_PENDING" in content:
                    try:
                        _, order_data_str = content.split("ORDER_PENDING|", 1)
                        yield _sse_event("tool_output", {
                            "type": "order_pending",
                            "data": order_data_str,
                        })
                    except ValueError:
                        yield _sse_event("text_delta", content)
                else:
                    yield _sse_event("text_delta", content)

        yield _sse_event("stream_end", {"status": "ok"})

    except GroqRateLimitError:
        logger.warning(f"[{request_id}] Groq rate limit exceeded")
        yield _sse_event("error", {
            "type": "rate_limit",
            "message": "Maaf, layanan AI sedang sibuk. Silakan coba lagi dalam 1-2 menit.",
        })
        yield _sse_event("stream_end", {"status": "error"})
    except Exception as e:
        logger.error(f"[{request_id}] Stream error: {e}", exc_info=True)
        yield _sse_event("error", {
            "type": "server_error",
            "message": "Terjadi kesalahan. Silakan coba lagi atau hubungi admin.",
        })
        yield _sse_event("stream_end", {"status": "error"})


@router.post("/chat/stream")
async def chat_stream(request: Request, req: ChatRequest):
    """SSE streaming endpoint for chat."""
    return StreamingResponse(
        _stream_chat(req, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
