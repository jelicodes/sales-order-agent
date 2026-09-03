### Task 11: Fix rate limiter duplication

**Files:**
- Modify: `src/api/chat.py`

**Interfaces:**
- Consumes: `app.state.limiter` from main.py
- Produces: single rate limiter instance

- [ ] **Step 1: Update chat.py to use app.state.limiter**

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

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add src/api/chat.py
git commit -m "fix: remove duplicate Limiter, use app.state.limiter"
```
