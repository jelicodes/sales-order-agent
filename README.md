# Sales Order Agent — PT Lemone Surya Indonesia

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangChain](https://img.shields.io/badge/LangChain-LangGraph-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

AI Agent untuk membantu proses order fashion grosir B2B. Multi-turn conversation dengan 6 tools untuk product search, stock checking, price calculation, dan quote generation.

## Tech Stack

- **Agent:** LangChain + LangGraph (ReAct pattern)
- **LLM:** Groq (GPT OSS model)
- **Embedding:** Google Gemini Embedding (gemini-embedding-001)
- **Backend:** FastAPI
- **Vector DB:** ChromaDB
- **Database:** SQLite

## Fitur

- **Product Search** — Cari produk dengan semantic search (Gemini Embedding)
- **Stock Check** — Cek ketersediaan stok real-time
- **Price Calculator** — Hitung harga berdasarkan quantity tier
- **Quote Generator** — Buat penawaran harga final
- **Alternative Finder** — Sarankan produk alternatif jika stok/budget tidak sesuai
- **Multi-turn Conversation** — Ingat konteks percakapan sebelumnya

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
pytest tests/test_integration.py -v
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
