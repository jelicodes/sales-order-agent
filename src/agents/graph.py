import json
from typing import Literal
from langchain_core.messages import ToolMessage
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


def after_tools(state: AgentState) -> str:
    """Check if any tool result contains ORDER_PENDING."""
    # If already confirmed, skip confirmation
    if state.get("confirmation_status") == "confirmed":
        return "llm"
    for msg in state["messages"]:
        content = msg.content if hasattr(msg, "content") else ""
        if "ORDER_PENDING" in str(content):
            return "confirmation"
    return "llm"


def confirmation_node(state: AgentState) -> Command[Literal["llm"]]:
    """Handle order confirmation via interrupt."""
    # Find the ORDER_PENDING message
    order_data = None
    for msg in state["messages"]:
        content = msg.content if hasattr(msg, "content") else ""
        if "ORDER_PENDING" in str(content):
            try:
                _, order_data_str = str(content).split("ORDER_PENDING|", 1)
                order_data = json.loads(order_data_str)
            except (ValueError, json.JSONDecodeError):
                continue
            break

    if not order_data:
        return Command(goto="llm")

    # Find the original tool_call_id from the create_order tool call
    tool_call_id = "create_order_confirmed"
    for msg in state["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "create_order":
                    tool_call_id = tc.get("id", tool_call_id)
                    break

    order_summary = f"Order {order_data['items'][0].get('product_name', 'N/A')} - {order_data['items'][0].get('qty', 0)} pcs - Total: Rp {order_data['total_price']:,}"

    human_response = interrupt({
        "action": "create_order",
        "summary": order_summary,
        "message": "Ketik 'YA' untuk konfirmasi order atau 'BATAL' untuk membatalkan"
    })

    response_text = str(human_response).strip().lower() if human_response else ""

    # Keyword matching for confirmation/cancellation
    # Works for both chat-based (free text) and button-based (exact "YA"/"BATAL") flows
    confirm_keywords = ("ya", "ok", "oke", "konfirmasi", "setuju", "lanjut", "proceed", "yes")
    cancel_keywords = ("batal", "cancel", "tidak", "no", "goback", "kembali")

    is_confirmed = any(kw in response_text for kw in confirm_keywords)
    is_cancelled = any(kw in response_text for kw in cancel_keywords)

    # If both present, cancel wins (safer to not create order by accident)
    if is_cancelled:
        is_confirmed = False

    if is_confirmed and not is_cancelled:
        order = db_create_order(
            customer_id=order_data["customer_id"],
            items=order_data["items"],
            subtotal=order_data["subtotal"],
            discount_amount=0,
            total_price=order_data["total_price"],
            shipping_address=order_data.get("shipping_address"),
            notes=order_data.get("notes"),
        )
        order_id = order["id"]
        customer_name = order_data.get("customer_name", "Bapak/Ibu")
        product_name = order_data["items"][0].get("product_name", "")
        qty = order_data["items"][0].get("qty", 0)
        confirmed_msg = (
            f"Order {order_id} telah berhasil dibuat dan dikonfirmasi. "
            f"Pelanggan: {customer_name}. "
            f"Produk: {product_name} {qty} pcs. "
            f"Total: Rp {order_data['total_price']:,}. "
            f"Status: pending. "
            f"Sampaikan kepada pelanggan bahwa order telah berhasil dibuat."
        )
        return Command(
            update={
                "messages": [ToolMessage(content=confirmed_msg, name="create_order", tool_call_id=tool_call_id)],
                "pending_order": None,
                "confirmation_status": "confirmed",
                "customer_id": order_data["customer_id"],
            },
            goto="llm"
        )
    else:
        return Command(
            update={
                "messages": [ToolMessage(content="Order dibatalkan oleh pelanggan.", name="create_order", tool_call_id=tool_call_id)],
                "pending_order": None,
                "confirmation_status": None,
            },
            goto="llm"
        )


def create_sales_agent(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node, retry_policy=RetryPolicy(max_attempts=3))
    graph.add_node("tools", tool_node)
    graph.add_node("confirmation", confirmation_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_conditional_edges("tools", after_tools, {"llm": "llm", "confirmation": "confirmation"})
    graph.add_edge("confirmation", "llm")
    return graph.compile(checkpointer=checkpointer)
