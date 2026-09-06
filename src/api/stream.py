import json
import re
import uuid
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, trim_messages
from langgraph.types import Command
from groq import RateLimitError as GroqRateLimitError
from src.agents.graph import create_sales_agent
from src.api.models import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)

STRUCTURED_OUTPUT_KEYS = ("product_cards", "price_breakdown", "order_summary", "reorder_suggestions")
JSON_TOOL_PATTERN = re.compile(
    r'^\s*\{.*"(?:available|total_stock|variants|error|message)"\s*:',
    re.DOTALL,
)


def _sse_event(event: str, data: dict | str) -> str:
    """Format a single SSE event."""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


def _is_raw_tool_json(content: str) -> bool:
    """Detect raw tool output JSON that should not be shown as chat text."""
    if not content.startswith("{"):
        return False
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(parsed, dict):
        return False
    if any(key in parsed for key in STRUCTURED_OUTPUT_KEYS):
        return False
    if "type" in parsed and "data" in parsed:
        return False
    return bool(JSON_TOOL_PATTERN.match(content))


def _get_message_count(checkpointer, session_id: str) -> int:
    """Get the current message count from checkpointer state."""
    try:
        config = {"configurable": {"thread_id": session_id}}
        snapshot = checkpointer.get(config)
        if snapshot and "channel_values" in snapshot:
            return len(snapshot["channel_values"].get("messages", []))
    except Exception:
        pass
    return 0


async def _stream_chat(req: ChatRequest, request: Request) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE events from the sales agent."""
    checkpointer = request.app.state.checkpointer
    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())

    logger.info(f"[{request_id}] SSE stream request: session={session_id}")

    yield _sse_event("session_info", {
        "session_id": session_id,
        "request_id": request_id,
    })

    agent = create_sales_agent(checkpointer=checkpointer)

    try:
        config = {"configurable": {"thread_id": session_id}}
        prev_count = _get_message_count(checkpointer, session_id)
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

        all_messages = result.get("messages", []) if isinstance(result, dict) else []
        new_messages = all_messages[prev_count:] if prev_count > 0 else all_messages

        for msg in new_messages:
            if isinstance(msg, HumanMessage):
                continue

            content = msg.content if hasattr(msg, "content") else str(msg)

            if isinstance(content, str) and not content.strip():
                continue

            if isinstance(msg, ToolMessage):
                _type = None
                try:
                    parsed = json.loads(content) if isinstance(content, str) else content
                    if isinstance(parsed, dict):
                        if "type" in parsed and "data" in parsed:
                            _type = parsed["type"]
                        else:
                            for key in STRUCTURED_OUTPUT_KEYS:
                                if key in parsed:
                                    _type = key
                                    break
                except (json.JSONDecodeError, ValueError):
                    pass

                if _type:
                    data = parsed.get("data", parsed) if isinstance(parsed, dict) else content
                    yield _sse_event("tool_output", {"type": _type, "data": data})
                continue

            if isinstance(content, dict):
                if content.get("ORDER_PENDING"):
                    order_val = content["ORDER_PENDING"]
                    yield _sse_event("tool_output", {
                        "type": "order_pending",
                        "data": order_val if isinstance(order_val, str) else json.dumps(order_val, ensure_ascii=False),
                    })
                    continue
                for key in STRUCTURED_OUTPUT_KEYS:
                    if key in content:
                        yield _sse_event("tool_output", {"type": key, "data": content[key]})
                        break
                else:
                    logger.debug(f"[{request_id}] Skipping non-structured dict: {list(content.keys())}")
                continue

            if isinstance(content, str) and content:
                if "ORDER_PENDING" in content:
                    try:
                        _, order_data_str = content.split("ORDER_PENDING|", 1)
                        yield _sse_event("tool_output", {
                            "type": "order_pending",
                            "data": order_data_str,
                        })
                    except ValueError:
                        yield _sse_event("text_delta", content)
                elif _is_raw_tool_json(content):
                    logger.debug(f"[{request_id}] Skipping raw tool JSON in text_delta")
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
