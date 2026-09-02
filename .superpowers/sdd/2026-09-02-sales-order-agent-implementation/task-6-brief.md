# Task 6: FastAPI Endpoints

## Files to Create
- `src/api/__init__.py`
- `src/api/health.py`
- `src/api/session.py`
- `src/api/chat.py`
- `src/main.py`
- `tests/test_api.py`

## Prerequisites
- Task 5 completed: `src/agents/graph.py` exists with `create_sales_agent()` function
- Task 3 completed: `src/data/database.py` exists with all CRUD functions

## What to Do

### 1. Create `src/api/health.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "sales-order-agent"}
```

### 2. Create `src/api/session.py`

```python
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
```

### 3. Create `src/api/chat.py`

```python
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message

router = APIRouter()
agent = create_sales_agent()

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    customer_name: str = ""

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        create_session(session_id, req.customer_name)

    # Build message history from DB
    history = get_conversation_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    # Run agent
    result = agent.invoke({
        "messages": messages,
        "session_id": session_id,
        "context": {},
    })

    # Save conversation to DB
    save_message(session_id, "user", req.message)
    response_content = result["messages"][-1].content
    save_message(session_id, "assistant", response_content)

    return {
        "response": response_content,
        "session_id": session_id,
    }
```

### 4. Create `src/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.data.database import init_db
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sales Order Agent - PT Lemone",
    description="AI Agent untuk membantu proses order fashion grosir B2B",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(session_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import settings
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
```

### 5. Create `tests/test_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestSession:
    def test_create_session(self):
        response = client.post("/session", json={"customer_name": "Test User"})
        assert response.status_code == 200
        assert "session_id" in response.json()

class TestChat:
    def test_chat_without_session(self):
        response = client.post("/chat", json={"message": "Halo"})
        assert response.status_code == 200
        assert "response" in response.json()
        assert "session_id" in response.json()
```

## Verification
1. Seed DB: `D:\Jeli\myenv\Scripts\python.exe -m src.data.seed.seed`
2. Run tests: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py -v`
3. Test server: `D:\Jeli\myenv\Scripts\python.exe -m src.main`
4. Open docs: http://localhost:8000/docs

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-6-report.md`
