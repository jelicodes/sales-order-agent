import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from src.agents.graph import create_sales_agent
from src.data.database import init_db, create_customer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_order_tool_call(order_data: dict) -> AIMessage:
    """Return AIMessage that triggers create_order tool."""
    items_json = json.dumps(order_data["items"])
    return AIMessage(
        content="",
        tool_calls=[{
            "id": "call_order_001",
            "name": "create_order",
            "args": {
                "customer_id": order_data["customer_id"],
                "items_json": items_json,
                "shipping_address": order_data.get("shipping_address"),
                "notes": order_data.get("notes"),
            },
        }],
    )


def _make_final_response(text: str = "Order sudah dikonfirmasi.") -> AIMessage:
    return AIMessage(content=text)


SAMPLE_ORDER = {
    "customer_id": "CUST-TEST-001",
    "items": [
        {"product_id": 1, "product_name": "Polo Navy", "qty": 100, "price_per_unit": 70000}
    ],
    "subtotal": 7000000,
    "total_price": 7000000,
    "shipping_address": "Jl. Tanah Abang III No. 10",
    "notes": "Seragam karyawan",
}

SAMPLE_MULTI_ITEM_ORDER = {
    "customer_id": "CUST-TEST-002",
    "items": [
        {"product_id": 1, "product_name": "Polo Navy", "qty": 100, "price_per_unit": 70000},
        {"product_id": 2, "product_name": "Kaos Putih", "qty": 200, "price_per_unit": 45000},
    ],
    "subtotal": 16000000,
    "total_price": 16000000,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_db():
    """Each test gets a fresh temp database."""
    import tempfile, os
    from src.config.settings import settings
    from src.data.schema import set_db_path

    old = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp = f.name
    settings.DATABASE_PATH = tmp
    set_db_path(None)
    init_db()
    yield
    settings.DATABASE_PATH = old
    set_db_path(None)
    os.unlink(tmp)


@pytest.fixture
def checkpointer():
    """In-memory checkpointer for HITL state persistence across invocations."""
    with SqliteSaver.from_conn_string(":memory:") as cp:
        yield cp


# ===================================================================
# TEST SUITE 1: create_order tool unit tests
# ===================================================================

class TestCreateOrderTool:
    """Unit tests for the create_order tool itself."""

    def test_create_order_returns_order_pending(self):
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([
                {"product_id": 1, "product_name": "Polo", "qty": 100, "price_per_unit": 70000}
            ]),
        })
        assert result.startswith("ORDER_PENDING|")
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["customer_id"] == "CUST-001"
        assert data["subtotal"] == 7000000
        assert data["total_price"] == 7000000
        assert data["pending_confirmation"] is True

    def test_create_order_multi_item_subtotal(self):
        from src.tools.create_order import create_order

        items = [
            {"product_id": 1, "product_name": "Polo", "qty": 100, "price_per_unit": 70000},
            {"product_id": 2, "product_name": "Kaos", "qty": 200, "price_per_unit": 45000},
        ]
        result = create_order.invoke({
            "customer_id": "CUST-002",
            "items_json": json.dumps(items),
        })
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["subtotal"] == 7000000 + 9000000
        assert len(data["items"]) == 2

    def test_create_order_empty_items(self):
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": "[]",
        })
        assert "Error" in result
        assert "Tidak ada items" in result

    def test_create_order_invalid_json(self):
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": "not-json",
        })
        assert "Error" in result
        assert "format tidak valid" in result

    def test_create_order_missing_fields(self):
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([{"product_id": 1}]),
        })
        assert "Error" in result
        assert "product_id, qty, dan price_per_unit" in result

    def test_create_order_with_shipping_and_notes(self):
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([
                {"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 80000}
            ]),
            "shipping_address": "Jl. Sudirman No. 1",
            "notes": "Urgent",
        })
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["shipping_address"] == "Jl. Sudirman No. 1"
        assert data["notes"] == "Urgent"


# ===================================================================
# TEST SUITE 2: cancel_order tool unit tests
# ===================================================================

