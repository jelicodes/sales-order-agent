import sqlite3
from pathlib import Path
from fastapi import APIRouter
from src.config.settings import settings, APP_VERSION
from src.config.langfuse import get_langfuse_handler
from src.api.models import HealthResponse, HealthCheckResult

router = APIRouter()


def check_database() -> dict:
    try:
        db_path = Path(settings.DATABASE_PATH)
        if not db_path.exists():
            return {"status": "error", "message": "Database file not found"}
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return {"status": "ok", "products_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_chromadb() -> dict:
    try:
        chromadb_path = Path(settings.CHROMADB_PATH)
        if not chromadb_path.exists():
            return {"status": "warning", "message": "ChromaDB directory not found (will be created on first use)"}
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_groq() -> dict:
    try:
        if not settings.GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}
        return {"status": "ok", "model": settings.GROQ_MODEL}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_langfuse() -> dict:
    handler = get_langfuse_handler()
    if handler:
        return {"status": "ok", "enabled": True}
    return {"status": "disabled", "enabled": False}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = check_database()
    chromadb_status = check_chromadb()
    groq_status = check_groq()
    langfuse_status = check_langfuse()
    
    overall_status = "ok"
    if db_status["status"] == "error" or groq_status["status"] == "error":
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        service="sales-order-agent",
        version=APP_VERSION,
        checks={
            "database": HealthCheckResult(**db_status),
            "chromadb": HealthCheckResult(**chromadb_status),
            "groq": HealthCheckResult(**groq_status),
            "langfuse": HealthCheckResult(**langfuse_status),
        }
    )