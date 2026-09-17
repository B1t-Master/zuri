from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables for the prototype. Run once against a fresh Neon DB.

    Requires 'CREATE EXTENSION IF NOT EXISTS vector;' executed beforehand
    (enable it once in Neon: Settings -> Extension -> vector).
    """
    import app.models  # noqa: F401  (register models on Base)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)