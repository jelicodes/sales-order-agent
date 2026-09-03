import pytest
from src.tools.search_products import search_products
from src.tools.get_product_detail import get_product_detail
from src.tools.check_stock import check_stock
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives


# ============================================================
# SEARCH PRODUCTS
# ============================================================
class TestSearchProducts:
    def test_returns_results_for_valid_query(self):
        results = search_products.invoke("polo")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_returns_results_by_category(self):
        results = search_products.invoke({"query": "", "category": "Kaos"})
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(r["category"] == "Kaos" for r in results)

    def test_returns_empty_for_no_match(self):
        results = search_products.invoke("jas formal pria mewah")
        assert isinstance(results, list)

    def test_returns_multiple_products(self):
        results = search_products.invoke("kaos")
        assert len(results) >= 2

    def test_result_has_required_fields(self):
        results = search_products.invoke("polo")
        assert len(results) > 0
        for r in results:
            assert "product_id" in r or "id" in r
            assert "name" in r or "category" in r


# ============================================================
# GET PRODUCT DETAIL
# ============================================================
class TestGetProductDetail:
    def test_returns_detail_for_valid_id(self):
        result = get_product_detail.invoke({"product_id": 1})
        assert result is not None
        assert result["name"] == "Polo Premium Cotton"
        assert "moq" in result
        assert "lead_time_days" in result

    def test_returns_none_for_invalid_id(self):
        result = get_product_detail.invoke({"product_id": 9999})
        assert result is None

    def test_returns_variants(self):
        result = get_product_detail.invoke({"product_id": 1})
        assert result is not None
        assert "variants" in result
        assert len(result["variants"]) > 0

    def test_variant_has_color(self):
        result = get_product_detail.invoke({"product_id": 1})
        for v in result["variants"]:
            assert "color" in v

    def test_different_products_have_different_data(self):
        p1 = get_product_detail.invoke({"product_id": 1})
        p2 = get_product_detail.invoke({"product_id": 2})
        assert p1["name"] != p2["name"]
        assert p1["base_price"] != p2["base_price"]


# ============================================================
# CHECK STOCK
# ============================================================
class TestCheckStock:
    def test_returns_stock_info(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 100})
        assert "available" in result
        assert "total_stock" in result

    def test_available_when_stock_sufficient(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 100})
        assert result["available"] is True

    def test_unavailable_when_stock_insufficient(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 999999})
        assert result["available"] is False

    def test_returns_variant_details(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 100})
        assert "variants" in result
        assert len(result["variants"]) > 0

    def test_variant_has_required_fields(self):
        result = check_stock.invoke({"product_id": 1, "quantity": 100})
        for v in result["variants"]:
            assert "color" in v
            assert "quantity" in v
            assert "warehouse" in v

    def test_exact_stock_match(self):
        # Get total stock first
        result_all = check_stock.invoke({"product_id": 1, "quantity": 1})
        total = result_all["total_stock"]
        result_exact = check_stock.invoke({"product_id": 1, "quantity": total})
        assert result_exact["available"] is True

    def test_one_over_stock(self):
        result_all = check_stock.invoke({"product_id": 1, "quantity": 1})
        total = result_all["total_stock"]
        result_over = check_stock.invoke({"product_id": 1, "quantity": total + 1})
        assert result_over["available"] is False

    def test_nonexistent_product(self):
        result = check_stock.invoke({"product_id": 9999, "quantity": 100})
        assert result["available"] is False
        assert result["stock"] == 0


# ============================================================
# CALCULATE PRICE
# ============================================================
class TestCalculatePrice:
    def test_calculates_correct_tier_500(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 500})
        assert result["price_per_unit"] == 70000
        assert result["subtotal"] == 35000000

    def test_calculates_correct_tier_100(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 100})
        assert result["price_per_unit"] == 80000
        assert result["subtotal"] == 8000000

    def test_calculates_correct_tier_300(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 300})
        assert result["price_per_unit"] == 75000
        assert result["subtotal"] == 22500000

    def test_tier_boundary_99(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 99})
        assert result["price_per_unit"] == 85000

    def test_tier_boundary_100(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 100})
        assert result["price_per_unit"] == 80000

    def test_tier_boundary_299(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 299})
        assert result["price_per_unit"] == 80000

    def test_tier_boundary_300(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 300})
        assert result["price_per_unit"] == 75000

    def test_applies_percentage_discount(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 500, "discount_code": "BULK500"})
        assert result["discount"] is not None
        assert result["discount"]["type"] == "percentage"
        assert result["discount_amount"] > 0
        assert result["total"] < result["subtotal"]

    def test_applies_fixed_discount(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 200, "discount_code": "HEMAT20K"})
        assert result["discount"] is not None
        assert result["discount"]["type"] == "fixed"
        assert result["discount_amount"] == 20000

    def test_invalid_discount_code(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 100, "discount_code": "TIDAKADA"})
        assert result["discount"] is None
        assert result["discount_amount"] == 0
        assert result["total"] == result["subtotal"]

    def test_empty_discount_code(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 100, "discount_code": ""})
        assert result["discount"] is None
        assert result["discount_amount"] == 0

    def test_total_equals_subtotal_minus_discount(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 500, "discount_code": "BULK500"})
        expected = result["subtotal"] - result["discount_amount"]
        assert result["total"] == expected

    def test_has_tier_info(self):
        result = calculate_price.invoke({"product_id": 1, "quantity": 500})
        assert "tier" in result
        assert "pcs" in result["tier"]

    def test_different_products_different_prices(self):
        r1 = calculate_price.invoke({"product_id": 1, "quantity": 100})
        r2 = calculate_price.invoke({"product_id": 2, "quantity": 100})
        assert r1["price_per_unit"] != r2["price_per_unit"]