class TestCancelOrderTool:
    """Unit tests for the cancel_order tool."""

    def _create_order_in_db(self):
        from src.data.repos.order_repo import OrderRepo
        repo = OrderRepo()
        customer = create_customer(name="Toko Batal", phone="08111111111")
        order = repo.create_order(
            customer_id=customer["id"],
            items=[{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}],
            subtotal=3500000, discount_amount=0, total_price=3500000,
        )
        return order

    def test_cancel_pending_order(self):
        from src.tools.cancel_order import cancel_order

        order = self._create_order_in_db()
        result = cancel_order.invoke({"order_id": order["id"]})
        assert "berhasil dibatalkan" in result

    def test_cancel_nonexistent_order(self):
        from src.tools.cancel_order import cancel_order

        result = cancel_order.invoke({"order_id": "ORD-NONEXISTENT"})
        assert "tidak bisa dibatalkan" in result

    def test_cancel_processing_order_fails(self):
        from src.tools.cancel_order import cancel_order
        from src.data.repos.order_repo import OrderRepo

        order = self._create_order_in_db()
        repo = OrderRepo()
        repo.update_status(order["id"], "confirmed")
        repo.update_status(order["id"], "processing")

        result = cancel_order.invoke({"order_id": order["id"]})
        assert "tidak bisa dibatalkan" in result


# ===================================================================
# TEST SUITE 3: check_order_status tool unit tests
# ===================================================================

class TestCheckOrderStatusTool:

    def _create_order_in_db(self):
        from src.data.repos.order_repo import OrderRepo
        repo = OrderRepo()
        customer = create_customer(name="Toko Status", phone="08222222222")
        return repo.create_order(
            customer_id=customer["id"],
            items=[{"product_id": 1, "product_name": "Polo", "qty": 100, "price_per_unit": 70000, "subtotal": 7000000}],
            subtotal=7000000, discount_amount=0, total_price=7000000,
        )

    def test_check_existing_order(self):
        from src.tools.check_order_status import check_order_status

        order = self._create_order_in_db()
        result = check_order_status.invoke({"order_id": order["id"]})
        assert order["id"] in result
        assert "pending" in result
        assert "7.000.000" in result.replace(",", ".")

    def test_check_nonexistent_order(self):
        from src.tools.check_order_status import check_order_status

        result = check_order_status.invoke({"order_id": "ORD-FAKE"})
        assert "tidak ditemukan" in result


# ===================================================================
# TEST SUITE 4: get_order_history tool unit tests
# ===================================================================

class TestGetOrderHistoryTool:

    def test_history_with_orders(self):
        from src.tools.get_order_history import get_order_history
        from src.data.repos.order_repo import OrderRepo

        repo = OrderRepo()
        customer = create_customer(name="Toko Riwayat", phone="08333333333")
        repo.create_order(
            customer_id=customer["id"],
            items=[{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}],
            subtotal=3500000, discount_amount=0, total_price=3500000,
        )
        result = get_order_history.invoke({"customer_id": customer["id"]})
        assert customer["id"] in result
        assert "ORD-" in result

    def test_history_empty(self):
        from src.tools.get_order_history import get_order_history

        result = get_order_history.invoke({"customer_id": "CUST-NONE"})
        assert "Tidak ada riwayat" in result


# ===================================================================
# TEST SUITE 5: Full HITL flow — confirm order
# ===================================================================

