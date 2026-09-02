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
        result = get_product_detail.invoke({"product_id": 1})
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