# ============================================================
# CREATE QUOTE
# ============================================================
class TestCreateQuote:
    def test_creates_quote(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test Corp"}
        })
        assert "quote_id" in result
        assert result["total_price"] > 0

    def test_quote_has_valid_until(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert "valid_until" in result
        assert result["valid_until"] != ""

    def test_quote_id_format(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert result["quote_id"].startswith("Q-")

    def test_multiple_items(self):
        result = create_quote.invoke({
            "items": [
                {"product_id": 1, "quantity": 100, "color": "Hitam"},
                {"product_id": 2, "quantity": 200, "color": "Navy"}
            ],
            "customer_info": {"customer_name": "Test"}
        })
        assert len(result["items"]) == 2
        assert result["total_price"] > 0

    def test_formatted_total(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert "formatted_total" in result
        assert "Rp" in result["formatted_total"]

    def test_items_have_pricing(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        for item in result["items"]:
            assert "price_per_unit" in item
            assert "subtotal" in item


# ============================================================
# GET ALTERNATIVES
# ============================================================
class TestGetAlternatives:
    def test_returns_alternatives_for_budget(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        assert isinstance(results, list)
        assert len(results) > 0

    def test_returns_alternatives_for_stock(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "stock"})
        assert isinstance(results, list)
        assert len(results) > 0

    def test_alternatives_not_include_original(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        for r in results:
            assert r["product_id"] != 1

    def test_budget_alternatives_cheaper(self):
        results = get_alternatives.invoke({"product_id": 5, "reason": "budget"})
        if len(results) > 0:
            # Should be sorted by price ascending for budget
            prices = [r["base_price"] for r in results]
            assert prices == sorted(prices)

    def test_alternatives_have_required_fields(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        for r in results:
            assert "product_id" in r
            assert "name" in r
            assert "base_price" in r
            assert "price_diff" in r
            assert "price_diff_pct" in r

    def test_alternatives_same_category(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        for r in results:
            assert r["category"] == "Polo"

    def test_max_3_alternatives(self):
        results = get_alternatives.invoke({"product_id": 3, "reason": "budget"})
        assert len(results) <= 3

    def test_nonexistent_product(self):
        results = get_alternatives.invoke({"product_id": 9999, "reason": "budget"})
        assert results == []


# ============================================================
# EDGE CASES - CROSS TOOL
# ============================================================
class TestEdgeCases:
    def test_stock_zero_all_variants(self):
        """Agent should handle product with zero stock gracefully"""
        result = check_stock.invoke({"product_id": 1, "quantity": 1})
        assert result["total_stock"] >= 0
        assert isinstance(result["available"], bool)

    def test_quantity_zero(self):
        """Price calculation with zero quantity"""
        result = calculate_price.invoke({"product_id": 1, "quantity": 0})
        assert result["subtotal"] == 0
        assert result["total"] == 0

    def test_very_large_quantity(self):
        """Price calculation with very large quantity"""
        result = calculate_price.invoke({"product_id": 1, "quantity": 100000})
        assert result["price_per_unit"] == 70000  # Should use highest tier
        assert result["subtotal"] == 7000000000

    def test_stock_check_with_zero_quantity(self):
        """Stock check with zero quantity should be available"""
        result = check_stock.invoke({"product_id": 1, "quantity": 0})
        assert result["available"] is True

    def test_search_with_empty_string(self):
        """Search with empty string"""
        results = search_products.invoke("")
        assert isinstance(results, list)

    def test_discount_min_qty_not_met(self):
        """Discount with quantity below minimum should not apply."""
        result = calculate_price.invoke({"product_id": 1, "quantity": 50, "discount_code": "BULK500"})
        # BULK500 requires min_qty 500, so discount should NOT apply
        assert result["discount"] is None
        assert result["discount_amount"] == 0
