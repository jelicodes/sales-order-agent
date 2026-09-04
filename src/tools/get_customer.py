from langchain_core.tools import tool
from src.data.database import get_customer_by_id, get_customer_by_phone


@tool
def get_customer(customer_id: str | None = None, phone: str | None = None) -> str:
    """Cari customer berdasarkan customer_id atau phone number."""
    if customer_id:
        customer = get_customer_by_id(customer_id)
    elif phone:
        customer = get_customer_by_phone(phone)
    else:
        return "Error: Mohon berikan customer_id atau phone number"

    if not customer:
        return "Customer tidak ditemukan"

    return f"Customer: {customer['name']} (ID: {customer['id']}), Tier: {customer['tier']}, Phone: {customer.get('phone', 'N/A')}"
