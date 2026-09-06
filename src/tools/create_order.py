import json
from langchain_core.tools import tool


@tool
def create_order(customer_id: str, items_json: str, shipping_address: str | None = None, notes: str | None = None) -> dict:
    """Siapkan order baru untuk konfirmasi. items_json adalah JSON array dengan format: [{"product_id": int, "product_name": str, "qty": int, "price_per_unit": int}]. Shipping address dan notes opsional. Order akan dibuat setelah customer konfirmasi YA."""
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        return {"error": "items_json format tidak valid"}

    if not items:
        return {"error": "Tidak ada items dalam order"}

    subtotal = 0
    formatted_items = []
    for item in items:
        if "product_id" not in item or "qty" not in item or "price_per_unit" not in item:
            return {"error": "Item harus memiliki product_id, qty, dan price_per_unit"}
        item_subtotal = item["qty"] * item["price_per_unit"]
        item["subtotal"] = item_subtotal
        subtotal += item_subtotal
        formatted_items.append({
            "product_id": item["product_id"],
            "product_name": item.get("product_name", "Produk"),
            "qty": item["qty"],
            "price_per_unit": item["price_per_unit"],
            "subtotal": item_subtotal,
        })

    order_data = {
        "customer_id": customer_id,
        "items": formatted_items,
        "subtotal": subtotal,
        "total_price": subtotal,
        "shipping_address": shipping_address,
        "notes": notes,
        "pending_confirmation": True,
    }

    return {
        "type": "order_summary",
        "data": {
            "order_id": "PENDING",
            "items": formatted_items,
            "subtotal": subtotal,
            "total_price": subtotal,
            "status": "pending",
            "customer_name": customer_id,
        },
        "ORDER_PENDING": json.dumps(order_data),
    }
