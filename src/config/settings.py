from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
