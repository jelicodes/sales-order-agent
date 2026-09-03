from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_product_by_id, search_products


class GetAlternativesInput(BaseModel):
    product_id: int = Field(description="ID produk asal")
    reason: str = Field(description="Alasan cari alternatif: 'stock' (stok tidak cukup) atau 'budget' (budget tidak sesuai)")


@tool(args_schema=GetAlternativesInput)
def get_alternatives(product_id: int, reason: str) -> list[dict]:
    """Cari produk alternatif. reason: 'stock' (stok tidak cukup) atau 'budget' (budget tidak sesuai)."""
    original = get_product_by_id(product_id)
    if not original:
        return []
    category = original["category"]
    base_price = original["base_price"]
    candidates = search_products("", category)
    alternatives = []
    for c in candidates:
        if c["id"] == product_id:
            continue
        price_diff = c["base_price"] - base_price
        price_pct = (price_diff / base_price) * 100 if base_price else 0
        alternatives.append({
            "product_id": c["id"], "name": c["name"], "category": c["category"],
            "base_price": c["base_price"], "price_diff": price_diff,
            "price_diff_pct": f"{price_pct:+.0f}%", "reason": reason,
        })
    if reason == "budget":
        alternatives.sort(key=lambda x: x["base_price"])
    else:
        alternatives.sort(key=lambda x: x["base_price"], reverse=True)
    return alternatives[:3]
