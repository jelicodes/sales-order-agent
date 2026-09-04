import json
from langchain_core.tools import tool
from src.data.database import create_order as db_create_order


@tool
def create_order(customer_id: str, items_json: str, shipping_address: str | None = None, notes: str | None = None) -> str:
    """Buat order baru. items_json adalah JSON array dengan format: [{"product_id": int, "product_name": str, "qty": int, "price_per_unit": int}]. Shipping address dan notes opsional."""
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        return "Error: items_json format tidak valid"

    if not items:
        return "Error: Tidak ada items dalam order"

    subtotal = 0
    for item in items:
        if "product_id" not in item or "qty" not in item or "price_per_unit" not in item:
            return "Error: Item harus memiliki product_id, qty, dan price_per_unit"
        item["subtotal"] = item["qty"] * item["price_per_unit"]
        subtotal += item["subtotal"]

    order = db_create_order(
        customer_id=customer_id,
        items=items,
        subtotal=subtotal,
        discount_amount=0,
        total_price=subtotal,
        shipping_address=shipping_address,
        notes=notes,
    )
    return f"Order berhasil dibuat! Order ID: {order['id']}, Total: Rp {order['total_price']:,}, Status: {order['status']}"