class TestHITLConfirmFlow:
    """E2E tests for the full HITL order confirmation flow."""

    def test_confirm_order_flow(self, checkpointer):
        """Full flow: LLM calls create_order → interrupt → user YA → order created."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-confirm-001"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # Step 1: LLM calls create_order tool
            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            result1 = agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )

            # Graph should have hit interrupt
            assert "__interrupt__" in result1
            interrupt_data = result1["__interrupt__"][0]
            payload = interrupt_data.value if hasattr(interrupt_data, "value") else interrupt_data
            assert payload["action"] == "create_order"
            assert "Polo Navy" in payload["summary"] or "100" in payload["summary"]

            # Step 2: User confirms with YA
            mock_llm.invoke.return_value = _make_final_response("Order berhasil dibuat.")
            mock_db_create.return_value = {
                "id": "ORD-20260905-TEST",
                "customer_id": "CUST-TEST-001",
                "total_price": 7000000,
                "status": "pending",
            }

            result2 = agent.invoke(Command(resume="YA"), config)

            # db_create_order was called with correct data
            mock_db_create.assert_called_once()
            call_kwargs = mock_db_create.call_args
            assert call_kwargs[1]["customer_id"] == "CUST-TEST-001"
            assert call_kwargs[1]["total_price"] == 7000000
            assert call_kwargs[1]["items"][0]["product_name"] == "Polo Navy"

            # Final response contains confirmation
            msgs = result2.get("messages", [])
            last_msg = msgs[-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            assert "berhasil" in content.lower() or "dikonfirmasi" in content.lower() or "Order" in content

    def test_cancel_order_flow(self, checkpointer):
        """Full flow: LLM calls create_order → interrupt → user BATAL → order cancelled."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-cancel-001"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # Step 1: LLM calls create_order
            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            result1 = agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )
            assert "__interrupt__" in result1

            # Step 2: User cancels with BATAL
            mock_llm.invoke.return_value = _make_final_response("Order dibatalkan.")
            result2 = agent.invoke(Command(resume="BATAL"), config)

            # db_create_order was NOT called
            mock_db_create.assert_not_called()

            # Final message mentions cancellation
            msgs = result2.get("messages", [])
            last_msg = msgs[-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            assert "dibatalkan" in content.lower() or "batal" in content.lower()

    def test_confirm_with_lowercase_ya(self, checkpointer):
        """User types 'ya' (lowercase) — should still confirm."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-lowercase-ya"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )

            mock_llm.invoke.return_value = _make_final_response("OK")
            mock_db_create.return_value = {"id": "ORD-TEST", "status": "pending"}
            agent.invoke(Command(resume="ya"), config)

            mock_db_create.assert_called_once()

    def test_confirm_with_spaces_around_ya(self, checkpointer):
        """User types '  YA  ' — should still confirm after strip."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-spaces-ya"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )

            mock_llm.invoke.return_value = _make_final_response("OK")
            mock_db_create.return_value = {"id": "ORD-TEST", "status": "pending"}
            agent.invoke(Command(resume="  YA  "), config)

            mock_db_create.assert_called_once()

    def test_non_ya_response_cancels(self, checkpointer):
        """User types something other than YA/BATAL — order should be cancelled."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-random-response"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )

            mock_llm.invoke.return_value = _make_final_response("Baik.")
            agent.invoke(Command(resume="tolong dipercepat ya"), config)

            mock_db_create.assert_not_called()


# ===================================================================
# TEST SUITE 6: Multi-item order HITL flow
# ===================================================================

class TestHITLMultiItemOrder:

    def test_multi_item_order_confirm(self, checkpointer):
        """Order with multiple items → interrupt → confirm → all items in DB."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-multi-item"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_MULTI_ITEM_ORDER)
            result1 = agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo + 200 Kaos")]},
                config,
            )
            assert "__interrupt__" in result1

            mock_llm.invoke.return_value = _make_final_response("Multi-item order confirmed.")
            mock_db_create.return_value = {"id": "ORD-MULTI", "status": "pending"}
            agent.invoke(Command(resume="YA"), config)

            call_kwargs = mock_db_create.call_args[1]
            assert len(call_kwargs["items"]) == 2
            assert call_kwargs["total_price"] == 16000000


# ===================================================================
# TEST SUITE 7: Order persistence — DB state after HITL
# ===================================================================

