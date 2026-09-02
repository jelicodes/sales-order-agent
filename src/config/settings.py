from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.6-27b"
    GOOGLE_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # Langfuse (Agent Observability)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
