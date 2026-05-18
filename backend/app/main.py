import logging
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.mongo import close_mongo_connection
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.sync_service import data_sync_service
from pathlib import Path

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Groove - Meta Ads Data Pipeline + NL Chatbot",
    description="Production-ready service integrating with Meta Marketing API to fetch ads data and provide natural language chatbot interface",
    version="0.1.0"
)

# Scheduler for daily sync
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
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

# Import and include routers
from app.api.v1.router import api_router
app.include_router(api_router, prefix="/api")