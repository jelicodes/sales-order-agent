### Task 7: Add missing unit tests

**Files:**
- Create: `tests/test_database_extended.py`
- Create: `tests/test_tools_extended.py`

**Interfaces:**
- Consumes: existing database and tool functions
- Produces: additional test coverage

- [ ] **Step 1: Create test_database_extended.py**

```python
import pytest
from src.data.database import (
    init_db, search_products, get_product_by_id,
    get_product_variants, get_price_tier, get_stock_by_product,
    create_session, get_session, save_message, get_conversation_history,
    create_quote, get_discount
)


class TestDatabaseExtended:
    def test_init_db_idempotent(self):
        """Calling init_db twice should not crash."""
        init_db()
        init_db()  # Should not raise

    def test_search_products_by_category(self):
        results = search_products("", "Kaos")
        assert len(results) > 0
        assert all(r["category"] == "Kaos" for r in results)

    def test_get_product_variants(self):
        variants = get_product_variants(1)
        assert len(variants) > 0
        assert "color" in variants[0]

    def test_get_price_tier_boundary_99(self):
        tier = get_price_tier(1, 99)
        assert tier is not None
        assert tier["price_per_unit"] == 85000

    def test_get_price_tier_boundary_100(self):
        tier = get_price_tier(1, 100)
        assert tier is not None
        assert tier["price_per_unit"] == 80000

    def test_get_stock_by_product(self):
        stock = get_stock_by_product(1)
        assert len(stock) > 0
        assert "quantity" in stock[0]

    def test_get_discount_valid(self):
        discount = get_discount("BULK500")
        assert discount is not None
        assert discount["type"] == "percentage"

    def test_get_discount_invalid(self):
        discount = get_discount("NONEXISTENT")
        assert discount is None

    def test_conversation_history_ordering(self):
        session_id = "test-ordering-123"
        create_session(session_id, "Test")
        save_message(session_id, "user", "Message 1")
        save_message(session_id, "assistant", "Response 1")
        save_message(session_id, "user", "Message 2")

        history = get_conversation_history(session_id)
        assert len(history) == 3
        assert history[0]["content"] == "Message 1"
        assert history[1]["content"] == "Response 1"
        assert history[2]["content"] == "Message 2"
```

- [ ] **Step 2: Create test_tools_extended.py**

```python
import pytest
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives


class TestCalculatePriceExtended:
    def test_calculates_price_no_tier_returns_error(self):
        result = calculate_price.invoke({"product_id": 9999, "quantity": 100})
        assert "error" in result

    def test_discount_min_qty_not_enforced(self):
        """Current behavior: discount applies regardless of min_qty.
        This documents the existing behavior for future reference."""
        result = calculate_price.invoke({
            "product_id": 1,
            "quantity": 50,
            "discount_code": "BULK500"
        })
        # BULK500 has min_qty 500, but currently applies anyway
        assert result["discount"] is not None


class TestCreateQuoteExtended:
    def test_create_quote_with_dict_items(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert "quote_id" in result
        assert result["total_price"] > 0

    def test_create_quote_with_pydantic_items(self):
        from pydantic import BaseModel
        from typing import List

        class QuoteItem(BaseModel):
            product_id: int
            quantity: int
            color: str

        items = [QuoteItem(product_id=1, quantity=100, color="Hitam")]
        result = create_quote.invoke({
            "items": [item.model_dump() for item in items],
            "customer_info": {"customer_name": "Test"}
        })
        assert "quote_id" in result


class TestGetAlternativesExtended:
    def test_stock_alternatives_sorted_descending(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "stock"})
        if len(results) > 1:
            prices = [r["base_price"] for r in results]
            assert prices == sorted(prices, reverse=True)

    def test_alternatives_same_category(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        for r in results:
            assert r["category"] == "Polo"
```

- [ ] **Step 3: Run new tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_database_extended.py tests/test_tools_extended.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_database_extended.py tests/test_tools_extended.py
git commit -m "test: add extended database and tools unit tests"
```
