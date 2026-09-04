from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    context: dict
    customer_id: Optional[str]
    pending_order: Optional[dict]
    confirmation_status: Optional[str]  # none, awaiting, confirmed
