from langchain_core.tools import tool
from src.data.database import get_orders_by_customer


@tool
def get_order_history(customer_id: str, limit: int = 5) -> str:
    """Lihat riwayat order customer. Default menampilkan 5 order terakhir."""
    orders = get_orders_by_customer(customer_id, limit)
    if not orders:
        return f"Tidak ada riwayat order untuk customer {customer_id}"

    result = [f"Riwayat order {customer_id}:"]
    for order in orders:
        result.append(f"- {order['id']}: Status={order['status']}, Total=Rp {order['total_price']:,}, Date={order['created_at'][:10]}")
    return "\n".join(result)
