### Task 3: Add async wrapping for database calls

**Files:**
- Modify: `src/api/chat.py`
- Modify: `src/api/session.py`
- Modify: `src/api/health.py`

**Interfaces:**
- Consumes: existing sync database functions
- Produces: non-blocking async handlers

- [ ] **Step 1: Update chat.py with async DB calls**

```python
import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message
from src.api.models import ChatRequest, ChatResponse

router = APIRouter()
agent = create_sales_agent()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        await asyncio.to_thread(create_session, session_id, req.customer_name)
        logger.info(f"[{request_id}] New session created: {session_id}")

    history = await asyncio.to_thread(get_conversation_history, session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

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
        }
    )

    await asyncio.to_thread(save_message, session_id, "user", req.message)
    response_content = result["messages"][-1].content
    await asyncio.to_thread(save_message, session_id, "assistant", response_content)

    logger.info(f"[{request_id}] Response sent successfully")

    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )
```

- [ ] **Step 2: Update session.py with async DB calls**

```python
import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from src.data.database import create_session, get_session
from src.api.models import CreateSessionRequest, CreateSessionResponse, SessionResponse

router = APIRouter()


@router.post("/session", response_model=CreateSessionResponse)
async def create_session_endpoint(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    session = await asyncio.to_thread(create_session, session_id, req.customer_name)
    return CreateSessionResponse(session_id=session_id, status=session["status"])


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    session = await asyncio.to_thread(get_session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)
```

- [ ] **Step 3: Update health.py with async DB calls**

```python
import sqlite3
import asyncio
from pathlib import Path
from fastapi import APIRouter
from src.config.settings import settings, APP_VERSION
from src.config.langfuse import get_langfuse_handler
from src.api.models import HealthResponse, HealthCheckResult

router = APIRouter()


def check_database_sync() -> dict:
    try:
        db_path = Path(settings.DATABASE_PATH)
        if not db_path.exists():
            return {"status": "error", "message": "Database file not found"}
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return {"status": "ok", "products_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_chromadb() -> dict:
    try:
        chromadb_path = Path(settings.CHROMADB_PATH)
        if not chromadb_path.exists():
            return {"status": "warning", "message": "ChromaDB directory not found (will be created on first use)"}
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_groq() -> dict:
    try:
        if not settings.GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}
        return {"status": "ok", "model": settings.GROQ_MODEL}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_langfuse() -> dict:
    handler = get_langfuse_handler()
    if handler:
        return {"status": "ok", "enabled": True}
    return {"status": "disabled", "enabled": False}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = await asyncio.to_thread(check_database_sync)
    chromadb_status = check_chromadb()
    groq_status = check_groq()
    langfuse_status = check_langfuse()

    overall_status = "ok"
    if db_status["status"] == "error" or groq_status["status"] == "error":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        service="sales-order-agent",
        version=APP_VERSION,
        checks={
            "database": HealthCheckResult(**db_status),
            "chromadb": HealthCheckResult(**chromadb_status),
            "groq": HealthCheckResult(**groq_status),
            "langfuse": HealthCheckResult(**langfuse_status),
        }
    )
```

- [ ] **Step 4: Run existing tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/api/chat.py src/api/session.py src/api/health.py
git commit -m "feat: wrap sync DB calls with asyncio.to_thread for non-blocking async"
```
