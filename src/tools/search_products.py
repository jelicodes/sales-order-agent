from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class SearchProductsInput(BaseModel):
    query: str = Field(description="Kata kunci pencarian produk")
    category: str = Field(default="", description="Filter kategori (contoh: 'Kemeja', 'Hoodie')")


def _format_product_card(product: dict) -> dict:
    """Convert product dict to structured card format."""
    return {
        "type": "product_card",
        "product_id": product.get("id") or product.get("product_id"),
        "name": product.get("name", ""),
        "category": product.get("category", ""),
        "price": int(product.get("base_price", 0)),
        "moq": product.get("moq", 1),
        "stock": product.get("stock", 0),
        "image_url": product.get("image_url", ""),
        "description": product.get("description", ""),
    }


@tool(args_schema=SearchProductsInput)
def search_products(query: str, category: str = "") -> dict:
    """Cari produk fashion grosir berdasarkan query. Menghasilkan product cards."""
    results = []
    if query and query.strip():
        results = search_products_semantic(query, n_results=5)
    if not results:
        results = _product_repo.search(query if query else "", category if category else None)

    if isinstance(results, dict) and "error" in results:
        return results

    # Enrich semantic results with full product data from repo
    enriched = []
    for item in results:
        product_id = item.get("product_id") or item.get("id")
        if product_id is not None:
            full_product = _product_repo.get_by_id(product_id)
            if full_product:
                enriched.append(full_product)
            else:
                enriched.append(item)
        else:
            enriched.append(item)

    cards = [_format_product_card(p) for p in enriched] if enriched else []
    return {"type": "product_cards", "data": cards}
