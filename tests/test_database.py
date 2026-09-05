import tempfile
import os
import pytest


@pytest.fixture(autouse=True)
def temp_db():
    from src.config.settings import settings
    from src.data.database import init_db
    from src.data.schema import set_db_path

    old_path = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    settings.DATABASE_PATH = temp_path
    set_db_path(None)
    init_db()
    yield
    settings.DATABASE_PATH = old_path
    set_db_path(None)
    os.unlink(temp_path)


def _insert_message(session_id, role, content, timestamp):
    from src.data.database import get_connection
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, timestamp),
        )
        conn.commit()


class TestDatabaseCRUD:
    def test_create_and_get_session(self):
        from src.data.database import create_session, get_session
        session = create_session("test-123", "Test Customer")
        assert session["id"] == "test-123"
        assert session["customer_name"] == "Test Customer"
        assert session["status"] == "active"

        retrieved = get_session("test-123")
        assert retrieved is not None
        assert retrieved["id"] == "test-123"

    def test_get_nonexistent_session(self):
        from src.data.database import get_session
        result = get_session("nonexistent")
        assert result is None

    def test_create_quote(self):
        from src.data.database import create_quote
        result = create_quote("Q-001", "session-1", "[]", 100000.0, "2026-12-31")
        assert result["id"] == "Q-001"
        assert result["total_price"] == 100000.0
        assert result["status"] == "pending"


class TestCustomerOperations:
    def test_create_customer(self):
        from src.data.database import create_customer, get_customer_by_id
        customer = create_customer(name="Toko Budi", phone="08123456789")
        assert customer["id"].startswith("CUST-")
        assert customer["name"] == "Toko Budi"
        assert customer["tier"] == "regular"
        fetched = get_customer_by_id(customer["id"])
        assert fetched is not None
        assert fetched["name"] == "Toko Budi"

    def test_get_customer_by_phone(self):
        from src.data.database import create_customer, get_customer_by_phone
        create_customer(name="Toko Jaya", phone="08999999999")
        found = get_customer_by_phone("08999999999")
        assert found is not None
        assert found["name"] == "Toko Jaya"

    def test_get_customer_not_found(self):
        from src.data.database import get_customer_by_id
        assert get_customer_by_id("CUST-NONEXISTENT") is None


class TestOrderOperations:
    def test_create_order(self):
        from src.data.database import create_customer, create_order, get_order_by_id
        customer = create_customer(name="Toko Test")
        items = [{"product_id": 1, "product_name": "Polo Navy", "qty": 100, "price_per_unit": 70000, "subtotal": 7000000}]
        order = create_order(customer_id=customer["id"], items=items, subtotal=7000000, discount_amount=0, total_price=7000000)
        assert order["id"].startswith("ORD-")
        assert order["status"] == "pending"
        fetched = get_order_by_id(order["id"])
        assert fetched is not None
        assert len(fetched["items"]) == 1

    def test_update_order_status(self):
        from src.data.database import create_customer, create_order, update_order_status, get_order_by_id
        customer = create_customer(name="Toko Status")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        order = create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        assert update_order_status(order["id"], "confirmed") is True
        assert get_order_by_id(order["id"])["status"] == "confirmed"

    def test_update_order_status_invalid_transition(self):
        from src.data.database import create_customer, create_order, update_order_status
        customer = create_customer(name="Toko Invalid")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        order = create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        assert update_order_status(order["id"], "shipped") is False

    def test_get_orders_by_customer(self):
        from src.data.database import create_customer, create_order, get_orders_by_customer
        customer = create_customer(name="Toko Multi")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}]
        create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        create_order(customer_id=customer["id"], items=items, subtotal=3500000, discount_amount=0, total_price=3500000)
        orders = get_orders_by_customer(customer["id"])
        assert len(orders) == 2
