from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.database import search_products as db_search


@tool
def search_products(query: str, category: str = "") -> list[dict]:
    """Cari produk fashion grosir berdasarkan query. Gunakan untuk mencari produk berdasarkan nama, kategori, atau deskripsi."""
    if query and query.strip():
        results = search_products_semantic(query, n_results=5)
        if results:
            return results
    return db_search(query if query else "", category if category else None)
