# Task 7: Integration Test & README

## Files to Create
- `tests/test_integration.py`
- `README.md`

## Prerequisites
- All previous tasks (1-6) completed
- FastAPI app exists at `src/main.py`

## What to Do

### 1. Create `tests/test_integration.py`

End-to-end test that tests the full conversation flow via FastAPI client.

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestFullFlow:
    def test_inquiry_to_quote_flow(self):
        # Turn 1: Inquiry
        resp1 = client.post("/chat", json={
            "message": "Saya butuh 500 kaos polo hitam untuk seragam karyawan",
            "customer_name": "Budi Santoso"
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]
        assert "polo" in data1["response"].lower() or "kaos" in data1["response"].lower()

        # Turn 2: Specify product
        resp2 = client.post("/chat", json={
            "message": "Yang Premium, bisa warna navy?",
            "session_id": session_id
        })
        assert resp2.status_code == 200
        assert "navy" in resp2["response"].lower() or "premium" in resp2["response"].lower()

        # Turn 3: Ask for quote
        resp3 = client.post("/chat", json={
            "message": "Buatkan penawaran untuk 500 pcs navy",
            "session_id": session_id
        })
        assert resp3.status_code == 200
        assert "rp" in resp3["response"].lower() or "penawaran" in resp3["response"].lower()


class TestEdgeCases:
    def test_unknown_product(self):
        resp = client.post("/chat", json={
            "message": "Saya cari jas formal pria",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None

    def test_budget_too_low(self):
        resp = client.post("/chat", json={
            "message": "Saya mau 500 kaos polo, budget cuma 10 juta",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None
```

### 2. Create `README.md`

Professional README for the portfolio project.

```markdown
# Sales Order Agent — PT Lemone Surya Indonesia

AI Agent untuk membantu proses order fashion grosir B2B. Multi-turn conversation dengan 6 tools untuk product search, stock checking, price calculation, dan quote generation.

## Tech Stack

- **Agent:** LangChain + LangGraph (ReAct pattern)
- **LLM:** Groq (GPT OSS model)
- **Embedding:** Google Gemini Embedding (gemini-embedding-001)
- **Backend:** FastAPI
- **Vector DB:** ChromaDB
- **Database:** SQLite

## Fitur

- 🔍 **Product Search** — Cari produk dengan semantic search (Gemini Embedding)
- 📦 **Stock Check** — Cek ketersediaan stok real-time
- 💰 **Price Calculator** — Hitung harga berdasarkan quantity tier
- 📋 **Quote Generator** — Buat penawaran harga final
- 🔄 **Alternative Finder** — Sarankan produk alternatif jika stok/budget tidak sesuai
- 💬 **Multi-turn Conversation** — Ingat konteks percakapan sebelumnya

## Setup

### Prerequisites
- Python 3.11+
- Groq API Key
- Google API Key (untuk Gemini Embedding)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd portfolio-PT-Lemone-Surya-Indonesia

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Seed database
python -m src.data.seed.seed

# Run server
python -m src.main
```

Server berjalan di `http://localhost:8000`

### API Docs
Buka `http://localhost:8000/docs` untuk Swagger UI

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/session` | Buat session baru |
| GET | `/session/{id}` | Get session info |
| POST | `/chat` | Kirim pesan ke agent |

## Contoh Percakapan

```
User: Saya butuh 500 kaos polo hitam untuk seragam karyawan
Agent: Saya temukan 2 opsi:
       1. Polo Premium Cotton - stok: 1200 ✓
       2. Polo Basic - stok: 800 ✓
       Mau saya buatkan penawaran untuk yang mana?

User: Yang Premium. Tapi bisa warna navy?
Agent: Polo Premium tersedia dalam warna:
       - Hitam (stok: 1200) ✓
       - Navy (stok: 950) ✓
       Untuk 500 pcs navy, stok aman. Mau lanjut?

User: Oke, buatkan penawaran 500 pcs navy
Agent: Penawaran Q-2026-09-02:
       - 500 x Polo Premium Navy @ Rp 70.000
       - Subtotal: Rp 35.000.000
       - Berlaku 7 hari
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_tools.py -v
pytest tests/test_agent.py -v
pytest tests/test_api.py -v
```

## Project Structure

```
src/
├── main.py                 # FastAPI entry point
├── agents/                 # LangGraph Agent
│   ├── graph.py           # State graph definition
│   ├── state.py           # Agent state schema
│   ├── nodes.py           # LLM + tool nodes
│   └── prompts.py         # System prompts
├── tools/                  # 6 Agent tools
├── data/                   # SQLite + ChromaDB
│   ├── database.py        # CRUD operations
│   ├── vector_store.py    # Semantic search
│   └── seed/              # Synthetic data
├── api/                    # FastAPI routes
└── config/                 # Settings
```

## License

MIT
```

## Verification
- README renders correctly
- All test files are syntactically correct

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-7-report.md`
