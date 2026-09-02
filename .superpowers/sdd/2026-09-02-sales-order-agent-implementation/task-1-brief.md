# Task 1: Project Setup & Configuration

## Files to Create
- `requirements.txt`
- `.env.example`
- `src/__init__.py`
- `src/config/__init__.py`
- `src/config/settings.py`
- `.gitignore`
- Empty `__init__.py` for: `src/data/`, `src/tools/`, `src/agents/`, `src/api/`, `tests/`

## What to Do

1. Create `requirements.txt` with these exact dependencies:
```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-groq>=0.2.0
langgraph>=0.2.0
fastapi>=0.115.0
uvicorn>=0.30.0
chromadb>=0.5.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

2. Create `.env.example`:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_PATH=data/app.db
CHROMADB_PATH=data/chromadb
APP_HOST=0.0.0.0
APP_PORT=8000
```

3. Create `src/config/settings.py`:
```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

4. Create `.gitignore`:
```gitignore
__pycache__/
*.pyc
.env
data/
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
```

5. Create all empty `__init__.py` files

6. Install dependencies: `pip install -r requirements.txt`

7. Commit everything

## Test
- `pip install -r requirements.txt` succeeds
- `python -c "from src.config.settings import settings; print(settings)"` works

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-1-report.md`
