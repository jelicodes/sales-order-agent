import json
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
    content = last_message.content if hasattr(last_message, "content") else ""
    if "ORDER_PENDING" in content:
        return "confirmation"
    return END


def confirmation_node(state: AgentState) -> Command[Literal["llm"]]:
    """Handle order confirmation via interrupt."""
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, "content") else ""

    if "ORDER_PENDING" not in content:
        return Command(goto="llm")

    try:
        _, order_data_str = content.split("ORDER_PENDING|", 1)
        order_data = json.loads(order_data_str)
    except (ValueError, json.JSONDecodeError):
        return Command(goto="llm")

    order_summary = f"Order {order_data['items'][0].get('product_name', 'N/A')} - {order_data['items'][0].get('qty', 0)} pcs - Total: Rp {order_data['total_price']:,}"

    human_response = interrupt({
        "action": "create_order",
        "summary": order_summary,
        "message": "Ketik 'YA' untuk konfirmasi order atau 'BATAL' untuk membatalkan"
    })

    if human_response and str(human_response).strip().upper() == "YA":
        order = db_create_order(
            customer_id=order_data["customer_id"],
            items=order_data["items"],
            subtotal=order_data["subtotal"],
            discount_amount=0,
            total_price=order_data["total_price"],
            shipping_address=order_data.get("shipping_address"),
            notes=order_data.get("notes"),
        )
        return Command(
            update={
                "pending_order": None,
                "confirmation_status": "confirmed",
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
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", "confirmation": "confirmation", END: END})
    graph.add_edge("tools", "llm")
    graph.add_edge("confirmation", "llm")
    return graph.compile(checkpointer=checkpointer)
