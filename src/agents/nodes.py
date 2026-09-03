from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
from src.agents.state import AgentState
from src.agents.prompts import SALES_AGENT_PROMPT
from src.tools.search_products import search_products
from src.tools.get_product_detail import get_product_detail
from src.tools.check_stock import check_stock
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives
from src.config.settings import settings
from src.config.langfuse import get_langfuse_handler

tools = [search_products, get_product_detail, check_stock, calculate_price, create_quote, get_alternatives]

_llm_instance = None


def get_llm():
    """Get or create cached LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
        ).bind_tools(tools)
    return _llm_instance


def create_llm():
    """Create new LLM instance (for testing or when cache needs refresh)."""
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    ).bind_tools(tools)


def llm_node(state: AgentState) -> dict:
    llm = get_llm()
    messages = list(state["messages"])
    if not messages or not (isinstance(messages[0], SystemMessage) and SALES_AGENT_PROMPT in messages[0].content):
        messages = [SystemMessage(content=SALES_AGENT_PROMPT)] + messages

    langfuse_handler = get_langfuse_handler()
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}


tool_node = ToolNode(tools)
