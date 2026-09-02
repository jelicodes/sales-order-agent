# Task 4: Agent Tools (6 Tools)

## Files to Create
- `src/tools/__init__.py`
- `src/tools/search_products.py`
- `src/tools/get_product_detail.py`
- `src/tools/check_stock.py`
- `src/tools/calculate_price.py`
- `src/tools/create_quote.py`
- `src/tools/get_alternatives.py`
- `tests/test_tools.py`

## Prerequisites
- Task 3 completed: `src/data/database.py` and `src/data/vector_store.py` exist

## What to Do

Create 6 LangChain `@tool` decorated functions. Each tool calls database functions from `src/data/database.py` and/or `src/data/vector_store.py`.

### Tool 1: search_products (src/tools/search_products.py)

```python
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.database import search_products as db_search

@tool
def search_products(query: str, category: str = "") -> list[dict]:
    """Cari produk fashion grosir berdasarkan query. Gunakan untuk mencari produk berdasarkan nama, kategori, atau deskripsi."""
    results = search_products_semantic(query, n_results=5)
    if results:
        return results
    return db_search(query, category if category else None)
```

### Tool 2: get_product_detail (src/tools/get_product_detail.py)

```python
from langchain_core.tools import tool
from src.data.database import get_product_by_id, get_product_variants

@tool
def get_product_detail(product_id: int) -> dict | None:
    """Ambil spesifikasi lengkap produk berdasarkan product_id."""
    product = get_product_by_id(product_id)
    if not product:
        return None
    variants = get_product_variants(product_id)
    product["variants"] = [{"id": v["id"], "color": v["color"]} for v in variants]
    return product
```

### Tool 3: check_stock (src/tools/check_stock.py)

```python
from langchain_core.tools import tool
from src.data.database import get_stock_by_product

@tool
def check_stock(product_id: int, quantity: int) -> dict:
    """Cek ketersediaan stok produk. Masukkan product_id dan jumlah yang dibutuhkan."""
    variants = get_stock_by_product(product_id)
    if not variants:
        return {"available": False, "stock": 0, "message": "Produk tidak ditemukan"}
    total_stock = sum(v["quantity"] for v in variants)
    available = total_stock >= quantity
    return {
        "available": available,
        "total_stock": total_stock,
        "variants": [{"color": v["color"], "quantity": v["quantity"], "warehouse": v["warehouse_location"]} for v in variants],
        "message": f"Stok mencukupi ({total_stock} tersedia)" if available else f"Stok tidak cukup. Tersedia: {total_stock}, dibutuhkan: {quantity}"
    }
```

### Tool 4: calculate_price (src/tools/calculate_price.py)

```python
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount

@tool
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
    tier = get_price_tier(product_id, quantity)
    if not tier:
        return {"error": "Tidak ada harga tersedia untuk quantity ini"}
    price_per_unit = tier["price_per_unit"]
    subtotal = price_per_unit * quantity
    discount_amount = 0
    discount_info = None
    if discount_code:
        discount = get_discount(discount_code)
        if discount:
            if discount["type"] == "percentage":
                discount_amount = subtotal * (discount["value"] / 100)
            else:
                discount_amount = min(discount["value"], subtotal)
            discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}
    total = subtotal - discount_amount
    return {
        "product_id": product_id, "quantity": quantity,
        "price_per_unit": price_per_unit, "subtotal": subtotal,
        "discount": discount_info, "discount_amount": discount_amount,
        "total": total, "tier": f"{tier['min_qty']}-{tier['max_qty'] or '∞'} pcs"
    }
```

### Tool 5: create_quote (src/tools/create_quote.py)

```python
import json
from datetime import datetime, timedelta
from langchain_core.tools import tool
from src.data.database import create_quote as db_create_quote, get_price_tier

@tool
def create_quote(items: list[dict], customer_info: dict) -> dict:
    """Buat penawaran harga final. Masukkan list item [{product_id, quantity, color}] dan customer_info."""
    quote_items = []
    total_price = 0
    for item in items:
        tier = get_price_tier(item["product_id"], item["quantity"])
        if tier:
            item_total = tier["price_per_unit"] * item["quantity"]
            quote_items.append({**item, "price_per_unit": tier["price_per_unit"], "subtotal": item_total})
            total_price += item_total
    quote_id = f"Q-{datetime.now().strftime('%Y-%m-%d')}-{datetime.now().strftime('%H%M%S')}"
    valid_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    result = db_create_quote(quote_id=quote_id, session_id="", items_json=json.dumps(quote_items), total_price=total_price, valid_until=valid_until)
    return {
        "quote_id": quote_id, "items": quote_items, "total_price": total_price,
        "formatted_total": f"Rp {total_price:,.0f}".replace(",", "."),
        "valid_until": valid_until, "customer_info": customer_info,
    }
```

### Tool 6: get_alternatives (src/tools/get_alternatives.py)

```python
from langchain_core.tools import tool
from src.data.database import get_product_by_id, search_products

@tool
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
```

### Tests (tests/test_tools.py)

Write tests for all 6 tools. Use the database fixtures from Task 3 (products should be seeded in test DB).

```python
import pytest
from src.tools.search_products import search_products
from src.tools.get_product_detail import get_product_detail
from src.tools.check_stock import check_stock
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives

class TestSearchProducts:
    def test_returns_results_for_valid_query(self):
        results = search_products.invoke("polo")
        assert isinstance(results, list)
        assert len(results) > 0

class TestGetProductDetail:
    def test_returns_detail_for_valid_id(self):
        result = get_product_detail.invoke(1)
        assert result is not None
        assert "name" in result

class TestCheckStock:
    def test_returns_stock_info(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 100})
        assert "available" in result

class TestCalculatePrice:
    def test_calculates_correct_tier(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 500})
        assert result["price_per_unit"] == 70000

class TestCreateQuote:
    def test_creates_quote(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert "quote_id" in result

class TestGetAlternatives:
    def test_returns_alternatives(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        assert isinstance(results, list)
```

## Verification
1. Seed the database first: `D:\Jeli\myenv\Scripts\python.exe -m src.data.seed.seed`
2. Run tests: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py -v`

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-4-report.md`