class TestHITLOrderPersistence:
    """Verify order is actually persisted in DB after HITL confirmation."""

    def test_order_appears_in_db_after_confirm(self, checkpointer):
        from src.data.repos.order_repo import OrderRepo

        agent = create_sales_agent(checkpointer=checkpointer)
        session_id = "test-persist-001"
        config = {"configurable": {"thread_id": session_id}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # Create a real customer
            customer = create_customer(name="Toko Persist", phone="08555555555")
            order_data = {
                "customer_id": customer["id"],
                "items": [{"product_id": 1, "product_name": "Polo Navy", "qty": 100, "price_per_unit": 70000}],
                "subtotal": 7000000,
                "total_price": 7000000,
            }

            mock_llm.invoke.return_value = _make_order_tool_call(order_data)
            result1 = agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo")]},
                config,
            )
            assert "__interrupt__" in result1

            mock_llm.invoke.return_value = _make_final_response("Order confirmed.")
            agent.invoke(Command(resume="YA"), config)

            # Verify order exists in DB
            repo = OrderRepo()
            orders = repo.get_by_customer(customer["id"])
            assert len(orders) == 1
            assert orders[0]["status"] == "pending"
            assert orders[0]["total_price"] == 7000000

    def test_order_history_after_creation(self, checkpointer):
        """After HITL confirm, order appears in order history."""
        from src.data.repos.order_repo import OrderRepo
        from src.tools.get_order_history import get_order_history

        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-history-001"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            customer = create_customer(name="Toko History", phone="08666666666")
            order_data = {
                "customer_id": customer["id"],
                "items": [{"product_id": 1, "product_name": "Kaos Putih", "qty": 200, "price_per_unit": 45000}],
                "subtotal": 9000000,
                "total_price": 9000000,
            }

            mock_llm.invoke.return_value = _make_order_tool_call(order_data)
            agent.invoke(
                {"messages": [HumanMessage(content="Order 200 Kaos Putih")]},
                config,
            )

            mock_llm.invoke.return_value = _make_final_response("Done.")
            agent.invoke(Command(resume="YA"), config)

            # Check order history tool
            history = get_order_history.invoke({"customer_id": customer["id"]})
            assert "ORD-" in history
            assert "9.000.000" in history.replace(",", ".")


# ===================================================================
# TEST SUITE 8: HITL via chat endpoint (HTTP)
# ===================================================================

class TestHITLChatEndpoint:
    """E2E tests hitting the /chat HTTP endpoint with HITL flow."""

    def test_chat_interrupt_returns_confirmation_prompt(self):
        """First chat returns interrupt with confirmation message."""
        from fastapi.testclient import TestClient
        from src.main import app

        with TestClient(app) as client:
            sess = client.post("/session", json={"customer_name": "E2E Customer"})
            session_id = sess.json()["session_id"]

            with patch("src.api.chat.create_sales_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.invoke.return_value = {
                    "__interrupt__": [MagicMock(value={
                        "action": "create_order",
                        "summary": "Order Polo Navy - 100 pcs - Total: Rp 7.000.000",
                        "message": "Ketik 'YA' untuk konfirmasi order atau 'BATAL' untuk membatalkan",
                    })],
                }
                mock_create.return_value = mock_agent

                resp = client.post("/chat", json={
                    "message": "Order 100 Polo Navy",
                    "session_id": session_id,
                })
                assert resp.status_code == 200
                data = resp.json()
                assert "konfirmasi" in data["response"].lower() or "order" in data["response"].lower()

    def test_chat_resume_ya_after_interrupt(self):
        """After interrupt, sending YA resumes and creates order."""
        from fastapi.testclient import TestClient
        from src.main import app

        with TestClient(app) as client:
            sess = client.post("/session", json={"customer_name": "E2E YA"})
            session_id = sess.json()["session_id"]

            with patch("src.api.chat.create_sales_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.invoke.return_value = {
                    "__interrupt__": [MagicMock(value={
                        "action": "create_order",
                        "summary": "Order Polo Navy - 100 pcs",
                        "message": "Ketik YA untuk konfirmasi",
                    })],
                }
                mock_create.return_value = mock_agent

                resp1 = client.post("/chat", json={
                    "message": "Order 100 Polo Navy",
                    "session_id": session_id,
                })
                assert resp1.status_code == 200

                mock_agent.invoke.return_value = {
                    "messages": [AIMessage(content="Order ORD-20260905-E2E berhasil dibuat.")],
                }
                resp2 = client.post("/chat", json={
                    "message": "YA",
                    "session_id": session_id,
                })
                assert resp2.status_code == 200
                assert "berhasil" in resp2.json()["response"].lower() or "order" in resp2.json()["response"].lower()

    def test_chat_resume_batal_after_interrupt(self):
        """After interrupt, sending BATAL cancels the order."""
        from fastapi.testclient import TestClient
        from src.main import app

        with TestClient(app) as client:
            sess = client.post("/session", json={"customer_name": "E2E BATAL"})
            session_id = sess.json()["session_id"]

            with patch("src.api.chat.create_sales_agent") as mock_create:
                mock_agent = MagicMock()
                mock_agent.invoke.return_value = {
                    "__interrupt__": [MagicMock(value={
                        "action": "create_order",
                        "summary": "Order Kaos Putih - 200 pcs",
                        "message": "Ketik YA untuk konfirmasi",
                    })],
                }
                mock_create.return_value = mock_agent

                resp1 = client.post("/chat", json={
                    "message": "Order 200 Kaos Putih",
                    "session_id": session_id,
                })
                assert resp1.status_code == 200

                mock_agent.invoke.return_value = {
                    "messages": [AIMessage(content="Order dibatalkan oleh pelanggan.")],
                }
                resp2 = client.post("/chat", json={
                    "message": "BATAL",
                    "session_id": session_id,
                })
                assert resp2.status_code == 200
                assert "dibatalkan" in resp2.json()["response"].lower() or "batal" in resp2.json()["response"].lower()


