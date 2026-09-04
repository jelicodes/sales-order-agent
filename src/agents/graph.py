from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy, interrupt, Command
from src.agents.state import AgentState
from src.agents.nodes import llm_node, tool_node
from src.data.database import create_order as db_create_order


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def confirmation_node(state: AgentState) -> Command[Literal["llm"]]:
    """Handle order confirmation via interrupt."""
    pending_order = state.get("pending_order")
    if not pending_order:
        return Command(goto="llm")

    order_summary = pending_order.get("summary", "")
    human_response = interrupt({
        "action": "create_order",
        "summary": order_summary,
        "message": "Ketik 'YA' untuk konfirmasi order atau 'BATAL' untuk membatalkan"
    })

    if human_response and str(human_response).strip().upper() == "YA":
        order = db_create_order(
            customer_id=pending_order["customer_id"],
            items=pending_order["items"],
            subtotal=pending_order["subtotal"],
            discount_amount=pending_order.get("discount_amount", 0),
            total_price=pending_order["total_price"],
            shipping_address=pending_order.get("shipping_address"),
            notes=pending_order.get("notes"),
        )
        return Command(
            update={
                "pending_order": None,
                "confirmation_status": "confirmed",
                "last_order_id": order["id"],
            },
            goto="llm"
        )
    else:
        return Command(
            update={"pending_order": None, "confirmation_status": None},
            goto="llm"
        )


def create_sales_agent(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node, retry_policy=RetryPolicy(max_attempts=3))
    graph.add_node("tools", tool_node)
    graph.add_node("confirmation", confirmation_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile(checkpointer=checkpointer)
