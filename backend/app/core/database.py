from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create async engine - convert PostgresDsn to string
engine = create_async_engine(
    str(settings.POSTGRES_DSN),
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,        # seconds to wait for a connection
    pool_pre_ping=True,     # verify connection is alive before use
    pool_recycle=3600,      # recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()