# ===================================================================
# TEST SUITE 9: Edge cases
# ===================================================================

class TestHITLEdgeCases:

    def test_double_confirm_same_order(self, checkpointer):
        """If user sends YA twice, second one should be handled gracefully."""
        agent = create_sales_agent(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "test-double-confirm"}}

        with patch("src.agents.nodes.get_llm") as mock_get_llm, \
             patch("src.agents.graph.db_create_order") as mock_db_create:

            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            mock_llm.invoke.return_value = _make_order_tool_call(SAMPLE_ORDER)
            agent.invoke(
                {"messages": [HumanMessage(content="Order 100 Polo Navy")]},
                config,
            )

            mock_llm.invoke.return_value = _make_final_response("Confirmed.")
            mock_db_create.return_value = {"id": "ORD-DOUBLE", "status": "pending"}
            agent.invoke(Command(resume="YA"), config)

            # Send YA again — should not create order again
            mock_llm.invoke.return_value = _make_final_response("Sudah confirmed.")
            mock_db_create.reset_mock()
            agent.invoke(
                {"messages": [HumanMessage(content="YA")]},
                config,
            )
            mock_db_create.assert_not_called()

    def test_order_with_invalid_product_id(self):
        """create_order tool handles missing product gracefully."""
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([
                {"product_id": 9999, "product_name": "Ghost Item", "qty": 10, "price_per_unit": 50000}
            ]),
        })
        assert result.startswith("ORDER_PENDING|")
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["subtotal"] == 500000

    def test_order_zero_quantity(self):
        """create_order tool with zero quantity."""
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([
                {"product_id": 1, "product_name": "Polo", "qty": 0, "price_per_unit": 70000}
            ]),
        })
        assert result.startswith("ORDER_PENDING|")
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["subtotal"] == 0

    def test_order_very_large_quantity(self):
        """create_order tool with very large quantity."""
        from src.tools.create_order import create_order

        result = create_order.invoke({
            "customer_id": "CUST-001",
            "items_json": json.dumps([
                {"product_id": 1, "product_name": "Polo", "qty": 100000, "price_per_unit": 70000}
            ]),
        })
        data = json.loads(result.split("ORDER_PENDING|", 1)[1])
        assert data["subtotal"] == 7000000000

    def test_order_status_transitions(self):
        """Test all valid status transitions via OrderRepo."""
        from src.data.repos.order_repo import OrderRepo

        repo = OrderRepo()
        customer = create_customer(name="Toko Transisi", phone="08777777777")
        order = repo.create_order(
            customer_id=customer["id"],
            items=[{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}],
            subtotal=3500000, discount_amount=0, total_price=3500000,
        )

        # pending → confirmed
        assert repo.update_status(order["id"], "confirmed") is True
        # confirmed → processing
        assert repo.update_status(order["id"], "processing") is True
        # processing → shipped
        assert repo.update_status(order["id"], "shipped") is True
        # shipped → delivered
        assert repo.update_status(order["id"], "delivered") is True

    def test_invalid_status_transition(self):
        """Test invalid status transition is rejected."""
        from src.data.repos.order_repo import OrderRepo

        repo = OrderRepo()
        customer = create_customer(name="Toko Invalid", phone="08888888888")
        order = repo.create_order(
            customer_id=customer["id"],
            items=[{"product_id": 1, "product_name": "Polo", "qty": 50, "price_per_unit": 70000, "subtotal": 3500000}],
            subtotal=3500000, discount_amount=0, total_price=3500000,
        )

        # pending → shipped (invalid)
        assert repo.update_status(order["id"], "shipped") is False
        # pending → delivered (invalid)
        assert repo.update_status(order["id"], "delivered") is False
