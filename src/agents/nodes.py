from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from src.agents.state import AgentState
from src.agents.prompts import SALES_AGENT_PROMPT
from src.tools.search_products import search_products
from src.tools.get_product_detail import get_product_detail
from src.tools.check_stock import check_stock
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives
from src.config.settings import settings

tools = [search_products, get_product_detail, check_stock, calculate_price, create_quote, get_alternatives]


def create_llm():
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    ).bind_tools(tools)


def llm_node(state: AgentState) -> dict:
    llm = create_llm()
    messages = list(state["messages"])
    # Prepend system prompt if not already present
    if not messages or not (isinstance(messages[0], HumanMessage) and SALES_AGENT_PROMPT in messages[0].content):
        messages = [HumanMessage(content=SALES_AGENT_PROMPT)] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}

    tool_map = {
        "search_products": search_products,
        "get_product_detail": get_product_detail,
        "check_stock": check_stock,
        "calculate_price": calculate_price,
        "create_quote": create_quote,
        "get_alternatives": get_alternatives,
    }

    results = []
    for tool_call in last_message.tool_calls:
        tool_func = tool_map.get(tool_call["name"])
        if tool_func:
            result = tool_func.invoke(tool_call["args"])
            results.append(
                {"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]}
            )

    return {"messages": results}
