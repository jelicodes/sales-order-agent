import pytest
import tempfile
import os


@pytest.fixture(autouse=True)
def temp_db():
    from src.config.settings import settings
    old_path = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    settings.DATABASE_PATH = temp_path
    import src.data.database as db_module
    db_module._db_path = None
    from src.data.database import init_db
    init_db()
    yield
    settings.DATABASE_PATH = old_path
    db_module._db_path = None
    os.unlink(temp_path)


class TestCreateOrderTool:
    def test_create_order_success(self):
        from src.data.database import create_customer
        from src.tools.create_order import create_order
        customer = create_customer(name="Toko Test")
        items = '[{"product_id": 1, "product_name": "Polo Navy", "qty": 100, "price_per_unit": 70000}]'
        result = create_order.invoke({"customer_id": customer["id"], "items_json": items})
        assert "berhasil" in result
        assert "ORD-" in result

    def test_create_order_invalid_json(self):
        from src.tools.create_order import create_order
        result = create_order.invoke({"customer_id": "CUST-XXX", "items_json": "invalid"})
        assert "Error" in result

    def test_create_order_empty_items(self):
        from src.tools.create_order import create_order
        result = create_order.invoke({"customer_id": "CUST-XXX", "items_json": "[]"})
        assert "Error" in result


class TestCancelOrderTool:
    def test_cancel_order_success(self):
        from src.data.database import create_customer, create_order as db_create_order
        from src.tools.cancel_order import cancel_order
        customer = create_customer(name="Toko Cancel")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        order = db_create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        result = cancel_order.invoke({"order_id": order["id"]})
        assert "berhasil" in result

    def test_cancel_order_not_found(self):
        from src.tools.cancel_order import cancel_order
        result = cancel_order.invoke({"order_id": "ORD-NONEXISTENT"})
        assert "Error" in result


class TestGetCustomerTool:
    def test_get_customer_by_id(self):
        from src.data.database import create_customer
        from src.tools.get_customer import get_customer
        customer = create_customer(name="Toko Budi", phone="08123456789")
        result = get_customer.invoke({"customer_id": customer["id"]})
        assert "Toko Budi" in result

    def test_get_customer_by_phone(self):
        from src.data.database import create_customer
        from src.tools.get_customer import get_customer
        create_customer(name="Toko Jaya", phone="08999999999")
        result = get_customer.invoke({"phone": "08999999999"})
        assert "Toko Jaya" in result

    def test_get_customer_not_found(self):
        from src.tools.get_customer import get_customer
        result = get_customer.invoke({"customer_id": "CUST-NONEXISTENT"})
        assert "tidak ditemukan" in result


class TestCheckOrderStatusTool:
    def test_check_order_status_success(self):
        from src.data.database import create_customer, create_order as db_create_order
        from src.tools.check_order_status import check_order_status
        customer = create_customer(name="Toko Status")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        order = db_create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        result = check_order_status.invoke({"order_id": order["id"]})
        assert "pending" in result

    def test_check_order_status_not_found(self):
        from src.tools.check_order_status import check_order_status
        result = check_order_status.invoke({"order_id": "ORD-NONEXISTENT"})
        assert "tidak ditemukan" in result


class TestGetOrderHistoryTool:
    def test_get_order_history_with_orders(self):
        from src.data.database import create_customer, create_order as db_create_order
        from src.tools.get_order_history import get_order_history
        customer = create_customer(name="Toko History")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        db_create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        result = get_order_history.invoke({"customer_id": customer["id"]})
        assert "Riwayat order" in result

    def test_get_order_history_empty(self):
        from src.tools.get_order_history import get_order_history
        result = get_order_history.invoke({"customer_id": "CUST-NONEXISTENT"})
        assert "Tidak ada riwayat" in result
