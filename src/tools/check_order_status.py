from langchain_core.tools import tool
from src.data.repos.order_repo import OrderRepo

_order_repo = OrderRepo()


@tool
def check_order_status(order_id: str) -> str:
    """Cek status order berdasarkan order_id."""
    order = _order_repo.get_by_id(order_id)
    if not order:
        return f"Order {order_id} tidak ditemukan"

    items_summary = ", ".join([f"{item['product_name']} ({item['qty']} pcs)" for item in order.get("items", [])])
    return f"Order {order['id']}: Status={order['status']}, Items=[{items_summary}], Total=Rp {order['total_price']:,}, Payment={order['payment_status']}"
