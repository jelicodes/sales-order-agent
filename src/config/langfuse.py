from typing import Optional
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from src.config.settings import settings

_langfuse_handler: Optional[CallbackHandler] = None


def init_langfuse() -> Optional[CallbackHandler]:
    global _langfuse_handler
    
    if not settings.LANGFUSE_ENABLED:
        return None
    
    if not settings.LANGFUSE_PUBLIC_KEY or settings.LANGFUSE_PUBLIC_KEY == "pk-lf-...":
        return None
    
    try:
        from langfuse import Langfuse
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        _langfuse_handler = CallbackHandler()
        return _langfuse_handler
    except Exception:
        return None


def get_langfuse_handler() -> Optional[CallbackHandler]:
    return _langfuse_handler


def get_langfuse_client():
    if settings.LANGFUSE_ENABLED and _langfuse_handler:
        return get_client()
    return None


def shutdown_langfuse():
    client = get_langfuse_client()
    if client:
        client.shutdown()
