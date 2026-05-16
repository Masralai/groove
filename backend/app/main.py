from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import asyncio

app = FastAPI(
    title="Groove - Meta Ads Data Pipeline + NL Chatbot",
    description="Production-ready service integrating with Meta Marketing API to fetch ads data and provide natural language chatbot interface",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    # Initialize database connection
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Import and include routers
from app.api.v1.router import api_router
app.include_router(api_router, prefix="/api")