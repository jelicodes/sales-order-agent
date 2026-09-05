from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class SearchProductsInput(BaseModel):
    query: str = Field(description="Kata kunci pencarian produk")
    category: str = Field(default="", description="Filter kategori (contoh: 'Kemeja', 'Hoodie')")


@tool(args_schema=SearchProductsInput)
def search_products(query: str, category: str = "") -> list[dict]:
    """Cari produk fashion grosir berdasarkan query. Gunakan untuk mencari produk berdasarkan nama, kategori, atau deskripsi."""
    if query and query.strip():
        results = search_products_semantic(query, n_results=5)
        if results:
            return results
    return _product_repo.search(query if query else "", category if category else None)
