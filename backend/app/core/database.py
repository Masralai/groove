import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Main (admin) engine — used by data sync ─────────────────────────────
engine = create_async_engine(
    str(settings.POSTGRES_DSN),
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# ── Read-only engine — used by LLM chat endpoint ────────────────────────
_readonly_dsn = settings.POSTGRES_READONLY_DSN
if _readonly_dsn:
    logger.info("Using read-only PostgreSQL DSN for LLM chat queries")
    _readonly_engine = create_async_engine(
        str(_readonly_dsn),
        pool_size=10,
        max_overflow=5,
        pool_timeout=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    AsyncSessionReadOnly = sessionmaker(
        _readonly_engine, class_=AsyncSession, expire_on_commit=False
    )
else:
    logger.info(
        "POSTGRES_READONLY_DSN not set — LLM chat will use admin DSN"
        " (set it in production for defense-in-depth)"
    )
    AsyncSessionReadOnly = AsyncSessionLocal

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_readonly_db() -> AsyncSession:
    async with AsyncSessionReadOnly() as session:
        try:
            await session.execute(text("SET TRANSACTION READ ONLY"))
            yield session
        finally:
            await session.close()
