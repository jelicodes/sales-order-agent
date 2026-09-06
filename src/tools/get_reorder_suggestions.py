from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.repos.order_repo import OrderRepo
from src.data.repos.product_repo import ProductRepo

_order_repo = OrderRepo()
_product_repo = ProductRepo()


class GetReorderSuggestionsInput(BaseModel):
    customer_id: str = Field(description="ID customer yang ingin lihat saran reorder")


@tool(args_schema=GetReorderSuggestionsInput)
def get_reorder_suggestions(customer_id: str) -> dict:
    """Saran produk untuk reorder berdasarkan riwayat pembelian customer."""
    items = _order_repo.get_items_by_customer(customer_id, limit=5)

    if not items:
        return {
            "type": "reorder_suggestions",
            "data": [],
            "message": f"Tidak ada riwayat pembelian untuk customer {customer_id}",
        }

    seen = set()
    suggestions = []
    for item in items:
        pid = item["product_id"]
        if pid in seen:
            continue
        seen.add(pid)

        product = _product_repo.get_by_id(pid)
        suggestions.append({
            "product_id": pid,
            "product_name": item["product_name"],
            "last_qty": item["qty"],
            "last_price": item["price_per_unit"],
            "last_order_date": item["last_order_date"][:10] if item.get("last_order_date") else None,
            "image_url": product.get("image_url", "") if product else "",
            "base_price": int(product.get("base_price", 0)) if product else 0,
        })

    return {"type": "reorder_suggestions", "data": suggestions}
