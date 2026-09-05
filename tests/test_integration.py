import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from src.main import app


@pytest.fixture
def client():
    """TestClient with mocked agent."""
    with patch("src.api.chat.create_sales_agent") as mock_create:
        mock_agent = MagicMock()

        def side_effect(input_state, config=None):
            msgs = input_state["messages"]
            last_user_msg = msgs[-1].content if msgs else ""

            if any(kw in last_user_msg.lower() for kw in ("polo", "kaos", "premium", "navy")):
                return {
                    "messages": [
                        msgs[0],
                        msgs[-1],
                        AIMessage(content=(
                            "Kami memiliki Polo Premium Cotton. "
                            "Harga: Rp 85.000/pcs untuk 100 pcs, "
                            "Rp 70.000/pcs untuk 500 pcs. "
                            "Stok tersedia 500 pcs."
                        ))
                    ]
                }
            elif "penawaran" in last_user_msg.lower() or "quote" in last_user_msg.lower():
                return {
                    "messages": [
                        msgs[0],
                        msgs[-1],
                        AIMessage(content=(
                            "Penawaran Q-2026-09-03:\n"
                            "- 500 x Polo Premium Navy @ Rp 70.000\n"
                            "- Subtotal: Rp 35.000.000\n"
                            "- Berlaku 7 hari"
                        ))
                    ]
                }
            return {
                "messages": [
                    msgs[0],
                    msgs[-1],
                    AIMessage(content="Maaf, saya tidak menemukan produk yang sesuai.")
                ]
            }

        mock_agent.invoke.side_effect = side_effect
        mock_create.return_value = mock_agent

        with TestClient(app) as c:
            yield c


class TestFullFlow:
    def test_inquiry_to_quote_flow(self, client):
        resp1 = client.post("/chat", json={
            "message": "Saya butuh 500 kaos polo hitam untuk seragam karyawan",
            "customer_name": "Budi Santoso"
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]
        assert "polo" in data1["response"].lower() or "kaos" in data1["response"].lower()

        resp2 = client.post("/chat", json={
            "message": "Yang Premium, bisa warna navy?",
            "session_id": session_id
        })
        assert resp2.status_code == 200
        assert "navy" in resp2.json()["response"].lower() or "premium" in resp2.json()["response"].lower()

        resp3 = client.post("/chat", json={
            "message": "Buatkan penawaran untuk 500 pcs navy",
            "session_id": session_id
        })
        assert resp3.status_code == 200
        assert "rp" in resp3.json()["response"].lower() or "penawaran" in resp3.json()["response"].lower()


class TestEdgeCases:
    def test_unknown_product(self, client):
        resp = client.post("/chat", json={
            "message": "Saya cari jas formal pria",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None

    def test_budget_too_low(self, client):
        resp = client.post("/chat", json={
            "message": "Saya mau 500 kaos polo, budget cuma 10 juta",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None
