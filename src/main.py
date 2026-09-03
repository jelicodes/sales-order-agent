from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.data.database import init_db
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.api.chat import router as chat_router
from src.api.models import ErrorResponse
from src.config.langfuse import init_langfuse, shutdown_langfuse
from src.config.settings import settings, APP_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_langfuse()
    yield
    shutdown_langfuse()


app = FastAPI(
    title="Sales Order Agent - PT Lemone",
    description="AI Agent untuk membantu proses order fashion grosir B2B",
    version=APP_VERSION,
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Terjadi kesalahan internal server",
            detail="Silakan coba lagi atau hubungi admin."
        ).model_dump()
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": "Terlalu banyak request. Silakan coba lagi nanti."}
    )


app.include_router(health_router)
app.include_router(session_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import settings, APP_VERSION
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)