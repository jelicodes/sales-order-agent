### Task 12: Fix discount min_qty validation

**Files:**
- Modify: `src/tools/calculate_price.py`
- Modify: `tests/test_tools.py`
- Modify: `tests/test_tools_extended.py`

**Interfaces:**
- Consumes: existing `get_discount()` function
- Produces: discount validation with min_qty check

- [ ] **Step 1: Update calculate_price.py with min_qty validation**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


class CalculatePriceInput(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
    if quantity <= 0:
        return {
            "product_id": product_id, "quantity": quantity,
            "price_per_unit": 0, "subtotal": 0,
            "discount": None, "discount_amount": 0,
            "total": 0, "tier": "N/A"
        }
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
            # Validate min_qty requirement
            if discount.get("min_qty") and quantity < discount["min_qty"]:
                discount = None  # Don't apply discount if min_qty not met
            else:
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

- [ ] **Step 2: Update test in test_tools.py to reflect new behavior**

Find and update the test `test_discount_min_qty_not_met`:

```python
def test_discount_min_qty_not_met(self):
    """Discount with quantity below minimum should not apply."""
    result = calculate_price.invoke({"product_id": 1, "quantity": 50, "discount_code": "BULK500"})
    # BULK500 requires min_qty 500, so discount should NOT apply
    assert result["discount"] is None
    assert result["discount_amount"] == 0
```

- [ ] **Step 3: Update test in test_tools_extended.py to reflect new behavior**

Find and update the test `test_discount_min_qty_not_enforced`:

```python
def test_discount_min_qty_validates_correctly(self):
    """Discount with quantity below minimum should not apply."""
    result = calculate_price.invoke({
        "product_id": 1,
        "quantity": 50,
        "discount_code": "BULK500"
    })
    # BULK500 has min_qty 500, so discount should NOT apply for qty 50
    assert result["discount"] is None
    assert result["discount_amount"] == 0
```

- [ ] **Step 4: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_tools_extended.py -v`

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/tools/calculate_price.py tests/test_tools.py tests/test_tools_extended.py
git commit -m "fix: validate discount min_qty before applying"
```
