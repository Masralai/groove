import asyncio
import logging
import sys
from pathlib import Path

from alembic.config import Config as AlembicConfig
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from alembic import command as alembic_command
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.models.mongo import close_mongo_connection
from app.services.sync_service import data_sync_service

# ── Structured logging ──────────────────────────────────────────────────
LOG_FORMAT = "[%(asctime)s] %(levelname)-5s  %(name)-35s %(message)s"
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# Warn if default SECRET_KEY is used in production
if settings.SECRET_KEY == "dev-secret-key-change-in-production":
    logger.warning(
        "SECRET_KEY is set to the dev default. Override with a strong secret in production."
    )

# CORS — allow frontend origins from settings, fall back to localhost for dev
_allowed_origins = settings.CORS_ORIGINS.split(",")

app = FastAPI(
    title="Groove - Meta Ads Data Pipeline + NL Chatbot",
    description=(
        "Production-ready service integrating with Meta Marketing API"
        " to fetch ads data and provide natural language chatbot interface"
    ),
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handlers ───────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error on %s %s: %s",
        request.method, request.url.path, exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Invalid request data. Check the fields and try again.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "%s %s → %s: %s",
        request.method, request.url.path, exc.status_code, exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "request_error",
            "message": str(exc.detail),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An internal server error occurred. Please try again later.",
        },
    )


# Scheduler for daily sync
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up — log level: %s", settings.LOG_LEVEL)

    # Run Alembic migrations to ensure schema is up to date
    alembic_cfg_path = Path(__file__).parent.parent / "alembic.ini"
    if alembic_cfg_path.exists():
        alembic_cfg = AlembicConfig(str(alembic_cfg_path))
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, alembic_command.upgrade, alembic_cfg, "head")
        logger.info("Alembic migrations applied successfully")
    else:
        # Fallback: create tables directly if alembic not configured
        logger.warning("alembic.ini not found, using Base.metadata.create_all as fallback")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Start APScheduler for daily sync at midnight
    scheduler.add_job(
        data_sync_service.sync_all,
        trigger='cron',
        hour=0,
        minute=0,
        id='daily_sync',
        name='Daily Meta Ads data sync',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Started APScheduler for daily sync at midnight")


@app.on_event("shutdown")
async def shutdown_event():
    # Close MongoDB connection
    await close_mongo_connection()

    # Shutdown scheduler
    scheduler.shutdown()


# Root-level health check (also available at /api/health)
@app.get("/health")
async def root_health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
