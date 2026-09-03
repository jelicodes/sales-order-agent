from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from src.agents.state import AgentState
from src.agents.nodes import llm_node, tool_node


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_sales_agent():
    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node, retry_policy=RetryPolicy(max_attempts=3))
    graph.add_node("tools", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile()
