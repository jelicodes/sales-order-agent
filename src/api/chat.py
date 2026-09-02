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

    history = get_conversation_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    result = agent.invoke({
        "messages": messages,
        "session_id": session_id,
        "context": {},
    })

    save_message(session_id, "user", req.message)
    response_content = result["messages"][-1].content
    save_message(session_id, "assistant", response_content)

    return {
        "response": response_content,
        "session_id": session_id,
    }