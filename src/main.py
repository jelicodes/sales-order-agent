from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.data.database import init_db
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.api.chat import router as chat_router
from src.config.langfuse import init_langfuse, shutdown_langfuse

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
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Terjadi kesalahan internal server",
            "detail": str(exc)
        }
    )


app.include_router(health_router)
app.include_router(session_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import settings
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)